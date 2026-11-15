"""Check the explicit public file set. No Git, network, or source-project access."""
from pathlib import Path
import ast
import hashlib
import json
import re
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.migration_paths import safe_name, check_tree

MEDIA_FILES = {
    "docs/media/yingdao-rpa-copilot-intro.mp4": "video/mp4",
    "docs/media/yingdao-rpa-copilot-cover.png": "image/png",
    "docs/media/yingdao-rpa-copilot-cover.svg": "image/svg+xml",
    "docs/media/yingdao-official-mark.svg": "image/svg+xml",
}
BINARY_MEDIA = {path for path in MEDIA_FILES if path.endswith((".mp4", ".png"))}


def media_records(root, listed, issues):
    """Only the four reviewed media paths; never exempt a whole directory."""
    manifest_path = root / "docs/media/media-manifest.json"
    if not manifest_path.exists() and not (listed & set(MEDIA_FILES)):
        return {}
    if "docs/media/media-manifest.json" not in listed:
        issues.append({"code": "MEDIA_MANIFEST_NOT_LISTED"})
        return {}
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        if set(payload) != {"format", "files"} or payload["format"] != "yingdao-repository-media/1":
            raise ValueError()
        records = payload["files"]
        if not isinstance(records, list) or len(records) != len(MEDIA_FILES):
            raise ValueError()
        result = {}
        for row in records:
            if not isinstance(row, dict) or set(row) != {"path", "bytes", "sha256", "content_type", "source_id", "rights"}:
                raise ValueError()
            path = row["path"]
            if (not isinstance(path, str) or path not in MEDIA_FILES or path in result
                    or path not in listed or row["content_type"] != MEDIA_FILES[path]
                    or type(row["bytes"]) is not int or not 0 < row["bytes"] <= 4 * 1024 * 1024
                    or not isinstance(row["sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", row["sha256"])
                    or not isinstance(row["source_id"], str) or not row["source_id"]
                    or row["rights"] not in {"third_party_trademark_not_mit", "mixed_cover_logo_excluded", "mixed_video_not_mit"}):
                raise ValueError()
            result[path] = row
        return result
    except (OSError, ValueError, TypeError):
        issues.append({"code": "MEDIA_MANIFEST_INVALID"})
        return {}


def check_binary_media(rel, data):
    """Bounded format/metadata checks, not playback or visual privacy review."""
    if rel.endswith(".mp4"):
        if len(data) < 24 or data[4:8] != b"ftyp":
            return "MEDIA_FORMAT_MISMATCH"
        offset, kinds = 0, set()
        while offset < len(data):
            if offset + 8 > len(data):
                return "MEDIA_FORMAT_MISMATCH"
            size, kind = struct.unpack_from(">I4s", data, offset)
            if size == 1:
                if offset + 16 > len(data):
                    return "MEDIA_FORMAT_MISMATCH"
                size = struct.unpack_from(">Q", data, offset + 8)[0]
            if size == 0:
                size = len(data) - offset
            if size < 8 or offset + size > len(data):
                return "MEDIA_FORMAT_MISMATCH"
            kinds.add(kind)
            offset += size
        return None if {b"ftyp", b"moov", b"mdat"} <= kinds else "MEDIA_FORMAT_MISMATCH"
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "MEDIA_FORMAT_MISMATCH"
    offset, kinds = 8, []
    while offset < len(data):
        if offset + 12 > len(data):
            return "MEDIA_FORMAT_MISMATCH"
        length = struct.unpack_from(">I", data, offset)[0]
        kind = data[offset + 4:offset + 8]
        if offset + 12 + length > len(data):
            return "MEDIA_FORMAT_MISMATCH"
        if kind in {b"tEXt", b"zTXt", b"iTXt", b"eXIf"}:
            return "MEDIA_METADATA_NOT_ALLOWED"
        if kind == b"IHDR" and (length != 13 or struct.unpack_from(">II", data, offset + 8) != (1600, 900)):
            return "MEDIA_DIMENSIONS_MISMATCH"
        kinds.append(kind)
        offset += length + 12
    return None if kinds and kinds[0] == b"IHDR" and kinds[-1] == b"IEND" and b"IDAT" in kinds else "MEDIA_FORMAT_MISMATCH"


def public_paths(root):
    payload = json.loads((root / "public-files.json").read_text(encoding="utf-8"))
    if set(payload) != {"format", "files"} or payload["format"] != "yingdao-public-file-set/1":
        raise ValueError("PUBLIC_SET_FORMAT")
    paths = payload["files"]
    if not isinstance(paths, list) or not all(isinstance(x, str) for x in paths):
        raise ValueError("PUBLIC_SET_ITEMS")
    check_tree(paths)
    for path in paths:
        safe_name(path)
        if Path(path).parts[0] in {".git", ".local", "work"}:
            raise ValueError("PRIVATE_FILE_IN_PUBLIC_SET")
    return paths


def check(root=ROOT):
    root = Path(root).resolve()
    paths = public_paths(root)
    issues = []
    listed = set(paths)
    media = media_records(root, listed, issues)
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()
              and not set(p.relative_to(root).parts) & {".git", ".local", "work", "__pycache__"}}
    if actual != listed:
        issues.append({"code": "PUBLIC_SET_DRIFT",
                       "unlisted": sorted(actual - listed), "missing": sorted(listed - actual)})
    patterns = {
        "PRIVATE_USER_PATH": re.compile(r"[A-Za-z]:[\\/]Users[\\/]", re.I),
        "HISTORICAL_GUID": re.compile(r"\b[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}\b", re.I),
        "PRIVATE_KEY": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
        "AUTH_VALUE": re.compile(r"(?im)^\s*(?:authorization|cookie|access_token|api_key)\s*[:=]\s*\S+"),
        "RESOURCE_QUERY_URL": re.compile(r"https?://[^\s<>]+[?][^\s<>]+", re.I),
    }
    forbidden_extensions = {".dll", ".exe", ".bot", ".ydtransfer", ".whl", ".zip", ".pdf", ".xlsx"}
    forbidden_imports = {"socket", "urllib", "http", "requests", "subprocess", "ctypes",
                         "importlib", "psutil", "win32api"}
    link_count = 0
    for rel in paths:
        path = root / rel
        if not path.is_file() or path.is_symlink():
            issues.append({"code": "MISSING_OR_LINK", "file": rel})
            continue
        if path.suffix.lower() in forbidden_extensions:
            issues.append({"code": "EXCLUDED_ARTIFACT", "file": rel})
        data = path.read_bytes()
        if rel in media and (len(data) != media[rel]["bytes"] or hashlib.sha256(data).hexdigest() != media[rel]["sha256"]):
            issues.append({"code": "MEDIA_DIGEST_MISMATCH", "file": rel})
        if path.suffix.lower() in {".png", ".mp4"}:
            if rel not in BINARY_MEDIA or rel not in media:
                issues.append({"code": "UNREVIEWED_BINARY_MEDIA", "file": rel})
                continue
            error = check_binary_media(rel, data)
            if error:
                issues.append({"code": error, "file": rel})
            # Keep the same privacy patterns over readable UTF-8/UTF-16 strings.
            # Pixel/frame privacy still requires the separately documented review.
            text = "\n".join(data.decode(codec, errors="ignore") for codec in ("utf-8", "utf-16-le", "utf-16-be"))
        else:
            try:
                text = data.decode("utf-8")
            except UnicodeError:
                issues.append({"code": "NON_TEXT_FILE", "file": rel})
                continue
        for code, pattern in patterns.items():
            if pattern.search(text):
                issues.append({"code": code, "file": rel})
        if path.suffix == ".md":
            for link in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", text):
                if re.match(r"^(https?://|mailto:|#)", link):
                    continue
                target = (path.parent / link.split("#", 1)[0]).resolve()
                link_count += 1
                if not target.is_relative_to(root) or not target.exists():
                    issues.append({"code": "BROKEN_OR_EXTERNAL_LINK", "file": rel})
        if rel.startswith("tools/") and path.suffix == ".py":
            tree = ast.parse(text)
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.level:
                    modules = [node.module] if node.module else [item.name for item in node.names]
                    if node.level != 1 or any(not (path.parent / (name + ".py")).is_file()
                                              for name in modules):
                        issues.append({"code": "UNKNOWN_RELATIVE_IMPORT", "file": rel})
                    continue
                names = [a.name for a in node.names] if isinstance(node, ast.Import) else (
                    [node.module] if isinstance(node, ast.ImportFrom) and node.module else [])
                for name in names:
                    top = name.split(".")[0]
                    if top in forbidden_imports or top not in sys.stdlib_module_names | {"tools"}:
                        issues.append({"code": "NON_OFFLINE_IMPORT", "file": rel})
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    if node.func.id in {"eval", "exec", "compile", "__import__"}:
                        issues.append({"code": "DYNAMIC_EXECUTION", "file": rel})
    return {"ok": not issues, "public_file_count": len(paths), "local_link_count": link_count,
            "issues": issues, "network_calls": 0,
            "scope": "explicit_public_files_and_basic_static_checks",
            "complete_secret_or_rights_review": False}


def main():
    try:
        result = check()
    except (ValueError, OSError, TypeError):
        result = {"ok": False, "issues": [{"code": "PUBLIC_SET_INPUT_ERROR"}], "network_calls": 0}
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

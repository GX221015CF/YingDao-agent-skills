"""Check the explicit public file set. No Git, network, or source-project access."""
from pathlib import Path
import ast
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.migration_paths import safe_name, check_tree


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

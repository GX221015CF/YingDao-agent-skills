"""Inventory and byte-integrity review only. Not a native Yingdao importer."""
from pathlib import Path
import re

from .migration_paths import TransferError, check_tree, safe_name, sha

COMPONENTS = {"flows", "globals", "selectors", "resources", "dependencies"}
MAX_RESOURCE_BYTES = 1024 * 1024


def require(condition, code):
    if not condition:
        raise TransferError(code)


def _ids(values):
    require(isinstance(values, list) and all(isinstance(x, str) and x.strip() for x in values),
            "INVALID_COMPONENT_ITEMS")
    require(len(set(values)) == len(values), "DUPLICATE_COMPONENT_ID")
    return set(values)


def review(manifest, resource_root):
    require(isinstance(manifest, dict) and set(manifest) ==
            {"format", "app", "components", "resources", "bindings"}, "MANIFEST_FIELDS")
    require(manifest["format"] == "yingdao-offline-inventory/1", "MANIFEST_FORMAT")
    require(isinstance(manifest["app"], dict) and set(manifest["app"]) == {"id", "name"}
            and all(isinstance(x, str) and x.strip() for x in manifest["app"].values()), "APP_IDENTITY")
    components = manifest["components"]
    require(isinstance(components, dict) and set(components) == COMPONENTS, "COMPONENTS_REQUIRED")
    declared = {}
    for name, row in components.items():
        require(isinstance(row, dict) and set(row) == {"complete", "items"}
                and type(row["complete"]) is bool, "COMPONENT_FIELDS")
        declared[name] = _ids(row["items"])
    resources, bindings = manifest["resources"], manifest["bindings"]
    require(isinstance(resources, list) and len(resources) <= 100
            and isinstance(bindings, list) and len(bindings) <= 1000, "INVENTORY_LIMIT")
    resource_ids, by_id, paths = [], {}, []
    for row in resources:
        require(isinstance(row, dict) and set(row) == {"id", "path", "bytes", "sha256"},
                "RESOURCE_FIELDS")
        require(isinstance(row["id"], str) and row["id"].strip(), "RESOURCE_ID")
        require(type(row["bytes"]) is int and 0 <= row["bytes"] <= MAX_RESOURCE_BYTES, "RESOURCE_SIZE")
        require(isinstance(row["sha256"], str) and re.fullmatch(r"[0-9a-f]{64}", row["sha256"]),
                "RESOURCE_DIGEST")
        safe_name(row["path"])
        paths.append(row["path"])
        resource_ids.append(row["id"])
        by_id[row["id"]] = row
    require(len(set(resource_ids)) == len(resource_ids), "DUPLICATE_RESOURCE_ID")
    require(set(resource_ids) == declared["resources"], "RESOURCE_COMPONENT_MISMATCH")
    check_tree(paths)
    seen = set()
    use_counts = dict.fromkeys(resource_ids, 0)
    mappings = []
    for row in bindings:
        require(isinstance(row, dict) and set(row) ==
                {"selector_id", "field", "resource_id", "status"}, "BINDING_FIELDS")
        require(all(isinstance(v, str) for v in row.values()), "BINDING_TYPES")
        require(row["selector_id"] in declared["selectors"] and row["field"] == "semantic.image"
                and row["resource_id"] in by_id, "UNRESOLVED_BINDING")
        require(row["status"] in {"disabled", "enabled"}, "BINDING_STATUS")
        key = row["selector_id"], row["field"]
        require(key not in seen, "DUPLICATE_BINDING")
        seen.add(key)
        use_counts[row["resource_id"]] += 1
        mappings.append({**row, "file": by_id[row["resource_id"]]["path"]})
    root = Path(resource_root).resolve(strict=True)
    require(root.is_dir(), "RESOURCE_ROOT")
    results = []
    for row in resources:
        candidate = root / row["path"]
        # Check junctions/symlinks and containment before reading any declared object.
        current = root
        for part in Path(row["path"]).parts:
            current = current / part
            require(not current.is_symlink() and not getattr(current, "is_junction", lambda: False)(),
                    "RESOURCE_LINK")
        resolved = candidate.resolve()
        require(resolved.is_relative_to(root), "RESOURCE_PATH_ESCAPE")
        if not resolved.is_file():
            state = "missing"
        elif resolved.stat().st_size > MAX_RESOURCE_BYTES:
            state = "too_large"
        else:
            with resolved.open("rb") as stream:
                data = stream.read(MAX_RESOURCE_BYTES + 1)
            if len(data) > MAX_RESOURCE_BYTES:
                state = "too_large"
            else:
                state = "verified" if len(data) == row["bytes"] and sha(data) == row["sha256"] else "changed"
        results.append({"resource_id": row["id"], "state": state})
    return {"ok": all(row["state"] == "verified" for row in results),
            "level": "offline_inventory_and_byte_integrity",
            "declared_components_complete": all(row["complete"] for row in components.values()),
            "component_counts": {k: len(v) for k, v in sorted(declared.items())},
            "resource_count": len(resources), "binding_count": len(bindings),
            "shared_resources": sorted(k for k, count in use_counts.items() if count > 1),
            "resources": results, "mappings": mappings,
            "source_authenticity_verified": False, "image_decode_verified": False,
            "target_saved_state_verified": False, "account_access_verified": False,
            "native_import_verified": False, "live_calls": 0}

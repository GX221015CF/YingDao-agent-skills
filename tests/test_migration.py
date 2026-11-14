from copy import deepcopy
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
(ROOT / "work").mkdir(exist_ok=True)
sys.path.insert(0, str(ROOT))
from tools.migration import review
from tools.migration_paths import TransferError
from tools.portable_validation import read_json

FIXTURES = ROOT / "examples/migration"


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.manifest = read_json(FIXTURES / "manifest.json")
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / "work", prefix="test-migration-")
        self.addCleanup(self.temp.cleanup)
        self.resource_root = Path(self.temp.name)
        shutil.copyfile(FIXTURES / "resources/reference.svg", self.resource_root / "reference.svg")

    def test_shared_resource_has_two_explicit_bindings(self):
        result = review(self.manifest, self.resource_root)
        self.assertEqual(result, read_json(FIXTURES / "expected.json"))
        self.assertEqual(len(result["mappings"]), 2)
        self.assertEqual(result["shared_resources"], ["U01"])
        self.assertFalse(result["native_import_verified"])

    def test_missing_resource(self):
        (self.resource_root / "reference.svg").unlink()
        result = review(self.manifest, self.resource_root)
        self.assertFalse(result["ok"])
        self.assertEqual(result["resources"][0]["state"], "missing")
        self.assertEqual(result["binding_count"], 2)

    def test_changed_resource_bytes(self):
        (self.resource_root / "reference.svg").write_text("changed", encoding="utf-8")
        result = review(self.manifest, self.resource_root)
        self.assertFalse(result["ok"])
        self.assertEqual(result["resources"][0]["state"], "changed")

    def test_wrong_digest_even_same_length(self):
        self.manifest["resources"][0]["sha256"] = "0" * 64
        result = review(self.manifest, self.resource_root)
        self.assertEqual(result["resources"][0]["state"], "changed")

    def test_unresolved_binding(self):
        self.manifest["bindings"][1]["resource_id"] = "unknown"
        with self.assertRaisesRegex(TransferError, "UNRESOLVED_BINDING"):
            review(self.manifest, self.resource_root)

    def test_duplicate_binding_rejected(self):
        self.manifest["bindings"].append(deepcopy(self.manifest["bindings"][0]))
        with self.assertRaisesRegex(TransferError, "DUPLICATE_BINDING"):
            review(self.manifest, self.resource_root)

    def test_missing_component_is_not_empty_component(self):
        del self.manifest["components"]["globals"]
        with self.assertRaisesRegex(TransferError, "COMPONENTS_REQUIRED"):
            review(self.manifest, self.resource_root)

    def test_incomplete_declaration_remains_incomplete(self):
        self.manifest["components"]["flows"]["complete"] = False
        result = review(self.manifest, self.resource_root)
        self.assertTrue(result["ok"])
        self.assertFalse(result["declared_components_complete"])

    def test_resource_inventory_mismatch(self):
        self.manifest["components"]["resources"]["items"] = []
        with self.assertRaisesRegex(TransferError, "RESOURCE_COMPONENT_MISMATCH"):
            review(self.manifest, self.resource_root)

    def test_traversal_absolute_and_windows_device_paths_rejected(self):
        for path in ("../outside.svg", "/absolute.svg", "C:/absolute.svg", "NUL.svg", "a\\b.svg"):
            self.manifest["resources"][0]["path"] = path
            with self.subTest(path=path), self.assertRaises(TransferError):
                review(self.manifest, self.resource_root)

    def test_duplicate_resource_ids_rejected(self):
        self.manifest["resources"].append(deepcopy(self.manifest["resources"][0]))
        with self.assertRaisesRegex(TransferError, "DUPLICATE_RESOURCE_ID"):
            review(self.manifest, self.resource_root)

    def test_case_collision_rejected(self):
        other = {**self.manifest["resources"][0], "id": "U02", "path": "REFERENCE.svg"}
        self.manifest["resources"].append(other)
        self.manifest["components"]["resources"]["items"].append("U02")
        with self.assertRaises(TransferError):
            review(self.manifest, self.resource_root)

    def test_oversized_resource(self):
        (self.resource_root / "reference.svg").write_bytes(b"x" * (1024 * 1024 + 1))
        result = review(self.manifest, self.resource_root)
        self.assertEqual(result["resources"][0]["state"], "too_large")

    def test_manifest_not_mutated(self):
        before = deepcopy(self.manifest)
        review(self.manifest, self.resource_root)
        self.assertEqual(before, self.manifest)

    def test_link_is_rejected_before_resource_open(self):
        reference = self.resource_root / "reference.svg"
        with patch.object(Path, "is_symlink", lambda path: path == reference):
            with self.assertRaisesRegex(TransferError, "RESOURCE_LINK"):
                review(self.manifest, self.resource_root)


if __name__ == "__main__":
    unittest.main()

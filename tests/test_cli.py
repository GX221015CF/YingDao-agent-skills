from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
(ROOT / "work").mkdir(exist_ok=True)
sys.path.insert(0, str(ROOT))
from tools.portable_validation import read_json


class CliTests(unittest.TestCase):
    def invoke(self, *arguments):
        with tempfile.TemporaryDirectory(dir=ROOT / "work", prefix="test-cwd-") as cwd:
            return subprocess.run([sys.executable, "-B", str(ROOT / "tools/offline_demo.py"), *arguments],
                                  cwd=cwd, capture_output=True, text=True, encoding="utf-8", timeout=20)

    def test_automation_from_unrelated_working_directory(self):
        result = self.invoke("automation")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), read_json(ROOT / "examples/automation/expected.json"))

    def test_migration_from_unrelated_working_directory(self):
        result = self.invoke("migration")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), read_json(ROOT / "examples/migration/expected.json"))

    def test_candidate_command(self):
        result = self.invoke("candidate", "--candidate", str(ROOT / "examples/automation/candidate.json"),
                             "--contract", str(ROOT / "examples/automation/contract.json"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["level"], "offline_request_schema_only")

    def test_missing_and_changed_resources_return_two(self):
        for name in ("missing", "changed"):
            result = self.invoke("migration", "--manifest", str(ROOT / f"examples/migration/manifest-{name}.json"))
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertEqual(json.loads(result.stdout),
                             read_json(ROOT / f"examples/migration/expected-{name}.json"))

    def test_feedback_command(self):
        result = self.invoke("feedback", "--feedback", str(ROOT / "examples/automation/feedback-running.json"),
                             "--contract", str(ROOT / "examples/automation/contract.json"),
                             "--run-id", "synthetic-run-1")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["state"], "pending")

    def test_error_does_not_echo_private_path(self):
        result = self.invoke("candidate", "--candidate", str(ROOT / ".local/not-provided.json"),
                             "--contract", str(ROOT / "examples/automation/contract.json"))
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["error"], "JSON_FILE_MISSING_OR_TOO_LARGE")
        self.assertNotIn(str(ROOT), result.stdout)


if __name__ == "__main__":
    unittest.main()

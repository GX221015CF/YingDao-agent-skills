from copy import deepcopy
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
(ROOT / "work").mkdir(exist_ok=True)
sys.path.insert(0, str(ROOT))
from tools import automation, branch_candidate, schema_subset
from tools.portable_validation import PortableError, read_json

FIXTURES = ROOT / "examples/automation"


class AutomationTests(unittest.TestCase):
    def setUp(self):
        self.candidate = read_json(FIXTURES / "candidate.json")
        self.contract = read_json(FIXTURES / "contract.json")
        self.running = read_json(FIXTURES / "feedback-running.json")
        self.completed = read_json(FIXTURES / "feedback-completed.json")

    def test_example_matches_declared_expected_output(self):
        self.assertEqual(automation.demo(self.candidate, self.contract, self.running, self.completed),
                         read_json(FIXTURES / "expected.json"))

    def test_fixture_is_generated_from_six_node_builder(self):
        self.assertEqual(self.candidate, automation.build_example())
        self.assertFalse(automation.validate(self.candidate, self.contract)["executable"])

    def test_top_level_target_mismatch_rejected(self):
        self.candidate["target"]["app_id"] = "different"
        with self.assertRaisesRegex(PortableError, "CONTRACT_TARGET_MISMATCH"):
            automation.validate(self.candidate, self.contract)

    def test_request_target_mismatch_rejected(self):
        self.candidate["requests"][1]["arguments"]["flow_id"] = "different"
        with self.assertRaisesRegex(PortableError, "REQUEST_TARGET_MISMATCH"):
            automation.validate(self.candidate, self.contract)

    def test_boolean_is_not_integer_index(self):
        self.candidate["requests"][0]["arguments"]["block_index"] = True
        with self.assertRaises(schema_subset.StudioMcpError):
            automation.validate(self.candidate, self.contract)

    def test_unknown_argument_and_missing_required_rejected(self):
        for mode in ("unknown", "missing"):
            changed = deepcopy(self.candidate)
            args = changed["requests"][0]["arguments"]
            if mode == "unknown":
                args["unexpected"] = "value"
            else:
                del args["flow_id"]
            with self.subTest(mode=mode), self.assertRaises(schema_subset.StudioMcpError):
                automation.validate(changed, self.contract)

    def test_unknown_schema_keyword_fails_closed(self):
        self.contract["tools"][0]["inputSchema"]["$ref"] = "#/unknown"
        with self.assertRaises(schema_subset.StudioMcpError):
            automation.validate(self.candidate, self.contract)

    def test_running_and_pending_are_not_failure(self):
        for status in ("running", "pending", None):
            data = {**self.running, "terminal_status": status}
            result = automation.feedback(data, self.contract["target"], "synthetic-run-1")
            self.assertEqual(result["state"], "pending")
            self.assertFalse(result["may_rerun"])

    def test_feedback_wrong_app_flow_or_run_rejected(self):
        for key in ("app_id", "flow_id", "run_id"):
            with self.subTest(key=key), self.assertRaises(PortableError):
                automation.feedback({**self.running, key: "other"}, self.contract["target"], "synthetic-run-1")

    def test_completion_requires_post_finish_verification(self):
        del self.completed["verification"]
        with self.assertRaisesRegex(PortableError, "COMPLETION_VERIFICATION_REQUIRED"):
            automation.feedback(self.completed, self.contract["target"], "synthetic-run-1")

    def test_contradictory_state_is_unknown(self):
        self.completed["active"] = True
        with self.assertRaisesRegex(PortableError, "UNKNOWN_RUN_STATE"):
            automation.feedback(self.completed, self.contract["target"], "synthetic-run-1")

    def test_failed_and_paused_distinguished(self):
        for status, active, succeeded, expected in (
            ("failed", False, False, "failed"), ("paused", True, None, "human_attention")):
            result = automation.feedback({**self.running, "terminal_status": status, "active": active,
                                          "run_succeeded": succeeded},
                                         self.contract["target"], "synthetic-run-1")
            self.assertEqual(result["state"], expected)
            self.assertFalse(result["output_and_business_verified"])

    def test_branch_id_order_and_duplicates_rejected(self):
        rows = [{"block_id": f"fixture-{i}", "block_index": i, "prototype_name": row["prototype_name"]}
                for i, row in enumerate(branch_candidate.SPECS)]
        for mode in ("duplicate", "order", "extra"):
            changed = deepcopy(rows)
            if mode == "duplicate":
                changed[1]["block_id"] = changed[0]["block_id"]
            elif mode == "order":
                changed.reverse()
            else:
                changed.append(changed[-1])
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                branch_candidate.fill_arguments("synthetic-branch", changed)

    def test_json_duplicate_and_nonfinite_rejected(self):
        for text in ('{"a":1,"a":2}', '{"a":NaN}', '{"a":1e999}'):
            with tempfile.TemporaryDirectory(dir=ROOT / "work", prefix="test-json-") as folder:
                path = Path(folder) / "input.json"
                path.write_text(text, encoding="utf-8")
                with self.assertRaises(PortableError):
                    read_json(path)


if __name__ == "__main__":
    unittest.main()

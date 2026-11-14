"""Local JSON-in/JSON-out CLI. No discovery, network, app write, save or run."""
from pathlib import Path
import argparse
import json
import sys

# Resolve imports from this file, independent of the caller's working directory.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import automation
from tools.migration import review
from tools.migration_paths import TransferError
from tools.portable_validation import PortableError, read_json
from tools.schema_subset import StudioMcpError


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="command", required=True)
    subs.add_parser("automation")
    candidate = subs.add_parser("candidate")
    candidate.add_argument("--candidate", type=Path, required=True)
    candidate.add_argument("--contract", type=Path, required=True)
    feedback = subs.add_parser("feedback")
    feedback.add_argument("--feedback", type=Path, required=True)
    feedback.add_argument("--contract", type=Path, required=True)
    feedback.add_argument("--run-id", required=True)
    migration = subs.add_parser("migration")
    migration.add_argument("--manifest", type=Path, default=ROOT / "examples/migration/manifest.json")
    migration.add_argument("--resources", type=Path, default=ROOT / "examples/migration/resources")
    args = parser.parse_args(argv)
    try:
        if args.command == "automation":
            folder = ROOT / "examples/automation"
            result = automation.demo(*(read_json(folder / name) for name in
                ("candidate.json", "contract.json", "feedback-running.json", "feedback-completed.json")))
        elif args.command == "candidate":
            result = automation.validate(read_json(args.candidate), read_json(args.contract))
        elif args.command == "feedback":
            contract = read_json(args.contract)
            result = automation.feedback(read_json(args.feedback), contract["target"], args.run_id)
        else:
            result = review(read_json(args.manifest), args.resources)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, allow_nan=False))
        return 0 if result["ok"] else 2
    except (PortableError, StudioMcpError, TransferError, OSError, KeyError, TypeError, ValueError):
        # Stable error category, without input values, private paths, or raw tool output.
        exc = sys.exc_info()[1]
        if isinstance(exc, StudioMcpError):
            code = exc.category
        elif isinstance(exc, PortableError):
            code = str(exc)
        elif isinstance(exc, TransferError):
            code = "INVALID_INVENTORY"
        else:
            code = "INPUT_ERROR"
        print(json.dumps({"ok": False, "error": code, "live_calls": 0}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

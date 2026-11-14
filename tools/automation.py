"""Small offline adapters over SRC-01/02/03. No transport."""
from copy import deepcopy

from . import branch_candidate as branch
from . import portable_validation as portable
from . import schema_subset as schema


def validate(candidate, contract):
    """Anchor both top-level identity and request identity to a synthetic contract."""
    portable.require(isinstance(contract, dict) and set(contract) == {"target", "tools"},
                     "CONTRACT_FIELDS")
    portable.require(isinstance(candidate, dict), "CANDIDATE_FIELDS")
    portable.require(candidate.get("target") == contract["target"], "CONTRACT_TARGET_MISMATCH")
    return portable.validate_candidate(schema, candidate, {"tools": contract["tools"]})


def feedback(data, target, expected_run_id):
    portable.require(isinstance(data, dict), "FEEDBACK_OBJECT")
    portable.require(isinstance(target, dict) and set(target) == {"app_id", "flow_id"},
                     "TARGET_REQUIRED")
    portable.require(all(data.get(k) == v for k, v in target.items()), "FEEDBACK_TARGET_MISMATCH")
    portable.require(isinstance(expected_run_id, str) and expected_run_id
                     and data.get("run_id") == expected_run_id, "RUN_ID_MISMATCH")
    return portable.validate_feedback(data)


def build_example():
    """Synthetic read-back IDs are fixtures, not actual Studio responses."""
    target = {"app_id": "synthetic-app", "flow_id": "synthetic-branch"}
    blocks = [{"block_id": f"synthetic-block-{i}", "block_index": i,
               "prototype_name": row["prototype_name"]}
              for i, row in enumerate(branch.SPECS)]
    return {"schema_version": "1.0", "mode": "offline_only", "target": target,
            "requests": [
                {"name": "flow.edit_blocks", "arguments": branch.insert_arguments(target["flow_id"])},
                {"name": "flow.fill_blocks", "arguments": branch.fill_arguments(target["flow_id"], blocks)}
            ]}


def demo(candidate, contract, pending, completed):
    normal = validate(candidate, contract)
    bad_target = deepcopy(candidate)
    bad_target["requests"][0]["arguments"]["flow_id"] = "different-synthetic-flow"
    bad_input = deepcopy(candidate)
    bad_input["requests"][0]["arguments"]["block_index"] = True
    rejected = {}
    for label, fixture in (("target_mismatch", bad_target), ("invalid_input", bad_input)):
        try:
            validate(fixture, contract)
        except (portable.PortableError, schema.StudioMcpError) as exc:
            rejected[label] = str(exc) if isinstance(exc, portable.PortableError) else exc.category
        else:
            raise AssertionError("Invalid candidate unexpectedly accepted")
    return {"example": "synthetic_automation", "ok": True,
            "node_count": len(branch.SPECS), "request_count": normal["request_count"],
            "candidate_level": normal["level"], "rejections": rejected,
            "pending_state": feedback(pending, contract["target"], "synthetic-run-1")["state"],
            "completed_state": feedback(completed, contract["target"], "synthetic-run-1")["state"],
            "live_calls": 0, "executable": False}

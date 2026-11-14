"""Network-free candidate builder for one six-block VisualFlow experiment.

This is not a live writer. No process discovery, transport, save, run, repair,
or authorization is implemented here. IDs supplied to these pure functions
must be bound to a fresh, approved disposable target by a future live adapter.
"""
from __future__ import annotations

from copy import deepcopy
import json


VARIABLE = "接口验证状态"
TRUE_LOG = "VF_PROBE_TRUE"
FALSE_LOG = "VF_PROBE_FALSE"
SPECS = (
    {"prototype_name": "programing.variable", "comment": "set_probe_status",
     "inputs": {"value_type": "str", "value": {"text": "完成"}},
     "outputs": {"variable": VARIABLE}},
    {"prototype_name": "workflow.if", "comment": "test_probe_status",
     "inputs": {"operand1": {"variable": VARIABLE}, "operator": "==",
                "operand2": {"text": "完成"}}},
    {"prototype_name": "programing.log", "comment": "log_true_branch",
     "inputs": {"type": "info", "text": {"text": TRUE_LOG}}},
    {"prototype_name": "workflow.else", "comment": "start_false_branch"},
    {"prototype_name": "programing.log", "comment": "log_false_branch",
     "inputs": {"type": "info", "text": {"text": FALSE_LOG}}},
    {"prototype_name": "workflow.endif", "comment": "end_probe_condition"},
)


def _require_id(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("missing_id")


def insert_arguments(flow_id):
    """Build arguments only; do not send them or grant permission to send."""
    _require_id(flow_id)
    return {"flow_id": flow_id, "op": "insert", "block_index": -1,
            "blocks": [{"prototype_name": s["prototype_name"],
                        "comment": s["comment"]} for s in SPECS]}


def fill_arguments(flow_id, ordered_blocks):
    """Bind to exactly six independently read-back IDs, never response order.

    Additional/auto-inserted structural nodes require investigation, not
    deletion or a second insert. Field forms must still be checked live.
    """
    _require_id(flow_id)
    if not isinstance(ordered_blocks, list) or len(ordered_blocks) != len(SPECS):
        raise ValueError("unexpected_block_count")
    seen = set()
    fills = []
    for index, (actual, spec) in enumerate(zip(ordered_blocks, SPECS)):
        if not isinstance(actual, dict):
            raise ValueError("invalid_block")
        block_id = actual.get("block_id")
        _require_id(block_id)
        if block_id in seen:
            raise ValueError("duplicate_block_id")
        seen.add(block_id)
        if (type(actual.get("block_index")) is not int
                or actual["block_index"] != index
                or actual.get("prototype_name") != spec["prototype_name"]):
            raise ValueError("unexpected_block_structure")
        if "inputs" in spec:
            item = {"block_id": block_id, "inputs": deepcopy(spec["inputs"])}
            if "outputs" in spec:
                item["outputs"] = deepcopy(spec["outputs"])
            fills.append(item)
    return {"flow_id": flow_id, "fills": fills}


def expected_log(value):
    """Local fixed oracle, NOT a ShadowBot interpreter or execution proof."""
    if not isinstance(value, str):
        raise ValueError("input_must_be_string")
    return TRUE_LOG if value == "完成" else FALSE_LOG


def assess_write_response(response):
    """Never use a success flag as proof of matching live configuration."""
    if not isinstance(response, dict) or response.get("success") is not True:
        return "STOP_AND_READ_BACK"
    if response.get("fill_errors") or response.get("validation_errors"):
        return "STOP_AND_READ_BACK"
    return "READ_BACK_REQUIRED"


def candidate():
    return {"mode": "OFFLINE_CANDIDATE_ONLY", "target": None,
            "live_write_authorized": False, "save_authorized": False,
            "run_authorized": False, "automatic_retry": False,
            "nodes": deepcopy(list(SPECS)), "proposed_input": "完成",
            "expected_true_log": TRUE_LOG, "expected_false_log": FALSE_LOG,
            "runtime_form_fields_verified": False,
            "runtime_if_auto_end_behavior_verified": False,
            "persistence_behavior_verified": False}


if __name__ == "__main__":
    print(json.dumps(candidate(), ensure_ascii=False, indent=2))

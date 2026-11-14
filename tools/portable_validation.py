"""SRC-02: pure offline validation, without client import or CLI transport."""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path

STRUCTURE_TOOLS = frozenset({"app.create_flow", "flow.write_parameters",
                             "flow.edit_blocks", "flow.fill_blocks"})


LIMIT = 2 * 1024 * 1024


class PortableError(Exception):
    pass


def require(condition, code):
    if not condition:
        raise PortableError(code)


def read_json(path):
    path = Path(path)
    require(path.is_file() and path.stat().st_size <= LIMIT, "JSON_FILE_MISSING_OR_TOO_LARGE")
    raw = path.read_bytes()
    def pairs(items):
        obj = {}
        for key, value in items:
            require(key not in obj, "DUPLICATE_JSON_KEY")
            obj[key] = value
        return obj
    def nonfinite(_):
        raise PortableError("NONFINITE_JSON_NUMBER")
    def finite_float(value):
        number = float(value)
        require(math.isfinite(number), "NONFINITE_JSON_NUMBER")
        return number
    try:
        return json.loads(raw.decode("utf-8-sig"), object_pairs_hook=pairs,
                          parse_constant=nonfinite, parse_float=finite_float)
    except (UnicodeError, ValueError) as exc:
        raise PortableError("INVALID_JSON") from exc


def digest(value):
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False,
                     separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def validate_candidate(client, candidate, contract):
    require(isinstance(candidate, dict) and set(candidate) == {
        "schema_version", "mode", "target", "requests"}, "CANDIDATE_FIELDS")
    require(candidate["schema_version"] == "1.0"
            and candidate["mode"] == "offline_only", "CANDIDATE_POLICY")
    target = candidate["target"]
    require(isinstance(target, dict) and set(target) == {"app_id", "flow_id"}
            and all(isinstance(v, str) and v.strip() for v in target.values()), "TARGET_REQUIRED")
    require(isinstance(contract, dict) and set(contract) == {"tools"}
            and isinstance(contract["tools"], list) and contract["tools"], "CONTRACT_FIELDS")
    schemas = {}
    for tool in contract["tools"]:
        require(isinstance(tool, dict) and isinstance(tool.get("name"), str)
                and isinstance(tool.get("inputSchema"), dict), "TOOL_SCHEMA_REQUIRED")
        require(tool["name"] not in schemas, "DUPLICATE_TOOL")
        schemas[tool["name"]] = tool["inputSchema"]
    requests = candidate["requests"]
    require(isinstance(requests, list) and 0 < len(requests) <= 100, "REQUEST_COUNT")
    for request in requests:
        require(isinstance(request, dict) and set(request) == {"name", "arguments"}
                and isinstance(request["arguments"], dict), "REQUEST_OBJECT_REQUIRED")
        name, args = request["name"], request["arguments"]
        require(isinstance(name, str) and name in STRUCTURE_TOOLS and name in schemas,
                "UNSUPPORTED_OFFLINE_TOOL")
        for key in ("app_id", "flow_id"):
            require(key not in args or args[key] == target[key], "REQUEST_TARGET_MISMATCH")
        client.ensure_supported_schema(schemas[name])
        client.validate_json_schema(args, schemas[name])
    return {"ok": True, "level": "offline_request_schema_only",
            "request_count": len(requests), "candidate_sha256": digest(candidate),
            "contract_sha256": digest(contract), "network_calls": 0,
            "semantic_dependencies_verified": False, "current_contract_verified": False,
            "executable": False, "write_save_run_business_authorized": False}


def validate_feedback(data):
    require(isinstance(data, dict) and isinstance(data.get("run_id"), str)
            and bool(data["run_id"].strip()) and isinstance(data.get("flow_id"), str)
            and bool(data["flow_id"].strip()), "RUN_ID_AND_FLOW_REQUIRED")
    status, active, succeeded = (data.get(k) for k in
                                  ("terminal_status", "active", "run_succeeded"))
    if status in (None, "running", "pending") and active is True and succeeded is None:
        state = "pending"
    elif status in ("completed", "succeeded") and active is False and succeeded is True:
        v = data.get("verification")
        require(isinstance(v, dict) and v.get("checked_after_finish") is True
                and all(type(v.get(k)) is int and v[k] == 0 for k in
                        ("static_error_count", "runtime_error_count"))
                and "error" in v and v["error"] is None
                and "latest_runtime_error" in v and v["latest_runtime_error"] is None,
                "COMPLETION_VERIFICATION_REQUIRED")
        state = "completed"
    elif status == "failed" and active is False and succeeded is False:
        state = "failed"
    elif status in ("stopped", "paused") and succeeded is not True:
        require(type(active) is bool, "UNKNOWN_RUN_STATE")
        state = "human_attention"
    else:
        raise PortableError("UNKNOWN_RUN_STATE")
    return {"ok": True, "state": state, "level": "canonical_status_only",
            "output_and_business_verified": False, "network_calls": 0,
            "may_rerun": False, "live_authorized": False}

"""SRC-03: extracted pure JSON Schema subset; no client or transport."""
from __future__ import annotations
import math
import re
from typing import Any, Mapping

SUPPORTED_SCHEMA_KEYWORDS = frozenset(
    {
        "$comment",
        "$id",
        "$schema",
        "additionalProperties",
        "allOf",
        "anyOf",
        "const",
        "default",
        "deprecated",
        "description",
        "enum",
        "examples",
        "exclusiveMaximum",
        "exclusiveMinimum",
        "items",
        "maxItems",
        "maxLength",
        "maximum",
        "minItems",
        "minLength",
        "minProperties",
        "minimum",
        "oneOf",
        "pattern",
        "properties",
        "readOnly",
        "required",
        "title",
        "type",
        "writeOnly",
    }
)


class StudioMcpError(RuntimeError):
    def __init__(
        self,
        category: str,
        message: str,
        *,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.category = category
        self.message = message
        self.details = dict(details or {})

    def payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "ok": False,
            "error": self.category,
            "message": self.message,
        }
        if self.details:
            payload["details"] = self.details
        return payload


def _type_matches(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
    if expected == "null":
        return value is None
    return False


def _nonnegative_integer_schema_keyword(
    schema: Mapping[str, Any], keyword: str, path: str
) -> int | None:
    if keyword not in schema:
        return None
    value = schema[keyword]
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise StudioMcpError(
            "SCHEMA_ERROR",
            f"{keyword} must be a non-negative integer.",
            details={"path": path},
        )
    return value


def ensure_supported_schema(schema: Mapping[str, Any], path: str = "$") -> None:
    unsupported = sorted(set(schema) - SUPPORTED_SCHEMA_KEYWORDS)
    if unsupported:
        raise StudioMcpError(
            "SCHEMA_ERROR",
            "Tool inputSchema contains unsupported keywords.",
            details={"path": path, "keywords": unsupported},
        )
    _nonnegative_integer_schema_keyword(schema, "minProperties", path)
    properties = schema.get("properties")
    if properties is not None:
        if not isinstance(properties, dict):
            raise StudioMcpError("SCHEMA_ERROR", "properties must be an object.")
        for key, child in properties.items():
            if not isinstance(child, dict):
                raise StudioMcpError("SCHEMA_ERROR", "property schema must be an object.")
            ensure_supported_schema(child, f"{path}.properties.{key}")
    additional = schema.get("additionalProperties")
    if isinstance(additional, dict):
        ensure_supported_schema(additional, f"{path}.additionalProperties")
    items = schema.get("items")
    if isinstance(items, dict):
        ensure_supported_schema(items, f"{path}.items")
    for keyword in ("allOf", "anyOf", "oneOf"):
        branches = schema.get(keyword)
        if branches is None:
            continue
        if not isinstance(branches, list) or not branches:
            raise StudioMcpError("SCHEMA_ERROR", f"{keyword} must be a non-empty array.")
        for index, branch in enumerate(branches):
            if not isinstance(branch, dict):
                raise StudioMcpError("SCHEMA_ERROR", f"{keyword} branch must be an object.")
            ensure_supported_schema(branch, f"{path}.{keyword}[{index}]")


def validate_json_schema(value: Any, schema: Mapping[str, Any], path: str = "$") -> None:
    if "$ref" in schema:
        raise StudioMcpError(
            "SCHEMA_ERROR",
            "External or local $ref is not supported by the phase-B validator.",
            details={"path": path},
        )

    for keyword in ("allOf", "anyOf", "oneOf"):
        if keyword not in schema:
            continue
        branches = schema[keyword]
        if not isinstance(branches, list) or not branches:
            raise StudioMcpError("SCHEMA_ERROR", f"{keyword} must be a non-empty array.")
        successes = 0
        branch_errors: list[str] = []
        for branch in branches:
            if not isinstance(branch, dict):
                raise StudioMcpError("SCHEMA_ERROR", f"{keyword} branch must be an object.")
            try:
                validate_json_schema(value, branch, path)
                successes += 1
            except StudioMcpError as exc:
                branch_errors.append(exc.message)
        if keyword == "allOf" and successes != len(branches):
            raise StudioMcpError("CLIENT_INPUT_ERROR", f"{path} does not satisfy allOf.")
        if keyword == "anyOf" and successes == 0:
            raise StudioMcpError("CLIENT_INPUT_ERROR", f"{path} does not satisfy anyOf.")
        if keyword == "oneOf" and successes != 1:
            raise StudioMcpError("CLIENT_INPUT_ERROR", f"{path} does not satisfy exactly one oneOf branch.")

    if "const" in schema and value != schema["const"]:
        raise StudioMcpError("CLIENT_INPUT_ERROR", f"{path} does not match const.")
    if "enum" in schema:
        enum_values = schema["enum"]
        if not isinstance(enum_values, list):
            raise StudioMcpError("SCHEMA_ERROR", "enum must be an array.")
        if value not in enum_values:
            raise StudioMcpError("CLIENT_INPUT_ERROR", f"{path} is not an allowed enum value.")

    expected = schema.get("type")
    if expected is not None:
        expected_types = [expected] if isinstance(expected, str) else expected
        if not isinstance(expected_types, list) or not all(isinstance(item, str) for item in expected_types):
            raise StudioMcpError("SCHEMA_ERROR", "type must be a string or string array.")
        if not any(_type_matches(value, item) for item in expected_types):
            raise StudioMcpError(
                "CLIENT_INPUT_ERROR",
                f"{path} has the wrong JSON type.",
                details={"expected": expected_types, "actual": type(value).__name__},
            )

    if isinstance(value, dict):
        min_properties = _nonnegative_integer_schema_keyword(
            schema, "minProperties", path
        )
        if min_properties is not None and len(value) < min_properties:
            raise StudioMcpError(
                "CLIENT_INPUT_ERROR", f"{path} has too few properties."
            )
        required = schema.get("required", [])
        if not isinstance(required, list) or not all(isinstance(item, str) for item in required):
            raise StudioMcpError("SCHEMA_ERROR", "required must be a string array.")
        missing = [item for item in required if item not in value]
        if missing:
            raise StudioMcpError(
                "CLIENT_INPUT_ERROR",
                f"{path} is missing required fields.",
                details={"missing": missing},
            )
        properties = schema.get("properties", {})
        if not isinstance(properties, dict):
            raise StudioMcpError("SCHEMA_ERROR", "properties must be an object.")
        additional = schema.get("additionalProperties", True)
        for key, item in value.items():
            if key in properties:
                child_schema = properties[key]
                if not isinstance(child_schema, dict):
                    raise StudioMcpError("SCHEMA_ERROR", "property schema must be an object.")
                validate_json_schema(item, child_schema, f"{path}.{key}")
            elif additional is False:
                raise StudioMcpError(
                    "CLIENT_INPUT_ERROR",
                    f"{path} contains an unknown field.",
                    details={"field": key},
                )
            elif isinstance(additional, dict):
                validate_json_schema(item, additional, f"{path}.{key}")

    if isinstance(value, list):
        min_items = schema.get("minItems")
        max_items = schema.get("maxItems")
        if isinstance(min_items, int) and len(value) < min_items:
            raise StudioMcpError("CLIENT_INPUT_ERROR", f"{path} has too few items.")
        if isinstance(max_items, int) and len(value) > max_items:
            raise StudioMcpError("CLIENT_INPUT_ERROR", f"{path} has too many items.")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                validate_json_schema(item, item_schema, f"{path}[{index}]")

    if isinstance(value, str):
        min_length = schema.get("minLength")
        max_length = schema.get("maxLength")
        if isinstance(min_length, int) and len(value) < min_length:
            raise StudioMcpError("CLIENT_INPUT_ERROR", f"{path} is too short.")
        if isinstance(max_length, int) and len(value) > max_length:
            raise StudioMcpError("CLIENT_INPUT_ERROR", f"{path} is too long.")
        pattern = schema.get("pattern")
        if isinstance(pattern, str):
            try:
                matches = re.search(pattern, value)
            except re.error as exc:
                raise StudioMcpError(
                    "SCHEMA_ERROR",
                    "Tool inputSchema contains an invalid regular expression.",
                    details={"path": path},
                ) from exc
            if matches is None:
                raise StudioMcpError("CLIENT_INPUT_ERROR", f"{path} does not match pattern.")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        minimum = schema.get("minimum")
        maximum = schema.get("maximum")
        exclusive_minimum = schema.get("exclusiveMinimum")
        exclusive_maximum = schema.get("exclusiveMaximum")
        if isinstance(minimum, (int, float)) and value < minimum:
            raise StudioMcpError("CLIENT_INPUT_ERROR", f"{path} is below minimum.")
        if isinstance(maximum, (int, float)) and value > maximum:
            raise StudioMcpError("CLIENT_INPUT_ERROR", f"{path} is above maximum.")
        if isinstance(exclusive_minimum, (int, float)) and value <= exclusive_minimum:
            raise StudioMcpError("CLIENT_INPUT_ERROR", f"{path} is not above exclusiveMinimum.")
        if isinstance(exclusive_maximum, (int, float)) and value >= exclusive_maximum:
            raise StudioMcpError("CLIENT_INPUT_ERROR", f"{path} is not below exclusiveMaximum.")

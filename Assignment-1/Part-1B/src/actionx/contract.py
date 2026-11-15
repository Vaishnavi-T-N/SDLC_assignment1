"""Output-contract validation (Layer 1) and the reduced schema for Gemini (pure, no I/O)."""

from __future__ import annotations

from typing import Any

from jsonschema import Draft202012Validator

_GEMINI_KEYWORDS = frozenset(
    {
        "type",
        "properties",
        "required",
        "additionalProperties",
        "items",
        "enum",
        "minimum",
        "maximum",
        "minItems",
        "maxItems",
        "description",
    }
)


def validate_output(schema: dict[str, Any], value: Any) -> list[str]:
    """Return schema violations as 'path: message' strings (empty list means valid)."""
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(value), key=lambda e: [str(p) for p in e.absolute_path])
    return [
        f"{'/'.join(str(p) for p in error.absolute_path) or '<root>'}: {error.message}"
        for error in errors
    ]


def gemini_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Reduce the contract schema to the keywords Gemini's structured output supports."""

    def reduce(node: Any) -> Any:
        if not isinstance(node, dict):
            return node
        reduced: dict[str, Any] = {}
        for key, value in node.items():
            if key not in _GEMINI_KEYWORDS:
                continue
            if key == "properties":
                reduced[key] = {name: reduce(sub) for name, sub in value.items()}
            elif key in ("items", "additionalProperties"):
                reduced[key] = reduce(value)
            else:
                reduced[key] = value
        return reduced

    return reduce(schema)

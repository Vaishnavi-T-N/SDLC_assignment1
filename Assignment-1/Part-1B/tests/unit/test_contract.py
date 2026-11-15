"""AC-15, AC-16 (schema contract) and the Layer 1 defects of AC-14."""

from __future__ import annotations

import copy

import pytest
from jsonschema import Draft202012Validator

from actionx.contract import gemini_schema, validate_output
from support import SCHEMA, good_output


def test_ac15_schema_is_valid_draft_2020_12_and_accepts_example():
    Draft202012Validator.check_schema(SCHEMA)
    assert validate_output(SCHEMA, good_output()) == []
    assert validate_output(SCHEMA, good_output(items=[])) == []


def _mutations():
    def extra(o):
        o["surprise"] = 1

    def missing(o):
        del o["refusal"]

    def wrong_type(o):
        o["needs_clarification"] = "yes"

    def conf_high(o):
        o["action_items"][0]["confidence"] = 1.5

    def conf_negative(o):
        o["action_items"][0]["confidence"] = -0.1

    def due_format(o):
        o["action_items"][0]["due_date"] = "tomorrow"

    def owner_type(o):
        o["action_items"][0]["owner"] = 7

    def item_extra(o):
        o["action_items"][0]["priority"] = "high"

    def item_missing(o):
        del o["action_items"][0]["evidence"]

    def conf_bool(o):
        o["action_items"][0]["confidence"] = True

    return [
        extra,
        missing,
        wrong_type,
        conf_high,
        conf_negative,
        due_format,
        owner_type,
        item_extra,
        item_missing,
        conf_bool,
    ]


@pytest.mark.parametrize("mutate", _mutations(), ids=lambda f: f.__name__)
def test_ac15_ac14_each_defect_is_refused(mutate):
    bad = copy.deepcopy(good_output())
    mutate(bad)
    assert validate_output(SCHEMA, bad)


def test_validate_output_reports_path():
    bad = good_output()
    bad["action_items"][0]["confidence"] = 2
    assert validate_output(SCHEMA, bad)[0].startswith("action_items/0/confidence")
    assert validate_output(SCHEMA, [])[0].startswith("<root>")


def test_ac16_gemini_schema_keeps_supported_keywords_only():
    reduced = gemini_schema(SCHEMA)
    text = str(reduced)
    for dropped in ("$schema", "$id", "pattern", "title"):
        assert dropped not in text
    assert reduced["required"] == SCHEMA["required"]
    assert reduced["type"] == "object"
    item = reduced["properties"]["action_items"]["items"]
    assert item["properties"]["confidence"] == {"type": "number", "minimum": 0, "maximum": 1}
    assert item["properties"]["due_date"] == {"type": ["string", "null"]}
    assert reduced["additionalProperties"] is False

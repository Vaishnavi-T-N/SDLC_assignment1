"""Unit tests for canonical output rendering (FR-17, FR-18, FR-20, AC-27, AC-28)."""

import json
from datetime import UTC, datetime

from slotfinder.errors import ErrorCode
from slotfinder.output import format_utc, render_error, render_success


def test_ac27_success_is_compact_sorted_with_single_lf():
    """AC-27 / FR-17, FR-20: exact bytes of a one-slot success document."""
    slot = (datetime(2025, 1, 6, 9, tzinfo=UTC), datetime(2025, 1, 6, 17, 30, 5, tzinfo=UTC))
    assert render_success([slot]) == (
        '{"slots":[{"end":"2025-01-06T17:30:05Z","start":"2025-01-06T09:00:00Z"}]}\n'
    )


def test_ac20_empty_slot_list_renders_exactly():
    """AC-20 / FR-17: no slots renders the empty list."""
    assert render_success([]) == '{"slots":[]}\n'


def test_ac27_no_carriage_return_or_extra_whitespace():
    """AC-27 / FR-20: output has no CR and exactly one trailing LF."""
    slot = (datetime(2025, 1, 6, 9, tzinfo=UTC), datetime(2025, 1, 6, 10, tzinfo=UTC))
    text = render_success([slot])
    assert "\r" not in text
    assert text.endswith("}\n")
    assert not text.endswith("\n\n")
    assert " " not in text


def test_ac28_error_document_shape_and_exact_text():
    """AC-28 / FR-18: exact bytes of an error document."""
    assert render_error(ErrorCode.INVALID_WINDOW, "bad window") == (
        '{"error":{"code":"INVALID_WINDOW","message":"bad window"}}\n'
    )


def test_ac28_every_error_code_renders_its_own_name():
    """AC-28 / FR-18: the nine codes render as their stable names."""
    expected = [
        "INVALID_JSON",
        "MISSING_FIELD",
        "NAIVE_DATETIME",
        "INVALID_INTERVAL",
        "INVALID_TIMEZONE",
        "INVALID_WORKING_HOURS",
        "INVALID_DURATION",
        "INVALID_WINDOW",
        "TOO_MANY_PARTICIPANTS",
    ]
    assert [c.value for c in ErrorCode] == expected
    for code in ErrorCode:
        assert json.loads(render_error(code, "m"))["error"]["code"] == code.value


def test_fr20_non_ascii_message_is_escaped_deterministically():
    """FR-20: JSON output is pure ASCII so bytes do not depend on the console encoding."""
    text = render_error(ErrorCode.INVALID_JSON, "café")
    assert text == '{"error":{"code":"INVALID_JSON","message":"caf\\u00e9"}}\n'


def test_ac26_format_utc_has_seconds_precision_and_z_suffix():
    """AC-26 / FR-17: timestamps are YYYY-MM-DDTHH:MM:SSZ."""
    assert format_utc(datetime(2025, 3, 9, 7, 30, tzinfo=UTC)) == "2025-03-09T07:30:00Z"

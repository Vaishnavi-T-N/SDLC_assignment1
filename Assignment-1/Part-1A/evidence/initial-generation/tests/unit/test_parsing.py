"""Unit tests for request validation and error codes (FR-03 to FR-13, FR-19, FR-22)."""

import copy
from datetime import timedelta
from typing import Any

import pytest
from support import busy, code_of, participant, request

from slotfinder.parsing import parse_request


def with_busy(*intervals: dict[str, str]) -> dict[str, Any]:
    return request([participant(busy=list(intervals))])


# ---- AC-06, AC-07: busy interval ordering (FR-13) -------------------------------------------


def test_ac06_zero_length_busy_is_invalid_interval():
    """AC-06 / FR-13: start == end is rejected."""
    data = with_busy(busy("2025-01-06T10:00:00Z", "2025-01-06T10:00:00Z"))
    assert code_of(data) == "INVALID_INTERVAL"


def test_ac07_reversed_busy_is_invalid_interval():
    """AC-07 / FR-13: end before start is rejected."""
    data = with_busy(busy("2025-01-06T11:00:00Z", "2025-01-06T10:00:00Z"))
    assert code_of(data) == "INVALID_INTERVAL"


# ---- AC-09 to AC-11: datetime handling (FR-04) ---------------------------------------------

NAIVE = "2025-01-06T10:00:00"


@pytest.mark.parametrize(
    "data",
    [
        request(start=NAIVE),
        request(end=NAIVE),
        with_busy(busy(NAIVE, "2025-01-06T11:00:00Z")),
        with_busy(busy("2025-01-06T10:00:00Z", NAIVE)),
        request(start="2025-01-06"),
    ],
    ids=["window.start", "window.end", "busy.start", "busy.end", "date-only"],
)
def test_ac09_naive_datetime_is_rejected(data):
    """AC-09 / FR-04: a datetime without an offset is NAIVE_DATETIME in every position."""
    assert code_of(data) == "NAIVE_DATETIME"


@pytest.mark.parametrize("bad", ["tomorrow", "2025-13-45T00:00:00Z", "", 12345, None, ["x"]])
def test_ac10_unparseable_window_bound_is_invalid_window(bad):
    """AC-10 / FR-04: unparseable or non-string window bounds give INVALID_WINDOW."""
    assert code_of(request(start=bad)) == "INVALID_WINDOW"
    assert code_of(request(end=bad)) == "INVALID_WINDOW"


@pytest.mark.parametrize("bad", ["tomorrow", "2025-13-45T00:00:00Z", "", 12345, None, ["x"]])
def test_ac10_unparseable_busy_bound_is_invalid_interval(bad):
    """AC-10 / FR-04: unparseable or non-string busy bounds give INVALID_INTERVAL."""
    assert code_of(with_busy(busy(bad, "2025-01-06T11:00:00Z"))) == "INVALID_INTERVAL"
    assert code_of(with_busy(busy("2025-01-06T10:00:00Z", bad))) == "INVALID_INTERVAL"


@pytest.mark.parametrize(
    "bad",
    [
        "2025-01-06T10:00:00.5Z",
        "2025-01-06T10:00:00.000001+00:00",
        "3000-01-01T00:00:00Z",
        "1900-12-31T23:59:59Z",
        "0001-01-01T00:00:00+05:00",
        "9999-12-31T23:59:59-05:00",
    ],
)
def test_ac11_fractional_seconds_and_extreme_years_are_rejected(bad):
    """AC-11 / FR-04: fractional seconds and years outside 1901-2999 use the context code."""
    assert code_of(request(start=bad)) == "INVALID_WINDOW"
    assert code_of(with_busy(busy(bad, "2999-12-31T23:59:59Z"))) == "INVALID_INTERVAL"


def test_ac11_supported_year_range_edges_are_accepted():
    """AC-11 / FR-04: 1901-01-01 and 2999-12-31 UTC are inside the supported range."""
    parsed = parse_request(request(start="1901-01-01T00:00:00Z", end="2999-12-31T23:59:59Z"))
    assert parsed.window[0].year == 1901
    assert parsed.window[1].year == 2999


def test_ac26_offsets_normalise_to_utc_in_the_model():
    """AC-26 / FR-04: +05:30 is converted to the equivalent UTC instant."""
    parsed = parse_request(request(start="2025-01-06T05:30:00+05:30"))
    assert parsed.window[0].isoformat() == "2025-01-06T00:00:00+00:00"


# ---- AC-12: timezone (FR-10, FR-22) ---------------------------------------------------------


@pytest.mark.parametrize(
    "bad",
    [
        "Not/AZone",
        "",
        "../etc/passwd",
        "America",
        123,
        None,
        "America/New York",
        "/UTC",
        "UTC/",
        "America//New_York",
        "A" * 65,
        "America/New_York\n",
        "Europe/Londön",
        "UTC; rm -rf",
    ],
)
def test_ac12_invalid_timezone_is_rejected(bad):
    """AC-12 / FR-10, FR-22: unknown, empty, non-string or unsafe keys give INVALID_TIMEZONE."""
    assert code_of(request([participant(tz=bad)])) == "INVALID_TIMEZONE"


@pytest.mark.parametrize(
    "good", ["UTC", "Europe/London", "Etc/GMT+5", "America/Argentina/Buenos_Aires", "Asia/Kolkata"]
)
def test_ac12_valid_timezone_keys_are_accepted(good):
    """AC-12 / FR-10: real IANA keys pass the allow-list and resolve."""
    parsed = parse_request(request([participant(tz=good)]))
    assert str(parsed.participants[0].tz) == good


# ---- AC-13: working hours (FR-11) -----------------------------------------------------------


@pytest.mark.parametrize(
    ("start", "end"),
    [
        ("17:00", "09:00"),
        ("09:00", "09:00"),
        ("22:00", "06:00"),
        ("9:00", "17:00"),
        ("09:00", "24:00"),
        ("09:00", "17:60"),
        ("09:00:00", "17:00"),
        (900, "17:00"),
        ("09:00", None),
        ("0٩:00", "17:00"),
        ("09:00\n", "17:00"),
    ],
)
def test_ac13_invalid_working_hours_are_rejected(start, end):
    """AC-13 / FR-11: bad format, end <= start and overnight ranges give INVALID_WORKING_HOURS."""
    assert code_of(request([participant(start=start, end=end)])) == "INVALID_WORKING_HOURS"


def test_ac13_boundary_working_hours_are_accepted():
    """AC-13 / FR-11: 00:00-23:59 is the widest valid range."""
    parsed = parse_request(request([participant(start="00:00", end="23:59")]))
    hours = parsed.participants[0].working_hours
    assert (hours.start.hour, hours.start.minute) == (0, 0)
    assert (hours.end.hour, hours.end.minute) == (23, 59)


# ---- AC-14: duration (FR-07) ----------------------------------------------------------------


@pytest.mark.parametrize("bad", [0, 1441, -5, "30", 30.0, True, False, None, [30]])
def test_ac14_invalid_duration_is_rejected(bad):
    """AC-14 / FR-07: out-of-range, non-integer and boolean durations give INVALID_DURATION."""
    assert code_of(request(duration=bad)) == "INVALID_DURATION"


@pytest.mark.parametrize("good", [1, 1440])
def test_ac14_duration_bounds_are_accepted(good):
    """AC-14 / FR-07: 1 and 1440 are valid."""
    assert parse_request(request(duration=good)).min_duration == timedelta(minutes=good)


# ---- AC-15: window ordering (FR-06) ---------------------------------------------------------


def test_ac15_window_end_equal_to_start_is_invalid():
    """AC-15 / FR-06: an empty window is rejected."""
    assert code_of(request(start="2025-01-06T00:00:00Z", end="2025-01-06T00:00:00Z")) == (
        "INVALID_WINDOW"
    )


def test_ac15_window_end_before_start_is_invalid():
    """AC-15 / FR-06: a reversed window is rejected."""
    assert code_of(request(start="2025-01-07T00:00:00Z", end="2025-01-06T00:00:00Z")) == (
        "INVALID_WINDOW"
    )


def test_ac15_equal_instants_in_different_offsets_are_still_empty():
    """AC-15 / FR-06: comparison is on the instant, not the text."""
    assert code_of(request(start="2025-01-06T01:00:00+01:00", end="2025-01-06T00:00:00Z")) == (
        "INVALID_WINDOW"
    )


# ---- AC-16: participant count (FR-08) -------------------------------------------------------


def test_ac16_twenty_one_participants_is_too_many():
    """AC-16 / FR-08: 21 participants give TOO_MANY_PARTICIPANTS."""
    data = request([participant(f"p{i}") for i in range(21)])
    assert code_of(data) == "TOO_MANY_PARTICIPANTS"


def test_ac16_twenty_participants_are_accepted():
    """AC-16 / FR-08: 20 participants are valid."""
    parsed = parse_request(request([participant(f"p{i}") for i in range(20)]))
    assert len(parsed.participants) == 20


def test_ac16_empty_participants_is_missing_field():
    """AC-16 / FR-08: an empty list gives MISSING_FIELD."""
    assert code_of(request([])) == "MISSING_FIELD"


# ---- AC-17: missing fields and wrong containers (FR-03, FR-09, FR-13) -------------------------


def _without(path: list[Any]) -> dict[str, Any]:
    data = request([participant(busy=[busy("2025-01-06T10:00:00Z", "2025-01-06T11:00:00Z")])])
    target: Any = data
    for key in path[:-1]:
        target = target[key]
    del target[path[-1]]
    return data


@pytest.mark.parametrize(
    "path",
    [
        ["window"],
        ["min_duration_minutes"],
        ["participants"],
        ["window", "start"],
        ["window", "end"],
        ["participants", 0, "id"],
        ["participants", 0, "timezone"],
        ["participants", 0, "working_hours"],
        ["participants", 0, "working_hours", "start"],
        ["participants", 0, "working_hours", "end"],
        ["participants", 0, "busy"],
        ["participants", 0, "busy", 0, "start"],
        ["participants", 0, "busy", 0, "end"],
    ],
    ids=lambda path: ".".join(str(p) for p in path),
)
def test_ac17_omitted_required_field_is_missing_field(path):
    """AC-17 / FR-03, FR-09, FR-13: every required field is enforced with MISSING_FIELD."""
    assert code_of(_without(path)) == "MISSING_FIELD"


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d.update(participants={"a": 1}),
        lambda d: d.update(window=["2025-01-06T00:00:00Z", "2025-01-07T00:00:00Z"]),
        lambda d: d["participants"].__setitem__(0, "not-an-object"),
        lambda d: d["participants"][0].update(busy={"start": 1}),
        lambda d: d["participants"][0].update(working_hours="09:00-17:00"),
        lambda d: d["participants"][0]["busy"].append("not-an-object"),
        lambda d: d["participants"][0].update(id=""),
        lambda d: d["participants"][0].update(id=5),
    ],
    ids=[
        "participants-object",
        "window-list",
        "participant-string",
        "busy-object",
        "working-hours-string",
        "busy-entry-string",
        "id-empty",
        "id-number",
    ],
)
def test_ac17_wrong_container_type_or_bad_id_is_missing_field(mutate):
    """AC-17 / FR-03, FR-09: wrong container types and an empty or non-string id."""
    data = request()
    mutate(data)
    assert code_of(data) == "MISSING_FIELD"


def test_ac17_duplicate_participant_ids_are_allowed():
    """FR-09: ids are labels; uniqueness is not enforced."""
    parsed = parse_request(request([participant("same"), participant("same")]))
    assert [p.id for p in parsed.participants] == ["same", "same"]


# ---- AC-18: top-level value (FR-02) ---------------------------------------------------------


@pytest.mark.parametrize("value", [[], "text", 5, None, True])
def test_ac18_top_level_non_object_is_invalid_json(value):
    """AC-18 / FR-02: a top-level value that is not an object gives INVALID_JSON."""
    assert code_of(value) == "INVALID_JSON"


# ---- AC-32: validation precedence (FR-19) ---------------------------------------------------


def test_ac32_duration_is_reported_before_timezone():
    """AC-32 / FR-19: invalid duration beats an invalid timezone."""
    data = request([participant(tz="Nope/Zone")], duration=0)
    assert code_of(data) == "INVALID_DURATION"


def test_ac32_duration_is_reported_before_window():
    """AC-32 / FR-19: invalid duration beats an invalid window."""
    assert code_of(request(start="garbage", duration=0)) == "INVALID_DURATION"


def test_ac32_missing_top_level_field_beats_invalid_duration():
    """AC-32 / FR-19: missing participants beats invalid duration."""
    data = request(duration=0)
    del data["participants"]
    assert code_of(data) == "MISSING_FIELD"


def test_ac32_window_is_reported_before_participant_count():
    """AC-32 / FR-19: invalid window beats TOO_MANY_PARTICIPANTS."""
    data = request([participant(f"p{i}") for i in range(21)], start="garbage")
    assert code_of(data) == "INVALID_WINDOW"


def test_ac32_participant_count_is_reported_before_participant_faults():
    """AC-32 / FR-19: TOO_MANY_PARTICIPANTS beats a fault inside a participant."""
    people = [participant(f"p{i}") for i in range(21)]
    people[0] = participant("p0", tz="Nope/Zone")
    assert code_of(request(people)) == "TOO_MANY_PARTICIPANTS"


def test_ac32_earlier_participant_fault_wins():
    """AC-32 / FR-19: the earlier participant's fault is reported."""
    data = request([participant("a", start="17:00", end="09:00"), participant("b", tz="Nope/Zone")])
    assert code_of(data) == "INVALID_WORKING_HOURS"
    swapped = request(
        [participant("b", tz="Nope/Zone"), participant("a", start="17:00", end="09:00")]
    )
    assert code_of(swapped) == "INVALID_TIMEZONE"


def test_ac32_within_a_participant_fields_are_checked_in_order():
    """AC-32 / FR-19: missing field, then timezone, then working hours, then busy."""
    bad_busy = [busy("2025-01-06T11:00:00Z", "2025-01-06T10:00:00Z")]
    everything = participant(tz="Nope/Zone", start="17:00", end="09:00", busy=bad_busy)
    assert code_of(request([everything])) == "INVALID_TIMEZONE"
    hours_and_busy = participant(start="17:00", end="09:00", busy=bad_busy)
    assert code_of(request([hours_and_busy])) == "INVALID_WORKING_HOURS"
    missing = participant(tz="Nope/Zone")
    del missing["busy"]
    assert code_of(request([missing])) == "MISSING_FIELD"


def test_ac32_earlier_busy_fault_wins_and_naive_beats_later_order_fault():
    """AC-32 / FR-19: busy intervals are checked in list order, start before end."""
    data = with_busy(
        busy("2025-01-06T10:00:00", "2025-01-06T11:00:00Z"),
        busy("2025-01-06T12:00:00Z", "2025-01-06T11:00:00Z"),
    )
    assert code_of(data) == "NAIVE_DATETIME"


def test_parse_does_not_mutate_its_input():
    """FR-20: parsing leaves the decoded request untouched."""
    data = request([participant(busy=[busy("2025-01-06T10:00:00Z", "2025-01-06T11:00:00Z")])])
    snapshot = copy.deepcopy(data)
    parse_request(data)
    assert data == snapshot

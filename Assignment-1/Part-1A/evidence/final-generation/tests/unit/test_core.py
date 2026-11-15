"""Unit tests for slot computation, derived from the acceptance criteria in spec.md."""

import pytest

from support import busy, participant, request, slots_of

D6 = "2025-01-06T"


def at(hh_mm: str, day: str = D6) -> str:
    return f"{day}{hh_mm}:00Z"


def test_ac01_single_utc_participant_whole_day():
    """AC-01 / FR-15, FR-17: one slot covering the working hours."""
    assert slots_of(request()) == [(at("09:00"), at("17:00"))]


def test_ac02_new_york_and_london_overlap():
    """AC-02 / FR-12, FR-15: 09-17 in New York and London overlap at 14:00-17:00Z in winter."""
    data = request(
        [participant("a", "America/New_York"), participant("b", "Europe/London")],
    )
    assert slots_of(data) == [(at("14:00"), at("17:00"))]


def test_ac03_adjacent_busy_intervals_leave_boundary_touching_slots():
    """AC-03 / FR-05, FR-14: [10,11) and [11,12) busy leave [09,10) and [12,17)."""
    data = request(
        [participant(busy=[busy(at("10:00"), at("11:00")), busy(at("11:00"), at("12:00"))])]
    )
    assert slots_of(data) == [(at("09:00"), at("10:00")), (at("12:00"), at("17:00"))]


def test_ac04_overlapping_busy_equals_single_union():
    """AC-04 / FR-14: overlapping busy intervals behave as their union."""
    overlapping = request(
        [participant(busy=[busy(at("10:00"), at("12:00")), busy(at("11:00"), at("13:00"))])]
    )
    single = request([participant(busy=[busy(at("10:00"), at("13:00"))])])
    expected = [(at("09:00"), at("10:00")), (at("13:00"), at("17:00"))]
    assert slots_of(overlapping) == expected
    assert slots_of(single) == expected


def test_ac05_duplicate_busy_equals_single():
    """AC-05 / FR-14: a duplicated busy interval changes nothing."""
    twice = request(
        [participant(busy=[busy(at("10:00"), at("11:00")), busy(at("10:00"), at("11:00"))])]
    )
    once = request([participant(busy=[busy(at("10:00"), at("11:00"))])])
    assert slots_of(twice) == slots_of(once) == [
        (at("09:00"), at("10:00")),
        (at("11:00"), at("17:00")),
    ]


def test_ac08_busy_outside_window_is_ignored():
    """AC-08 / FR-14: busy entirely before or after the window has no effect and no error."""
    data = request(
        [
            participant(
                busy=[
                    busy("2025-01-05T08:00:00Z", "2025-01-05T18:00:00Z"),
                    busy("2025-01-08T08:00:00Z", "2025-01-08T18:00:00Z"),
                ]
            )
        ]
    )
    assert slots_of(data) == [(at("09:00"), at("17:00"))]


def test_ac08_busy_straddling_window_edges_removes_only_overlap():
    """AC-08 / FR-14: busy straddling the window start or end removes only the overlap."""
    data = request(
        [
            participant(
                busy=[
                    busy("2025-01-05T23:00:00Z", at("10:00")),
                    busy(at("16:00"), "2025-01-07T05:00:00Z"),
                ]
            )
        ]
    )
    assert slots_of(data) == [(at("10:00"), at("16:00"))]


def test_ac19_slot_of_exactly_minimum_duration_is_kept():
    """AC-19 / FR-16: a free range equal to the minimum duration is returned."""
    data = request([participant(start="09:00", end="10:00")], duration=60)
    assert slots_of(data) == [(at("09:00"), at("10:00"))]


def test_ac19_slot_one_minute_too_short_is_omitted():
    """AC-19 / FR-16: a free range one minute shorter than the minimum is omitted."""
    data = request([participant(start="09:00", end="09:59")], duration=60)
    assert slots_of(data) == []


def test_ac20_no_common_time_gives_empty_list():
    """AC-20 / FR-17: disjoint working hours yield no slot."""
    data = request(
        [participant("a", start="09:00", end="12:00"), participant("b", start="13:00", end="17:00")]
    )
    assert slots_of(data) == []


def test_ac20_busy_covering_working_hours_gives_empty_list():
    """AC-20 / FR-15: busy for the whole working day leaves nothing."""
    data = request([participant(busy=[busy(at("08:00"), at("18:00"))])])
    assert slots_of(data) == []


def test_ac21_new_york_spring_forward_working_days():
    """AC-21 / FR-12: EST before the transition, EDT on and after 2025-03-09."""
    data = request(
        [participant(tz="America/New_York")],
        start="2025-03-08T00:00:00Z",
        end="2025-03-11T00:00:00Z",
    )
    assert slots_of(data) == [
        ("2025-03-08T14:00:00Z", "2025-03-08T22:00:00Z"),
        ("2025-03-09T13:00:00Z", "2025-03-09T21:00:00Z"),
        ("2025-03-10T13:00:00Z", "2025-03-10T21:00:00Z"),
    ]


def test_ac22_dst_gap_start_uses_pre_transition_offset():
    """AC-22 / FR-12: 02:30 does not exist on 2025-03-09; it maps with the EST offset (07:30Z)."""
    data = request(
        [participant(tz="America/New_York", start="02:30", end="04:00")],
        start="2025-03-09T00:00:00Z",
        end="2025-03-10T00:00:00Z",
    )
    assert slots_of(data) == [("2025-03-09T07:30:00Z", "2025-03-09T08:00:00Z")]


def test_ac22_dst_gap_negative_day_contributes_nothing():
    """AC-22 / FR-12: 02:30-03:00 maps to 07:30Z-07:00Z (negative), so the day has no slot."""
    data = request(
        [participant(tz="America/New_York", start="02:30", end="03:00")],
        start="2025-03-09T00:00:00Z",
        end="2025-03-10T00:00:00Z",
        duration=1,
    )
    assert slots_of(data) == []


def test_ac23_dst_overlap_start_takes_first_occurrence():
    """AC-23 / FR-12: 01:30 occurs twice on 2025-11-02; fold=0 takes EDT (05:30Z)."""
    data = request(
        [participant(tz="America/New_York", start="01:30", end="03:00")],
        start="2025-11-02T00:00:00Z",
        end="2025-11-03T00:00:00Z",
    )
    assert slots_of(data) == [("2025-11-02T05:30:00Z", "2025-11-02T08:00:00Z")]


def test_ac24_slot_spans_utc_midnight_and_window_edges_clip():
    """AC-24 / FR-16: Tokyo 06:00-10:00 gives an unsplit slot over UTC midnight."""
    data = request(
        [participant(tz="Asia/Tokyo", start="06:00", end="10:00")],
        start="2025-01-06T00:00:00Z",
        end="2025-01-08T00:00:00Z",
    )
    assert slots_of(data) == [
        ("2025-01-06T00:00:00Z", "2025-01-06T01:00:00Z"),
        ("2025-01-06T21:00:00Z", "2025-01-07T01:00:00Z"),
        ("2025-01-07T21:00:00Z", "2025-01-08T00:00:00Z"),
    ]


def test_ac25_slots_never_leave_the_window():
    """AC-25 / FR-15: a window narrower than the working day clips the slot."""
    data = request(start=at("12:00"), end=at("14:00"))
    assert slots_of(data) == [(at("12:00"), at("14:00"))]


def test_ac26_offsets_are_normalised_to_utc():
    """AC-26 / FR-04, FR-17: +05:30, -08:00 and Z inputs normalise; output ends in Z."""
    data = request(
        [participant(busy=[busy("2025-01-06T15:30:00+05:30", "2025-01-06T11:00:00Z")])],
        start="2025-01-06T05:30:00+05:30",
        end="2025-01-06T16:00:00-08:00",
    )
    assert slots_of(data) == [(at("09:00"), at("10:00")), (at("11:00"), at("17:00"))]


@pytest.mark.parametrize(
    ("tz", "expected_start", "expected_end"),
    [
        ("Asia/Kolkata", "2025-01-06T03:30:00Z", "2025-01-06T11:30:00Z"),
        ("Australia/Sydney", "2025-01-05T22:00:00Z", "2025-01-06T06:00:00Z"),
    ],
)
def test_fr12_fractional_and_far_offsets_apply_to_working_hours(tz, expected_start, expected_end):
    """FR-12: a +05:30 zone and a zone whose local day begins before the window both work."""
    data = request(
        [participant(tz=tz)],
        start="2025-01-05T00:00:00Z",
        end="2025-01-07T00:00:00Z",
    )
    assert (expected_start, expected_end) in slots_of(data)


def test_fr15_slot_must_be_inside_every_participants_hours_and_outside_every_busy():
    """FR-15: three participants; each one's busy time and hours restrict the result."""
    data = request(
        [
            participant("a", start="08:00", end="18:00", busy=[busy(at("09:00"), at("10:00"))]),
            participant("b", start="09:00", end="17:00", busy=[busy(at("12:00"), at("13:00"))]),
            participant("c", start="10:00", end="16:00"),
        ]
    )
    assert slots_of(data) == [(at("10:00"), at("12:00")), (at("13:00"), at("16:00"))]

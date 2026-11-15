"""Hypothesis property tests (FR-14, FR-15, FR-16, FR-20, AC-25, AC-29).

All generated instants are minute-aligned so a brute-force per-minute oracle is exact.
"""

from datetime import UTC, date, datetime, timedelta
from functools import lru_cache
from typing import Any
from zoneinfo import ZoneInfo

from hypothesis import given
from hypothesis import strategies as st
from support import busy, participant, request

from slotfinder.core import find_slots
from slotfinder.output import format_utc, render_success
from slotfinder.parsing import parse_request

MINUTE = timedelta(minutes=1)
JAN_BASE = datetime(2025, 1, 6, tzinfo=UTC)
# Zones whose UTC offset does not change between 2025-01-05 and 2025-01-20.
STABLE_ZONES = [
    "UTC",
    "America/New_York",
    "Europe/London",
    "Asia/Kolkata",
    "Asia/Tokyo",
    "Australia/Sydney",
]
# Zones that cross a DST transition near the transition dates used below.
DST_ZONES = ["America/New_York", "Europe/London", "Australia/Sydney", "Asia/Tokyo", "UTC"]
DST_DATES = [date(2025, 3, 8), date(2025, 3, 29), date(2025, 4, 4), date(2025, 10, 25),
             date(2025, 10, 31), date(2025, 11, 1)]  # fmt: skip


def iso(moment: datetime) -> str:
    return format_utc(moment)


@st.composite
def scenarios(draw, zones, bases, max_window_minutes, max_participants):
    """Draw a request dict plus the raw numbers needed by the oracle."""
    base = draw(bases)
    window_offset = draw(st.integers(0, 1440))
    window_length = draw(st.integers(1, max_window_minutes))
    window_start = base + window_offset * MINUTE
    window_end = window_start + window_length * MINUTE
    count = draw(st.integers(1, max_participants))
    people: list[dict[str, Any]] = []
    for index in range(count):
        tz = draw(st.sampled_from(zones))
        first = draw(st.integers(0, 1438))
        last = draw(st.integers(first + 1, 1439))
        intervals = []
        for _ in range(draw(st.integers(0, 5))):
            start = base + draw(st.integers(-720, 4000)) * MINUTE
            length = draw(st.integers(1, 900))
            intervals.append(busy(iso(start), iso(start + length * MINUTE)))
        opens = f"{first // 60:02d}:{first % 60:02d}"
        closes = f"{last // 60:02d}:{last % 60:02d}"
        people.append(participant(f"p{index}", tz, opens, closes, intervals))
    duration = draw(st.integers(1, 600))
    return request(people, iso(window_start), iso(window_end), duration)


jan_scenarios = scenarios(
    STABLE_ZONES, st.just(JAN_BASE), max_window_minutes=2 * 1440, max_participants=3
)
dst_scenarios = scenarios(
    DST_ZONES,
    st.sampled_from(DST_DATES).map(lambda d: datetime(d.year, d.month, d.day, tzinfo=UTC)),
    max_window_minutes=3 * 1440,
    max_participants=4,
)


def parsed_slots(data):
    return find_slots(parse_request(data))


@lru_cache(maxsize=None)
def local_minutes(zone: str, count: int = 7000) -> tuple[int, ...]:
    """Local minute-of-day for each minute after JAN_BASE (valid: no DST change in range)."""
    tz = ZoneInfo(zone)
    out = []
    for index in range(count):
        local = (JAN_BASE + index * MINUTE).astimezone(tz)
        out.append(local.hour * 60 + local.minute)
    return tuple(out)


def minutes_between(moment: datetime) -> int:
    return int((moment - JAN_BASE) / MINUTE)


def brute_force(data) -> list[tuple[datetime, datetime]]:
    """Independent per-minute oracle for windows without DST transitions."""
    request_obj = parse_request(data)
    first = minutes_between(request_obj.window[0])
    last = minutes_between(request_obj.window[1])
    free = []
    for minute in range(first, last):
        ok = True
        for person in request_obj.participants:
            hours = person.working_hours
            lo = hours.start.hour * 60 + hours.start.minute
            hi = hours.end.hour * 60 + hours.end.minute
            local = local_minutes(str(person.tz))[minute]
            instant = JAN_BASE + minute * MINUTE
            if not lo <= local < hi or any(s <= instant < e for s, e in person.busy):
                ok = False
                break
        free.append(ok)
    slots = []
    run_start = None
    for offset, flag in enumerate(free + [False]):
        if flag and run_start is None:
            run_start = offset
        elif not flag and run_start is not None:
            slots.append((first + run_start, first + offset))
            run_start = None
    need = request_obj.min_duration / MINUTE
    return [
        (JAN_BASE + a * MINUTE, JAN_BASE + b * MINUTE) for a, b in slots if (b - a) >= need
    ]


@given(jan_scenarios)
def test_fr16_result_equals_brute_force_minute_oracle(data):
    """FR-14, FR-15, FR-16 / AC-25: slots equal the per-minute oracle on non-DST windows."""
    assert parsed_slots(data) == brute_force(data)


@given(jan_scenarios | dst_scenarios)
def test_fr14_no_slot_overlaps_any_busy_interval(data):
    """FR-14 / FR-15: no returned slot intersects any participant's busy interval."""
    request_obj = parse_request(data)
    for start, end in find_slots(request_obj):
        for person in request_obj.participants:
            for busy_start, busy_end in person.busy:
                assert not (start < busy_end and busy_start < end)


@given(jan_scenarios | dst_scenarios)
def test_fr16_slots_sorted_disjoint_non_touching_long_enough_and_inside_window(data):
    """FR-16 / AC-25: ordering, maximality, minimum length and window containment."""
    request_obj = parse_request(data)
    slots = find_slots(request_obj)
    for start, end in slots:
        assert start < end
        assert end - start >= request_obj.min_duration
        assert request_obj.window[0] <= start
        assert end <= request_obj.window[1]
    for (_, previous_end), (next_start, _) in zip(slots, slots[1:], strict=False):
        assert previous_end < next_start


@given(jan_scenarios | dst_scenarios)
def test_fr15_every_slot_lies_inside_each_participants_working_day(data):
    """FR-15 / FR-12: each slot fits wholly inside one local working-hours range per person."""
    request_obj = parse_request(data)
    for start, end in find_slots(request_obj):
        for person in request_obj.participants:
            tz = person.tz
            local_day = start.astimezone(tz).date()
            inside = False
            for delta in (-1, 0, 1):
                day = local_day + timedelta(days=delta)
                day_start = datetime.combine(day, person.working_hours.start, tzinfo=tz)
                day_end = datetime.combine(day, person.working_hours.end, tzinfo=tz)
                if day_start <= start and end <= day_end:
                    inside = True
            assert inside


@given(st.data())
def test_fr20_result_is_invariant_under_permutation_of_participants_and_busy(draw):
    """FR-20 / AC-29: reordering participants and busy intervals changes nothing."""
    data = draw.draw(jan_scenarios | dst_scenarios)
    shuffled = {**data}
    people = []
    for person in data["participants"]:
        order = draw.draw(st.permutations(person["busy"]))
        people.append({**person, "busy": list(order)})
    shuffled["participants"] = list(draw.draw(st.permutations(people)))
    original = render_success(parsed_slots(data))
    assert render_success(parsed_slots(shuffled)) == original

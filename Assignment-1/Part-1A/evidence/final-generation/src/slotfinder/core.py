"""Slot computation (FR-12, FR-14, FR-15, FR-16). Pure: no I/O, clock or randomness."""

from datetime import UTC, datetime, timedelta
from functools import reduce

from slotfinder.intervals import Interval, clip, intersect, merge, subtract
from slotfinder.model import Participant, Request


def working_intervals(participant: Participant, window: Interval) -> list[Interval]:
    """UTC working ranges of one participant, clipped to the window and merged.

    Wall-clock times are converted with ''fold=0'' (PEP 495), endpoint by endpoint; a day whose
    converted range is empty or negative contributes nothing (FR-12).
    """
    tz = participant.tz
    hours = participant.working_hours
    first = window[0].astimezone(tz).date() - timedelta(days=1)
    last = window[1].astimezone(tz).date() + timedelta(days=1)
    ranges: list[Interval] = []
    day = first
    while day <= last:
        start = datetime.combine(day, hours.start, tzinfo=tz).astimezone(UTC)
        end = datetime.combine(day, hours.end, tzinfo=tz).astimezone(UTC)
        ranges.append((start, end))
        day += timedelta(days=1)
    return merge(clip(ranges, window[0], window[1]))


def free_intervals(participant: Participant, window: Interval) -> list[Interval]:
    """Working time of one participant minus their busy time (FR-14)."""
    busy = merge(clip(list(participant.busy), window[0], window[1]))
    return subtract(working_intervals(participant, window), busy)


def find_slots(request: Request) -> list[Interval]:
    """Maximal common free slots, sorted, each at least the minimum duration (FR-15, FR-16)."""
    per_participant = [free_intervals(p, request.window) for p in request.participants]
    common = reduce(intersect, per_participant)
    return [slot for slot in common if slot[1] - slot[0] >= request.min_duration]

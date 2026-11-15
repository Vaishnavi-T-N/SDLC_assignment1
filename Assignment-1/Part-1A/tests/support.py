"""Request builders shared by the tests."""

import copy
from typing import Any

from slotfinder.core import find_slots
from slotfinder.errors import SlotFinderError
from slotfinder.output import format_utc
from slotfinder.parsing import parse_request

DAY_START = "2025-01-06T00:00:00Z"
DAY_END = "2025-01-07T00:00:00Z"


def participant(
    pid: str = "p",
    tz: str = "UTC",
    start: str = "09:00",
    end: str = "17:00",
    busy: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Build one participant object."""
    return {
        "id": pid,
        "timezone": tz,
        "working_hours": {"start": start, "end": end},
        "busy": busy if busy is not None else [],
    }


def request(
    participants: list[dict[str, Any]] | None = None,
    start: Any = DAY_START,
    end: Any = DAY_END,
    duration: Any = 30,
) -> dict[str, Any]:
    """Build a request object (defaults: one UTC participant, 2025-01-06 whole day)."""
    return {
        "window": {"start": start, "end": end},
        "min_duration_minutes": duration,
        "participants": participants if participants is not None else [participant()],
    }


def busy(start: str, end: str) -> dict[str, str]:
    """Build one busy interval."""
    return {"start": start, "end": end}


def slots_of(data: dict[str, Any]) -> list[tuple[str, str]]:
    """Run the pure pipeline and return slots as formatted string pairs."""
    result = find_slots(parse_request(data))
    return [(format_utc(s), format_utc(e)) for s, e in result]


def code_of(data: Any) -> str:
    """Return the error code raised for ``data`` (fails the test if none is raised)."""
    try:
        parse_request(copy.deepcopy(data))
    except SlotFinderError as error:
        return str(error.code)
    raise AssertionError("expected a SlotFinderError, none was raised")

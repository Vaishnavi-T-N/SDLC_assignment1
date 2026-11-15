"""Immutable validated request model (see data-model.md)."""

from dataclasses import dataclass
from datetime import time, timedelta
from zoneinfo import ZoneInfo

from slotfinder.intervals import Interval


@dataclass(frozen=True)
class WorkingHours:
    """Local wall-clock range within one day, ''start < end''."""

    start: time
    end: time


@dataclass(frozen=True)
class Participant:
    """One attendee."""

    id: str
    tz: ZoneInfo
    working_hours: WorkingHours
    busy: tuple[Interval, ...]


@dataclass(frozen=True)
class Request:
    """A validated search request."""

    window: Interval
    min_duration: timedelta
    participants: tuple[Participant, ...]

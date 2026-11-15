"""Validate an untrusted request object into a ``Request`` (FR-03 to FR-13, FR-19, FR-22).

Faults are reported in the order given by FR-19. This module performs no I/O.
"""

import re
from datetime import UTC, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from slotfinder.errors import ErrorCode, SlotFinderError
from slotfinder.intervals import Interval
from slotfinder.model import Participant, Request, WorkingHours

MAX_PARTICIPANTS = 20
MIN_DURATION_MINUTES = 1
MAX_DURATION_MINUTES = 1440
MIN_YEAR = 1901
MAX_YEAR = 2999

_TZ_KEY = re.compile(r"[A-Za-z0-9_+\-/]{1,64}")
_HHMM = re.compile(r"([01][0-9]|2[0-3]):([0-5][0-9])")


def _fail(code: ErrorCode, message: str) -> SlotFinderError:
    return SlotFinderError(code, message)


def _require(obj: dict[str, Any], key: str, where: str) -> Any:
    if key not in obj:
        raise _fail(ErrorCode.MISSING_FIELD, f"missing required field '{key}' in {where}")
    return obj[key]


def _require_object(value: Any, where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise _fail(ErrorCode.MISSING_FIELD, f"{where} must be a JSON object")
    return value


def parse_datetime(value: Any, bad_code: ErrorCode, where: str) -> datetime:
    """Parse an ISO-8601 string with offset into an aware UTC datetime (FR-04)."""
    if not isinstance(value, str):
        raise _fail(bad_code, f"{where} must be an ISO-8601 string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        raise _fail(bad_code, f"{where} is not a valid ISO-8601 datetime") from None
    if parsed.utcoffset() is None:
        raise _fail(ErrorCode.NAIVE_DATETIME, f"{where} has no UTC offset")
    if parsed.microsecond != 0:
        raise _fail(bad_code, f"{where} must not have fractional seconds")
    try:
        utc = parsed.astimezone(UTC)
    except OverflowError:
        raise _fail(bad_code, f"{where} is out of the supported range") from None
    if not MIN_YEAR <= utc.year <= MAX_YEAR:
        raise _fail(bad_code, f"{where} is out of the supported range")
    return utc


def _parse_duration(value: Any) -> timedelta:
    if type(value) is not int or not MIN_DURATION_MINUTES <= value <= MAX_DURATION_MINUTES:
        raise _fail(
            ErrorCode.INVALID_DURATION,
            "min_duration_minutes must be an integer from 1 to 1440",
        )
    return timedelta(minutes=value)


def _parse_window(window: dict[str, Any]) -> Interval:
    start = parse_datetime(window["start"], ErrorCode.INVALID_WINDOW, "window.start")
    end = parse_datetime(window["end"], ErrorCode.INVALID_WINDOW, "window.end")
    if end <= start:
        raise _fail(ErrorCode.INVALID_WINDOW, "window.end must be after window.start")
    return (start, end)


def _parse_timezone(value: Any, where: str) -> ZoneInfo:
    if (
        not isinstance(value, str)
        or _TZ_KEY.fullmatch(value) is None
        or "" in value.split("/")
    ):
        raise _fail(ErrorCode.INVALID_TIMEZONE, f"{where} is not a valid IANA time zone")
    try:
        return ZoneInfo(value)
    except (KeyError, ValueError, OSError):
        raise _fail(ErrorCode.INVALID_TIMEZONE, f"{where} is not a known time zone") from None


def _parse_hhmm(value: Any, where: str) -> time:
    match = _HHMM.fullmatch(value) if isinstance(value, str) else None
    if match is None:
        raise _fail(ErrorCode.INVALID_WORKING_HOURS, f"{where} must be HH:MM (00:00-23:59)")
    return time(int(match.group(1)), int(match.group(2)))


def _parse_working_hours(raw: dict[str, Any], where: str) -> WorkingHours:
    start = _parse_hhmm(raw["start"], f"{where}.start")
    end = _parse_hhmm(raw["end"], f"{where}.end")
    if end <= start:
        raise _fail(
            ErrorCode.INVALID_WORKING_HOURS,
            f"{where}.end must be after {where}.start (overnight hours are not supported)",
        )
    return WorkingHours(start, end)


def _parse_busy(items: list[Any], where: str) -> tuple[Interval, ...]:
    busy: list[Interval] = []
    for index, item in enumerate(items):
        label = f"{where}[{index}]"
        entry = _require_object(item, label)
        raw_start = _require(entry, "start", label)
        raw_end = _require(entry, "end", label)
        start = parse_datetime(raw_start, ErrorCode.INVALID_INTERVAL, f"{label}.start")
        end = parse_datetime(raw_end, ErrorCode.INVALID_INTERVAL, f"{label}.end")
        if end <= start:
            raise _fail(ErrorCode.INVALID_INTERVAL, f"{label}.end must be after {label}.start")
        busy.append((start, end))
    return tuple(busy)


def _parse_participant(raw: Any, index: int) -> Participant:
    where = f"participants[{index}]"
    obj = _require_object(raw, where)
    pid = _require(obj, "id", where)
    raw_tz = _require(obj, "timezone", where)
    raw_hours = _require_object(_require(obj, "working_hours", where), f"{where}.working_hours")
    _require(raw_hours, "start", f"{where}.working_hours")
    _require(raw_hours, "end", f"{where}.working_hours")
    raw_busy = _require(obj, "busy", where)
    if not isinstance(pid, str) or not pid:
        raise _fail(ErrorCode.MISSING_FIELD, f"{where}.id must be a non-empty string")
    if not isinstance(raw_busy, list):
        raise _fail(ErrorCode.MISSING_FIELD, f"{where}.busy must be a list")
    tz = _parse_timezone(raw_tz, f"{where}.timezone")
    hours = _parse_working_hours(raw_hours, f"{where}.working_hours")
    busy = _parse_busy(raw_busy, f"{where}.busy")
    return Participant(id=pid, tz=tz, working_hours=hours, busy=busy)


def parse_request(data: Any) -> Request:
    """Validate ``data`` (the decoded JSON value) and return a ``Request``."""
    if not isinstance(data, dict):
        raise _fail(ErrorCode.INVALID_JSON, "top-level JSON value must be an object")
    raw_window = _require(data, "window", "request")
    raw_duration = _require(data, "min_duration_minutes", "request")
    raw_participants = _require(data, "participants", "request")
    window_obj = _require_object(raw_window, "window")
    _require(window_obj, "start", "window")
    _require(window_obj, "end", "window")
    if not isinstance(raw_participants, list):
        raise _fail(ErrorCode.MISSING_FIELD, "participants must be a list")

    duration = _parse_duration(raw_duration)
    window = _parse_window(window_obj)

    if len(raw_participants) == 0:
        raise _fail(ErrorCode.MISSING_FIELD, "participants must not be empty")
    if len(raw_participants) > MAX_PARTICIPANTS:
        raise _fail(
            ErrorCode.TOO_MANY_PARTICIPANTS,
            f"at most {MAX_PARTICIPANTS} participants are allowed",
        )
    participants = tuple(_parse_participant(p, i) for i, p in enumerate(raw_participants))
    return Request(window=window, min_duration=duration, participants=participants)

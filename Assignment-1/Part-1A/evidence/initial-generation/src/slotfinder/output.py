"""Canonical JSON rendering (FR-17, FR-18, FR-20). Pure: returns text, performs no I/O."""

import json
from datetime import datetime
from typing import Any

from slotfinder.errors import ErrorCode
from slotfinder.intervals import Interval


def format_utc(moment: datetime) -> str:
    """Format a UTC datetime as ''YYYY-MM-DDTHH:MM:SSZ''."""
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def _canonical(document: dict[str, Any]) -> str:
    return json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n"


def render_success(slots: list[Interval]) -> str:
    """Render the success document."""
    return _canonical(
        {"slots": [{"start": format_utc(start), "end": format_utc(end)} for start, end in slots]}
    )


def render_error(code: ErrorCode, message: str) -> str:
    """Render the error document."""
    return _canonical({"error": {"code": str(code), "message": message}})

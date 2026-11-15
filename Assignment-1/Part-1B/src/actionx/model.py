"""Request model, prompt message construction and canned outputs (pure, no I/O)."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from typing import Any

MAX_NOTES_CHARS = 60_000
_ISO_SHAPE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
_NOTES_TAG = re.compile(r"</?\s*notes\s*>", re.IGNORECASE)

EMPTY_QUESTION = "The notes are empty. Please provide the meeting notes to analyse."
TOO_LONG_QUESTION = (
    "The notes are longer than the supported limit. Please split them into smaller parts."
)
FALLBACK_QUESTION = (
    "The extractor could not produce a reliable result. Please resubmit or rephrase the notes."
)
GENERIC_QUESTION = "Please clarify the missing details in the notes."
GENERIC_TEXT_REPLACEMENT = (
    "This text was removed because it contained a link not present in the notes."
)
LEAK_REFUSAL_REASON = "Output withheld: possible disclosure of internal instructions"
GENERIC_REFUSAL_REASON = "The request was refused."


class InputError(ValueError):
    """The request violates the input contract (FR-01, FR-02)."""


class ParseError(ValueError):
    """The model text contains no parseable JSON object (FR-07)."""


@dataclass(frozen=True)
class ExtractionRequest:
    notes: str
    meeting_date: date
    attendees: tuple[str, ...] = ()


def parse_request(data: Mapping[str, Any]) -> ExtractionRequest:
    """Validate a request mapping and build an 'ExtractionRequest'."""
    if not isinstance(data, Mapping):
        raise InputError("request must be a JSON object")
    notes = data.get("notes")
    if not isinstance(notes, str):
        raise InputError("notes must be a string")
    raw_date = data.get("meeting_date")
    if not isinstance(raw_date, str) or not _ISO_SHAPE.fullmatch(raw_date):
        raise InputError("meeting_date must be an ISO date YYYY-MM-DD")
    try:
        meeting_date = date.fromisoformat(raw_date)
    except ValueError as error:
        raise InputError(f"meeting_date is not a real calendar date: {raw_date}") from error
    attendees = data.get("attendees", [])
    if not isinstance(attendees, list) or not all(isinstance(a, str) for a in attendees):
        raise InputError("attendees must be a list of strings")
    return ExtractionRequest(notes=notes, meeting_date=meeting_date, attendees=tuple(attendees))


def build_user_message(request: ExtractionRequest) -> str:
    """Build the user message; notes sit between <notes> tags, inner tags are neutralised."""
    safe_notes = _NOTES_TAG.sub(lambda m: m.group(0).replace("<", "&lt;"), request.notes)
    attendees = json.dumps(list(request.attendees), ensure_ascii=False)
    weekday = request.meeting_date.strftime("%A")
    return (
        f"Meeting date: {request.meeting_date.isoformat()} ({weekday})\n"
        f"Attendees: {attendees}\n"
        f"<notes>\n{safe_notes}\n</notes>"
    )


def clarification_output(question: str) -> dict[str, Any]:
    return {
        "action_items": [],
        "needs_clarification": True,
        "clarification_question": question,
        "refusal": False,
        "refusal_reason": None,
    }


def refusal_output(reason: str) -> dict[str, Any]:
    return {
        "action_items": [],
        "needs_clarification": False,
        "clarification_question": None,
        "refusal": True,
        "refusal_reason": reason,
    }


def fallback_output() -> dict[str, Any]:
    return clarification_output(FALLBACK_QUESTION)

"""Shared helpers for the tests (no network; model calls go through FakeModelClient)."""

from __future__ import annotations

import copy
import json
from datetime import date
from pathlib import Path
from typing import Any

from actionx.client import FakeModelClient
from actionx.config import Config
from actionx.extractor import Extractor, load_schema, load_system_prompt
from actionx.model import ExtractionRequest

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "specs" / "001-action-extractor" / "spec.md"
SYSTEM_PROMPT = load_system_prompt()
SCHEMA = load_schema()
CONFIG = Config(model="test-model", temperature=0.0, seed=7, max_output_tokens=256)

NOTES = "Bob Rivera will send the report by Friday."


def req(
    notes: str = NOTES, meeting: str = "2026-03-11", attendees: tuple[str, ...] = ("Bob Rivera",)
) -> ExtractionRequest:
    return ExtractionRequest(
        notes=notes, meeting_date=date.fromisoformat(meeting), attendees=attendees
    )


def good_item(**changes: Any) -> dict[str, Any]:
    item: dict[str, Any] = {
        "task": "send the report",
        "owner": "Bob Rivera",
        "due_date": "2026-03-13",
        "confidence": 0.9,
        "evidence": NOTES,
    }
    item.update(changes)
    return item


def good_output(items: list[dict[str, Any]] | None = None, **changes: Any) -> dict[str, Any]:
    output: dict[str, Any] = {
        "action_items": [good_item()] if items is None else items,
        "needs_clarification": False,
        "clarification_question": None,
        "refusal": False,
        "refusal_reason": None,
    }
    output.update(changes)
    return copy.deepcopy(output)


def ids(violations: list[Any]) -> list[str]:
    return [v.id for v in violations]


def make_extractor(
    responses: list[str | Exception], sleeps: list[float] | None = None
) -> tuple[Extractor, FakeModelClient]:
    client = FakeModelClient(responses)
    record = sleeps if sleeps is not None else []
    return Extractor(client, CONFIG, SYSTEM_PROMPT, SCHEMA, sleep=record.append), client


def dumps(value: Any) -> str:
    return json.dumps(value)

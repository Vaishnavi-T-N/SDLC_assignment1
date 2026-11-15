"""Deterministic post-validation guardrails GR-01..GR-08 (pure, no I/O)."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

from actionx.invariants import (
    item_key,
    leaks_prompt,
    output_strings,
    owner_in_context,
    parse_due,
    prompt_runs,
)
from actionx.model import (
    GENERIC_QUESTION,
    GENERIC_REFUSAL_REASON,
    GENERIC_TEXT_REPLACEMENT,
    LEAK_REFUSAL_REASON,
    ExtractionRequest,
    refusal_output,
)
from actionx.textnorm import normalize_ws, urls, words

DATE_CUE_WORDS = frozenset(
    (
        "today tomorrow tonight week weeks month months year years day days eod eow eom quarter "
        "weekend monday tuesday wednesday thursday friday saturday sunday "
        "january february march april may june july august september october november december "
        "jan feb mar apr jun jul aug sep sept oct nov dec "
        "hoy manana mañana lunes martes miercoles miércoles jueves viernes sabado sábado domingo "
        "semana mes año "
        "aujourd demain lundi mardi mercredi jeudi vendredi samedi dimanche semaine mois "
        "heute morgen montag dienstag mittwoch donnerstag freitag samstag sonntag woche monat jahr"
    ).split()
)


@dataclass(frozen=True)
class GuardrailAction:
    id: str
    detail: str


def has_date_cue(notes: str) -> bool:
    """True when the notes contain any temporal word or any digit (GR-05)."""
    if any(char.isdigit() for char in notes):
        return True
    return any(word in DATE_CUE_WORDS for word in words(notes))


def apply_guardrails(
    output: dict[str, Any], request: ExtractionRequest, system_prompt: str
) -> tuple[dict[str, Any], list[GuardrailAction]]:
    """Return a repaired copy of a schema-valid output and the actions taken."""
    result = copy.deepcopy(output)
    actions: list[GuardrailAction] = []
    runs = prompt_runs(system_prompt)

    if any(leaks_prompt(text, runs) for text in output_strings(result)):
        actions.append(GuardrailAction("GR-01", "output replaced by a refusal (prompt disclosure)"))
        return refusal_output(LEAK_REFUSAL_REASON), actions

    notes_urls = urls(request.notes)
    kept = []
    for index, item in enumerate(result["action_items"]):
        strings = [str(item.get(k) or "") for k in ("task", "owner", "due_date", "evidence")]
        if any(urls(text) - notes_urls for text in strings):
            actions.append(GuardrailAction("GR-02", f"item {index} dropped: novel URL"))
        else:
            kept.append(item)
    result["action_items"] = kept
    for key in ("clarification_question", "refusal_reason"):
        value = result.get(key)
        if isinstance(value, str) and urls(value) - notes_urls:
            result[key] = GENERIC_TEXT_REPLACEMENT
            actions.append(GuardrailAction("GR-02", f"{key} replaced: novel URL"))

    notes_norm = normalize_ws(request.notes)
    kept = []
    for index, item in enumerate(result["action_items"]):
        evidence = normalize_ws(str(item.get("evidence", "")))
        if not evidence or evidence not in notes_norm:
            actions.append(GuardrailAction("GR-03", f"item {index} dropped: evidence not a quote"))
        else:
            kept.append(item)
    result["action_items"] = kept

    for index, item in enumerate(result["action_items"]):
        owner = item.get("owner")
        if owner is not None and not owner_in_context(owner, request):
            item["owner"] = None
            actions.append(GuardrailAction("GR-04", f"item {index}: owner {owner!r} set to null"))

    cue = has_date_cue(request.notes)
    for index, item in enumerate(result["action_items"]):
        due = item.get("due_date")
        if due is None:
            continue
        parsed = parse_due(due)
        reason = None
        if parsed is None:
            reason = "not a real calendar date"
        elif parsed < request.meeting_date:
            reason = "before the meeting date"
        elif not cue:
            reason = "no date cue in the notes"
        if reason:
            item["due_date"] = None
            actions.append(GuardrailAction("GR-05", f"item {index}: due_date {due!r} nulled: {reason}"))

    seen: set[tuple[str, str, str]] = set()
    kept = []
    for index, item in enumerate(result["action_items"]):
        key = item_key(item)
        if key in seen:
            actions.append(GuardrailAction("GR-06", f"item {index} dropped: duplicate"))
        else:
            seen.add(key)
            kept.append(item)
    result["action_items"] = kept

    kept = []
    for index, item in enumerate(result["action_items"]):
        if not str(item.get("task", "")).strip():
            actions.append(GuardrailAction("GR-08", f"item {index} dropped: empty task"))
        else:
            kept.append(item)
    result["action_items"] = kept

    _enforce_consistency(result, actions)
    return result, actions


def _enforce_consistency(result: dict[str, Any], actions: list[GuardrailAction]) -> None:
    """GR-07."""
    if result["refusal"]:
        if result["action_items"]:
            result["action_items"] = []
            actions.append(GuardrailAction("GR-07", "items cleared because refusal is true"))
        reason = result.get("refusal_reason")
        if not (isinstance(reason, str) and reason.strip()):
            result["refusal_reason"] = GENERIC_REFUSAL_REASON
            actions.append(GuardrailAction("GR-07", "generic refusal_reason filled"))
    elif result.get("refusal_reason") is not None:
        result["refusal_reason"] = None
        actions.append(GuardrailAction("GR-07", "refusal_reason cleared because refusal is false"))

    if any(item.get("owner") is None for item in result["action_items"]) and not result[
        "needs_clarification"
    ]:
        result["needs_clarification"] = True
        actions.append(GuardrailAction("GR-07", "needs_clarification forced by an ownerless item"))
    question = result.get("clarification_question")
    has_question = isinstance(question, str) and bool(question.strip())
    if result["needs_clarification"] and not has_question:
        result["clarification_question"] = GENERIC_QUESTION
        actions.append(GuardrailAction("GR-07", "generic clarification_question filled"))
    elif not result["needs_clarification"] and question is not None:
        result["clarification_question"] = None
        actions.append(GuardrailAction("GR-07", "clarification_question cleared"))

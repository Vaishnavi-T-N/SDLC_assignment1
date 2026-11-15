"""AC-70, AC-71, AC-80..AC-87: the dataset is valid and carries the cases each property needs."""

from __future__ import annotations

import json
import re
from datetime import date, timedelta

from actionx.model import parse_request
from actionx.textnorm import normalize_ws
from support import ROOT, SPEC_PATH

DATASET = json.loads((ROOT / "evals" / "dataset.json").read_text(encoding="utf-8"))
CANNED = json.loads((ROOT / "tests" / "fixtures" / "canned_outputs.json").read_text(encoding="utf-8"))
BY_ID = {case["id"]: case for case in DATASET}
CATEGORIES = {"normal", "boundary", "ambiguous", "missing_info", "malformed", "adversarial"}
PROPERTY_KEYS = {"max_items", "all_owner_null", "all_due_null", "needs_clarification", "refusal",
                 "clarify_or_refuse", "forbidden_owners", "must_not_contain"}


def test_ac70_dataset_shape_and_coverage():
    assert len(DATASET) >= 18
    assert len(BY_ID) == len(DATASET)
    assert {case["category"] for case in DATASET} == CATEGORIES
    spec_ids = set(re.findall(r"\*\*((?:FR|INV|GR|BP|AC)-\d+)", SPEC_PATH.read_text(encoding="utf-8")))
    for case in DATASET:
        assert set(case) <= {"id", "category", "requirement_ids", "input", "expected_items", "properties"}
        assert case["requirement_ids"], case["id"]
        assert set(case["requirement_ids"]) <= spec_ids, case["id"]
        assert "expected_items" in case or "properties" in case, case["id"]
        assert set(case.get("properties", {})) <= PROPERTY_KEYS, case["id"]
        parse_request(case["input"])
        assert case["id"] in CANNED, case["id"]


def test_ac70_every_expected_item_has_evidence_quoted_from_its_notes():
    for case in DATASET:
        notes = normalize_ws(case["input"]["notes"])
        for item in case.get("expected_items", []):
            assert set(item) == {"task", "owner", "due_date", "evidence"}
            assert normalize_ws(item["evidence"]) in notes, case["id"]


def test_ac70_dataset_has_enough_scored_cases_and_cases_without_pii_markers():
    scored = [c for c in DATASET if c.get("expected_items")]
    assert len(scored) >= 12
    text = json.dumps(DATASET)
    assert not re.search(r"[\w.]+@[\w.]+\.\w+", text)  # no e-mail addresses
    assert not re.search(r"\b\d{3}[-. ]\d{3}[-. ]\d{4}\b", text)  # no phone numbers


# ------------------------------------------------------------------ AC-71: independent date maths


def weekday_after(start: date, weekday: int) -> date:
    delta = (weekday - start.weekday()) % 7 or 7
    return start + timedelta(days=delta)


def next_week_weekday(start: date, weekday: int) -> date:
    monday = start - timedelta(days=start.weekday())
    return monday + timedelta(days=7 + weekday)


def end_of_month(start: date) -> date:
    first_next = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
    return first_next - timedelta(days=1)


def next_occurrence(start: date, month: int, day: int) -> date:
    candidate = date(start.year, month, day)
    return candidate if candidate >= start else date(start.year + 1, month, day)


def due(case_id: str, index: int) -> str | None:
    return BY_ID[case_id]["expected_items"][index]["due_date"]


def meeting(case_id: str) -> date:
    return date.fromisoformat(BY_ID[case_id]["input"]["meeting_date"])


FRI, TUE = 4, 1


def test_ac71_relative_date_ground_truth_matches_independent_computation():
    multi = "normal-multiple-owners-relative-dates"
    assert due(multi, 0) == weekday_after(meeting(multi), FRI).isoformat()  # "by Friday"
    assert due(multi, 1) == (meeting(multi) + timedelta(days=1)).isoformat()  # "tomorrow"
    assert due(multi, 2) == next_week_weekday(meeting(multi), TUE).isoformat()  # "next Tuesday"
    speakers = "normal-speaker-labels-first-names"
    assert due(speakers, 0) == (meeting(speakers) + timedelta(days=1)).isoformat()
    assert due(speakers, 1) == (meeting(speakers) + timedelta(weeks=2)).isoformat()  # "in two weeks"
    plain = "normal-no-attendees-today-and-days"
    assert due(plain, 0) == meeting(plain).isoformat()  # "today"
    assert due(plain, 1) == (meeting(plain) + timedelta(days=3)).isoformat()  # "in 3 days"
    eom = "boundary-end-of-month"
    assert due(eom, 0) == end_of_month(meeting(eom)).isoformat() == "2026-02-28"
    roll = "boundary-year-rollover"
    assert due(roll, 0) == weekday_after(meeting(roll), FRI).isoformat() == "2027-01-01"
    assert due(roll, 1) == next_occurrence(meeting(roll), 1, 15).isoformat() == "2027-01-15"
    spanish = "boundary-non-english-notes"
    assert due(spanish, 0) == weekday_after(meeting(spanish), FRI).isoformat()  # "el viernes"
    assert due("ambiguous-vague-due-next-week", 0) is None
    assert due("boundary-due-date-in-the-past", 0) is None


def test_ac71_every_explicit_iso_date_in_ground_truth_is_after_the_meeting_or_null():
    for case in DATASET:
        for item in case.get("expected_items", []):
            if item["due_date"]:
                assert date.fromisoformat(item["due_date"]) >= meeting(case["id"]), case["id"]


# ------------------------------------------------------------------ behavioural properties


def test_ac80_owner_and_due_invention_are_probed():
    null_owner = [c for c in DATASET for i in c.get("expected_items", []) if i["owner"] is None]
    null_due = [c for c in DATASET for i in c.get("expected_items", []) if i["due_date"] is None]
    assert len(null_owner) >= 2 and len(null_due) >= 3
    assert BY_ID["ambiguous-name-mentioned-not-assigned"]["properties"]["all_owner_null"] is True


def test_ac81_relative_date_cases_cover_week_month_year_and_vague():
    ids = set(BY_ID)
    assert {"boundary-end-of-month", "boundary-year-rollover",
            "normal-multiple-owners-relative-dates", "ambiguous-vague-due-next-week"} <= ids


def test_ac82_ambiguous_and_missing_info_cases_exist_with_clarification_properties():
    assert BY_ID["ambiguous-someone-should"]["properties"]["clarify_or_refuse"] is True
    categories = [c["category"] for c in DATASET]
    assert categories.count("ambiguous") >= 3 and categories.count("missing_info") >= 3


def test_ac83_no_action_empty_and_gibberish_cases_forbid_items():
    for case_id in ("missing-no-actions-at-all", "malformed-empty-string", "malformed-gibberish",
                    "malformed-whitespace-only"):
        assert BY_ID[case_id]["properties"]["max_items"] == 0
    assert BY_ID["malformed-gibberish"]["properties"]["clarify_or_refuse"] is True
    assert BY_ID["malformed-empty-string"]["input"]["notes"] == ""


def test_ac84_two_injection_variants_one_with_fake_json_blob():
    ceo = BY_ID["adversarial-injection-assign-to-ceo"]
    assert "CEO" in ceo["properties"]["forbidden_owners"]
    leak = BY_ID["adversarial-injection-reveal-system-prompt"]
    assert "AX-CANARY" in leak["properties"]["must_not_contain"]
    assert "http://" in leak["input"]["notes"]
    assert '"action_items"' in BY_ID["malformed-fake-json-blob-in-notes"]["input"]["notes"]


def test_ac85_harmful_request_must_be_refused():
    assert BY_ID["adversarial-harmful-request"]["properties"]["refusal"] is True


def test_ac86_verdict_rule_is_declared_in_the_spec():
    text = SPEC_PATH.read_text(encoding="utf-8")
    assert "`INCONCLUSIVE` if any case is SERVICE_ERROR" in text
    assert "Layer 3 never overrides" in text


def test_ac87_duplicate_non_english_and_long_cases_exist():
    assert len(BY_ID["boundary-duplicate-mention"]["expected_items"]) == 1
    assert BY_ID["boundary-duplicate-mention"]["input"]["notes"].count("press release") == 2
    assert "enviará" in BY_ID["boundary-non-english-notes"]["input"]["notes"]
    assert len(BY_ID["boundary-very-long-notes"]["input"]["notes"]) > 5000

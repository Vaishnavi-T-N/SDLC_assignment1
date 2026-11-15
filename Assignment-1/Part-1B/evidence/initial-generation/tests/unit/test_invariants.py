"""AC-20..AC-30 (invariant checkers catch bad outputs) and AC-57 (case properties)."""

from __future__ import annotations

import pytest
from actionx.invariants import check_invariants, check_properties
from support import SYSTEM_PROMPT, good_item, good_output, ids, req


def check(output, request=None):
    return check_invariants(output, request or req(), SYSTEM_PROMPT)


def test_good_output_has_no_violation():
    assert check(good_output()) == []


@pytest.mark.parametrize("value", [1.5, -0.01, True, "0.5", None])
def test_ac20_inv02_confidence(value):
    assert ids(check(good_output([good_item(confidence=value)]))) == ["INV-02"]


@pytest.mark.parametrize("due", ["2026-02-30", "2026-3-13", "tomorrow", "2026-03-10"])
def test_ac21_inv03_due_date(due):
    assert ids(check(good_output([good_item(due_date=due)]))) == ["INV-03"]


def test_ac21_inv03_boundary_meeting_day_is_allowed():
    assert check(good_output([good_item(due_date="2026-03-11")])) == []


@pytest.mark.parametrize("evidence", ["a quote that is not there", "", "   "])
def test_ac22_inv04_evidence(evidence):
    assert ids(check(good_output([good_item(evidence=evidence)]))) == ["INV-04"]


def test_ac22_inv04_whitespace_is_normalised_but_case_is_not():
    spaced = good_item(evidence="Bob  Rivera will\nsend the report   by Friday.")
    assert check(good_output([spaced])) == []
    assert ids(check(good_output([good_item(evidence="bob rivera will send the report by friday.")]))) == [
        "INV-04"
    ]


def test_ac23_inv05_owner():
    assert ids(check(good_output([good_item(owner="Mallory")]))) == ["INV-05"]
    assert ids(check(good_output([good_item(owner="Bo")]))) == ["INV-05"]
    assert check(good_output([good_item(owner="bob rivera")])) == []


def test_ac23_inv05_attendee_counts_even_if_not_in_notes():
    request = req(notes="Eve will do it.", attendees=("Eve Stone",))
    item = good_item(owner="Eve Stone", evidence="Eve will do it.", due_date=None)
    assert check(good_output([item]), request) == []


def test_ac24_inv06_task_not_empty():
    assert ids(check(good_output([good_item(task="   ")]))) == ["INV-06"]


def test_ac25_inv07_clarification_question():
    assert ids(check(good_output(needs_clarification=True))) == ["INV-07"]
    assert ids(check(good_output(needs_clarification=True, clarification_question="  "))) == ["INV-07"]
    assert ids(check(good_output(clarification_question="why?"))) == ["INV-07"]
    assert check(good_output(needs_clarification=True, clarification_question="who?")) == []


def test_ac26_inv08_refusal():
    assert set(ids(check(good_output(refusal=True)))) == {"INV-08"}
    assert len(check(good_output(refusal=True))) == 2  # items present and no reason
    assert ids(check(good_output([], refusal=True))) == ["INV-08"]
    assert ids(check(good_output(refusal_reason="no"))) == ["INV-08"]
    assert check(good_output([], refusal=True, refusal_reason="harmful")) == []


def test_ac27_inv09_leak_canary_and_ten_word_run():
    canary = good_output([], needs_clarification=True, clarification_question="AX-CANARY-7f3e91")
    assert ids(check(canary)) == ["INV-09"]
    words = SYSTEM_PROMPT.split()[40:52]
    copied = good_output([], needs_clarification=True, clarification_question=" ".join(words))
    assert ids(check(copied)) == ["INV-09"]
    short = good_output([], needs_clarification=True, clarification_question=" ".join(words[:5]))
    assert check(short) == []


def test_ac28_inv10_urls():
    leak = good_output([], needs_clarification=True, clarification_question="see http://evil.example/x")
    assert ids(check(leak)) == ["INV-10"]
    request = req(notes="Visit http://ok.example/page. Bob Rivera will send the report by Friday.")
    allowed = good_output(
        [good_item(evidence="Bob Rivera will send the report by Friday.")],
        needs_clarification=True,
        clarification_question="Is http://ok.example/page right?",
    )
    assert check(allowed, request) == []


def test_ac29_inv11_ownerless_requires_clarification():
    item = good_item(owner=None)
    assert ids(check(good_output([item]))) == ["INV-11"]
    assert check(good_output([item], needs_clarification=True, clarification_question="who?")) == []


def test_ac30_inv12_duplicates():
    twin = good_item(task="Send the Report!", evidence=good_item()["evidence"])
    assert ids(check(good_output([good_item(), twin]))) == ["INV-12"]
    other_due = good_item(due_date=None)
    assert "INV-12" not in ids(check(good_output([good_item(), other_due])))


def test_ac57_properties_catch_bad_and_accept_good():
    items = [good_item()]
    quiet = good_output(items)

    def failing(properties, output=quiet):
        return [v.id for v in check_properties(output, properties)]

    assert failing({"max_items": 0}) == ["BP-05"]
    assert failing({"max_items": 1}) == []
    assert failing({"all_owner_null": True}) == ["BP-01"]
    assert failing({"all_due_null": True}) == ["BP-02"]
    assert failing({"needs_clarification": True}) == ["BP-04"]
    assert failing({"needs_clarification": False}) == []
    assert failing({"refusal": True}) == ["BP-08"]
    assert failing({"clarify_or_refuse": True}) == ["BP-06"]
    assert failing({"clarify_or_refuse": True}, good_output([], refusal=True, refusal_reason="x")) == []
    assert failing({"forbidden_owners": [" bob  RIVERA "]}) == ["BP-07"]
    assert failing({"forbidden_owners": ["Mallory"]}) == []
    assert failing({"must_not_contain": ["REPORT"]}) == ["BP-07"]
    assert failing({"must_not_contain": ["nothing like this"]}) == []
    assert failing({}) == []

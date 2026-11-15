"""AC-50..AC-56: deterministic matching, scores and the verdict rule."""

from __future__ import annotations

import json
import re

import pytest
from actionx.scoring import (
    THRESHOLDS,
    aggregate,
    match_items,
    score_case,
    similarity,
    verdict,
)
from support import SPEC_PATH


def it(task, owner=None, due=None):
    return {"task": task, "owner": owner, "due_date": due}


def test_similarity_is_max_of_jaccard_and_difflib():
    assert similarity("send the budget draft", "Send budget draft!") == 1.0
    assert similarity("book venue", "paint the fence") < 0.5
    assert similarity("", "") == 1.0  # identical empty strings: difflib ratio is 1
    assert similarity("!!!", "???") == 0.0


def test_ac50_matching_is_greedy_one_to_one_with_deterministic_ties():
    expected = [it("send the report")]
    predicted = [it("send the report"), it("send the report")]
    assert match_items(predicted, expected) == [(0, 0, 1.0)]  # tie -> lowest predicted index
    two_expected = [it("write release notes"), it("write release notes draft")]
    predicted = [it("write release notes draft")]
    # best similarity wins, a predicted item matches at most one expected item
    assert match_items(predicted, two_expected) == [(0, 1, 1.0)]
    assert match_items([it("completely unrelated words")], expected) == []


def test_ac50_below_cutoff_does_not_match():
    assert match_items([it("alpha beta gamma delta")], [it("alpha omega sigma tau")]) == []


def test_ac51_f1_precision_recall_hand_computed():
    case_a = score_case(
        [it("send report"), it("book venue"), it("extra thing entirely")],
        [it("send report"), it("book venue"), it("fix bug in login")],
    )
    assert (case_a["tp"], case_a["fp"], case_a["fn"]) == (2, 1, 1)
    case_b = score_case([it("update roadmap")], [it("update roadmap")])
    totals = aggregate([case_a, case_b])
    assert (totals["tp"], totals["fp"], totals["fn"]) == (3, 1, 1)
    assert totals["precision"] == pytest.approx(0.75)
    assert totals["recall"] == pytest.approx(0.75)
    assert totals["f1"] == pytest.approx(0.75)


def test_ac51_zero_everything_gives_zero_not_error():
    totals = aggregate([score_case([], [])])
    assert totals["f1"] == 0.0
    assert totals["owner_accuracy"] == 0.0
    assert totals["due_accuracy"] == 0.0
    assert aggregate([])["f1"] == 0.0


def test_ac52_owner_and_due_accuracy_null_equals_only_null():
    expected = [it("send report", "Bob Rivera", "2026-03-13"), it("book venue", None, None),
                it("fix login bug", "Eve Stone", None)]
    predicted = [it("send report", " bob  rivera ", "2026-03-13"), it("book venue", "Zed", "2026-03-20"),
                 it("fix login bug", None, None)]
    scored = score_case(predicted, expected)
    assert scored["owner_correct"] == 1
    assert scored["due_correct"] == 2
    totals = aggregate([scored])
    assert totals["owner_accuracy"] == pytest.approx(1 / 3)
    assert totals["due_accuracy"] == pytest.approx(2 / 3)


def test_ac53_fabrication_counts_invented_owner_and_due():
    scored = score_case([it("book venue", "Zed", "2026-03-20")], [it("book venue", None, None)])
    assert scored["fabrication"] == 2
    assert [m["invented_owner"] for m in scored["matches"]] == [True]
    clean = score_case([it("book venue", None, None)], [it("book venue", None, None)])
    assert clean["fabrication"] == 0
    wrong_not_invented = score_case([it("book venue", "Zed", "2026-03-20")], [it("book venue", "Amy", "2026-03-21")])
    assert wrong_not_invented["fabrication"] == 0


PERFECT = {"f1": 1.0, "owner_accuracy": 1.0, "due_accuracy": 1.0, "fabrication": 0}


def test_ac54_verdict_pass_fail_inconclusive():
    assert verdict(0, 1.0, PERFECT)[0] == "PASS"
    assert verdict(1, 1.0, PERFECT)[0] == "INCONCLUSIVE"
    assert verdict(3, 0.0, {**PERFECT, "f1": 0.0})[0] == "INCONCLUSIVE"
    for change in (
        {"f1": 0.79},
        {"owner_accuracy": 0.84},
        {"due_accuracy": 0.84},
        {"fabrication": 1},
    ):
        outcome, gates = verdict(0, 1.0, {**PERFECT, **change})
        assert outcome == "FAIL"
        assert list(gates.values()).count(False) == 1
    assert verdict(0, 0.95, PERFECT) [0] == "FAIL"
    assert verdict(0, 1.0, {**PERFECT, "f1": 0.80})[0] == "PASS"


def test_ac55_service_errors_are_not_part_of_any_denominator():
    # aggregate only sees the per-case scores that the harness passes it: a SERVICE_ERROR case has none
    only_scored = aggregate([score_case([it("send report")], [it("send report")])])
    assert only_scored["f1"] == 1.0


def test_ac56_thresholds_equal_the_spec_block():
    text = SPEC_PATH.read_text(encoding="utf-8")
    block = re.search(r"```json evaluation-thresholds\n(.*?)\n```", text, re.DOTALL)
    assert block is not None
    assert json.loads(block.group(1)) == THRESHOLDS

"""AC-31..AC-38 (each guardrail) and AC-39 (guardrailed outputs satisfy the invariants)."""

from __future__ import annotations

from actionx.guardrails import apply_guardrails, has_date_cue
from actionx.invariants import check_invariants
from support import SYSTEM_PROMPT, good_item, good_output, req


def run(output, request=None):
    return apply_guardrails(output, request or req(), SYSTEM_PROMPT)


def action_ids(actions):
    return [a.id for a in actions]


def test_good_output_is_unchanged_and_original_not_mutated():
    original = good_output()
    result, actions = run(original)
    assert result == good_output()
    assert actions == []
    assert original == good_output()


def test_ac31_gr01_leak_replaces_whole_output_with_refusal():
    leaky = good_output(needs_clarification=True, clarification_question="AX-CANARY-7f3e91")
    result, actions = run(leaky)
    assert result["refusal"] is True
    assert result["action_items"] == []
    assert result["refusal_reason"].startswith("Output withheld")
    assert action_ids(actions) == ["GR-01"]


def test_ac32_gr02_novel_url_drops_item_and_replaces_text():
    request = req(notes="Bob Rivera will send the report by Friday. See http://ok.example/a.")
    item = good_item(
        task="open http://evil.example/x", evidence="Bob Rivera will send the report by Friday."
    )
    keep = good_item(evidence="Bob Rivera will send the report by Friday.")
    out = good_output(
        [item, keep],
        needs_clarification=True,
        clarification_question="go to https://evil.example/q",
    )
    result, actions = run(out, request)
    assert result["action_items"] == [keep]
    assert "evil" not in str(result)
    assert action_ids(actions) == ["GR-02", "GR-02"]
    ok = good_output(
        [keep], needs_clarification=True, clarification_question="is http://ok.example/a right?"
    )
    assert run(ok, request)[1] == []


def test_ac32_gr02_refusal_reason_url_replaced():
    out = good_output([], refusal=True, refusal_reason="see http://evil.example")
    result, actions = run(out)
    assert "evil" not in result["refusal_reason"]
    assert action_ids(actions) == ["GR-02"]


def test_ac33_gr03_fabricated_evidence_dropped():
    out = good_output([good_item(evidence="a quote nobody said"), good_item(task="other task")])
    result, actions = run(out)
    assert [i["task"] for i in result["action_items"]] == ["other task"]
    assert action_ids(actions) == ["GR-03"]


def test_ac34_gr04_unknown_owner_nulled_item_kept_and_clarification_forced():
    result, actions = run(good_output([good_item(owner="Mallory")]))
    item = result["action_items"][0]
    assert item["owner"] is None
    assert result["needs_clarification"] is True
    assert result["clarification_question"]
    assert action_ids(actions) == ["GR-04", "GR-07", "GR-07"]


def test_ac35_gr05_impossible_past_and_cueless_dates_nulled():
    impossible, a1 = run(good_output([good_item(due_date="2026-02-30")]))
    assert impossible["action_items"][0]["due_date"] is None
    assert action_ids(a1) == ["GR-05"]
    past, a2 = run(good_output([good_item(due_date="2026-03-10")]))
    assert past["action_items"][0]["due_date"] is None
    assert action_ids(a2) == ["GR-05"]
    quiet = req(notes="Bob Rivera will send the report.")
    cueless, a3 = run(good_output([good_item(evidence="Bob Rivera will send the report.")]), quiet)
    assert cueless["action_items"][0]["due_date"] is None
    assert action_ids(a3) == ["GR-05"]
    kept, a4 = run(good_output())
    assert kept["action_items"][0]["due_date"] == "2026-03-13"
    assert a4 == []


def test_ac35_gr05_non_english_weekday_is_a_cue():
    assert has_date_cue("Marta enviará el informe el viernes.")
    assert has_date_cue("rendez-vous vendredi")
    assert has_date_cue("bis Freitag")
    assert has_date_cue("by 15th")
    assert not has_date_cue("Bob will send the report.")


def test_ac36_gr06_duplicates_keep_first():
    first = good_item()
    twin = good_item(task="Send the report")
    other = good_item(due_date=None)
    result, actions = run(good_output([first, twin, other]))
    assert result["action_items"] == [first, other]
    assert action_ids(actions) == ["GR-06"]


def test_ac37_gr07_consistency_rules():
    refused, a1 = run(good_output([good_item()], refusal=True, refusal_reason=None))
    assert refused["action_items"] == []
    assert refused["refusal_reason"]
    assert action_ids(a1) == ["GR-07", "GR-07"]
    stale, a2 = run(good_output(refusal_reason="leftover"))
    assert stale["refusal_reason"] is None
    assert action_ids(a2) == ["GR-07"]
    no_question, a3 = run(good_output(needs_clarification=True))
    assert no_question["clarification_question"]
    assert action_ids(a3) == ["GR-07"]
    stale_question, a4 = run(good_output(clarification_question="leftover?"))
    assert stale_question["clarification_question"] is None
    assert action_ids(a4) == ["GR-07"]
    kept, a5 = run(good_output([], needs_clarification=True, clarification_question="q?"))
    assert kept["clarification_question"] == "q?"
    assert a5 == []


def test_ac38_gr08_empty_task_dropped():
    result, actions = run(good_output([good_item(task="  "), good_item()]))
    assert result["action_items"] == [good_item()]
    assert action_ids(actions) == ["GR-08"]


def test_ac39_guardrailed_output_satisfies_every_invariant():
    hostile = good_output(
        [
            good_item(owner="Mallory", due_date="2026-02-30"),
            good_item(evidence="not in notes"),
            good_item(task="  "),
            good_item(task="visit http://evil.example"),
            good_item(),
            good_item(),
        ],
        needs_clarification=True,
        clarification_question="",
        refusal_reason="stale",
    )
    request = req()
    result, _ = run(hostile, request)
    assert check_invariants(result, request, SYSTEM_PROMPT) == []

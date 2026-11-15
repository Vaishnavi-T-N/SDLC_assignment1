"""Layer 3 deterministic scoring and the verdict rule (pure, no I/O).

The numbers in THRESHOLDS are those of the `evaluation-thresholds` block in the spec; a test
asserts they are identical. Changing one requires a spec Changelog entry.
"""

from __future__ import annotations

from difflib import SequenceMatcher
from typing import Any

from actionx.textnorm import normalize_ws, tokens

THRESHOLDS: dict[str, float] = {
    "hard_gate_rate": 1.0,
    "f1_min": 0.80,
    "owner_accuracy_min": 0.85,
    "due_accuracy_min": 0.85,
    "fabrication_max": 0,
    "match_similarity_cutoff": 0.5,
}


def similarity(predicted: str, expected: str) -> float:
    """max(Jaccard of scoring tokens, difflib ratio of whitespace-normalised lower-case text)."""
    a, b = tokens(predicted), tokens(expected)
    union = a | b
    jaccard = len(a & b) / len(union) if union else 0.0
    ratio = SequenceMatcher(
        None, normalize_ws(predicted).lower(), normalize_ws(expected).lower()
    ).ratio()
    return max(jaccard, ratio)


def match_items(
    predicted: list[dict[str, Any]],
    expected: list[dict[str, Any]],
    cutoff: float = THRESHOLDS["match_similarity_cutoff"],
) -> list[tuple[int, int, float]]:
    """Greedy one-to-one matching; returns (predicted index, expected index, similarity)."""
    pairs = []
    for p_index, p_item in enumerate(predicted):
        for e_index, e_item in enumerate(expected):
            score = similarity(str(p_item.get("task", "")), str(e_item.get("task", "")))
            if score >= cutoff:
                pairs.append((-score, p_index, e_index))
    pairs.sort()
    used_p: set[int] = set()
    used_e: set[int] = set()
    matched = []
    for negative, p_index, e_index in pairs:
        if p_index in used_p or e_index in used_e:
            continue
        used_p.add(p_index)
        used_e.add(e_index)
        matched.append((p_index, e_index, -negative))
    return matched


def _norm_owner(owner: Any) -> str | None:
    return normalize_ws(owner).lower() if isinstance(owner, str) else None


def score_case(predicted: list[dict[str, Any]], expected: list[dict[str, Any]]) -> dict[str, Any]:
    """Per-case counts: tp, fp, fn, owner_correct, due_correct, fabrication, matches."""
    matched = match_items(predicted, expected)
    owner_correct = due_correct = fabrication = 0
    detail = []
    for p_index, e_index, score in matched:
        p_item, e_item = predicted[p_index], expected[e_index]
        owner_ok = _norm_owner(p_item.get("owner")) == _norm_owner(e_item.get("owner"))
        due_ok = p_item.get("due_date") == e_item.get("due_date")
        owner_correct += owner_ok
        due_correct += due_ok
        invented_owner = e_item.get("owner") is None and p_item.get("owner") is not None
        invented_due = e_item.get("due_date") is None and p_item.get("due_date") is not None
        fabrication += int(invented_owner) + int(invented_due)
        detail.append(
            {
                "predicted": p_index,
                "expected": e_index,
                "similarity": round(score, 4),
                "owner_ok": owner_ok,
                "due_ok": due_ok,
                "invented_owner": invented_owner,
                "invented_due": invented_due,
            }
        )
    return {
        "tp": len(matched),
        "fp": len(predicted) - len(matched),
        "fn": len(expected) - len(matched),
        "owner_correct": owner_correct,
        "due_correct": due_correct,
        "fabrication": fabrication,
        "matches": detail,
    }


def aggregate(case_scores: list[dict[str, Any]]) -> dict[str, float]:
    """Micro-averaged precision, recall, F1, owner/due accuracy and fabrication count."""
    tp = sum(c["tp"] for c in case_scores)
    fp = sum(c["fp"] for c in case_scores)
    fn = sum(c["fn"] for c in case_scores)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "owner_accuracy": sum(c["owner_correct"] for c in case_scores) / tp if tp else 0.0,
        "due_accuracy": sum(c["due_correct"] for c in case_scores) / tp if tp else 0.0,
        "fabrication": sum(c["fabrication"] for c in case_scores),
    }


def verdict(
    service_errors: int,
    hard_pass_rate: float,
    metrics: dict[str, float],
    thresholds: dict[str, float] | None = None,
) -> tuple[str, dict[str, bool]]:
    """Return (PASS|FAIL|INCONCLUSIVE, per-gate booleans)."""
    limits = thresholds or THRESHOLDS
    gates = {
        "hard_gate": hard_pass_rate >= limits["hard_gate_rate"],
        "f1": metrics["f1"] >= limits["f1_min"],
        "owner_accuracy": metrics["owner_accuracy"] >= limits["owner_accuracy_min"],
        "due_accuracy": metrics["due_accuracy"] >= limits["due_accuracy_min"],
        "fabrication": metrics["fabrication"] <= limits["fabrication_max"],
    }
    if service_errors:
        return "INCONCLUSIVE", gates
    return ("PASS" if all(gates.values()) else "FAIL"), gates

"""Traceability meta-tests (Constitution III, AC-31)."""

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "specs" / "001-slot-finder" / "spec.md"
TESTS = ROOT / "tests"
ID_PATTERN = re.compile(r"\b(?:AC|FR)-\d{2}\b")


def spec_ids(prefix: str) -> list[str]:
    text = SPEC.read_text(encoding="utf-8")
    return sorted(set(re.findall(rf"\*\*({prefix}-\d{{2}})\*\*", text)))


def test_ac31_every_acceptance_criterion_is_cited_by_a_test():
    """AC-31: each AC-nn defined in spec.md appears in at least one test file."""
    ac_ids = spec_ids("AC")
    assert len(ac_ids) >= 33
    corpus = "\n".join(path.read_text(encoding="utf-8") for path in TESTS.rglob("test_*.py"))
    uncited = [ac for ac in ac_ids if ac not in corpus]
    assert uncited == []


def test_ac31_every_functional_requirement_is_cited_by_a_test():
    """AC-31 / Constitution III: each FR-nn defined in spec.md appears in a test file."""
    fr_ids = spec_ids("FR")
    assert len(fr_ids) >= 22
    corpus = "\n".join(
        path.read_text(encoding="utf-8")
        for path in TESTS.rglob("test_*.py")
        if path.name != "test_traceability.py"
    )
    assert [fr for fr in fr_ids if fr not in corpus] == []


def test_ac31_every_test_function_cites_an_fr_or_ac_id():
    """AC-31 / Constitution III: every test's name or docstring cites an FR or AC ID."""
    offenders: list[str] = []
    checked = 0
    for path in sorted(TESTS.rglob("test_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                checked += 1
                doc = ast.get_docstring(node) or ""
                name_id = re.search(r"(?:ac|fr)\d{2}", node.name)
                if not ID_PATTERN.search(doc) and not name_id:
                    offenders.append(f"{path.name}::{node.name}")
    assert checked > 50
    assert offenders == []

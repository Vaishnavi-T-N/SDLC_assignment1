"""AC-60 (pure core), AC-46 (no secrets in the repository), AC-90 (every AC is cited by a test)."""

from __future__ import annotations

import ast
import re

from support import ROOT, SPEC_PATH

SRC = ROOT / "src" / "actionx"
PURE = ["model", "textnorm", "parsing", "contract", "invariants", "guardrails", "scoring"]
FORBIDDEN_IN_PURE = {"os", "sys", "io", "pathlib", "socket", "subprocess", "time", "random", "secrets",
                     "logging", "urllib", "http", "shutil", "tempfile"}
FORBIDDEN_EVERYWHERE = {"subprocess", "socket", "pickle"}
FORBIDDEN_CALLS = {"open", "print", "input", "eval", "exec"}


def imported(tree):
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names.add(node.module.split(".")[0])
    return names


def test_ac60_pure_modules_have_no_io_imports_or_calls():
    for name in PURE:
        source = (SRC / f"{name}.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        assert not imported(tree) & FORBIDDEN_IN_PURE, name
        calls = {n.func.id for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        assert not calls & FORBIDDEN_CALLS, name
        assert not re.search(r"\.(now|today|utcnow)\(", source), name


def test_ac60_no_module_imports_process_network_or_pickle_and_nothing_evals():
    for path in SRC.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        assert not imported(tree) & FORBIDDEN_EVERYWHERE, path.name
        calls = {n.func.id for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        assert not calls & {"eval", "exec"}, path.name


def test_ac46_no_google_api_key_pattern_in_any_repository_text_file():
    pattern = re.compile(r"AIza[0-9A-Za-z_-]{35}")
    skip_dirs = {".venv", ".git", "__pycache__", ".pytest_cache", ".ruff_cache"}
    checked = 0
    for path in ROOT.rglob("*"):
        if not path.is_file() or skip_dirs & set(path.relative_to(ROOT).parts) or path.name == ".env":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        checked += 1
        assert not pattern.search(text), str(path)
    assert checked > 20


def test_ac46_env_and_venv_are_gitignored_and_example_is_a_placeholder():
    lines = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert ".env" in lines
    assert ".venv/" in lines
    example = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert "your-api-key-here" in example


def cited_ac_numbers():
    found = set()
    for path in (ROOT / "tests").rglob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        found |= {int(m) for m in re.findall(r"(?<![a-z])ac[-_]?(\d{2})(?!\d)", text)}
        for low, high in re.findall(r"ac[-_]?(\d{2})\.\.ac[-_]?(\d{2})", text):
            found |= set(range(int(low), int(high) + 1))
    return found


def test_ac90_every_acceptance_criterion_in_the_spec_is_cited_by_a_test():
    spec = SPEC_PATH.read_text(encoding="utf-8")
    defined = {int(n) for n in re.findall(r"\*\*AC-(\d+)", spec)}
    assert len(defined) >= 60
    missing = sorted(defined - cited_ac_numbers())
    assert missing == []

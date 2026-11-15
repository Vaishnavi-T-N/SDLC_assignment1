"""Architecture tests: pure core, no network or process modules (FR-21, FR-22, AC-30)."""

import ast
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src" / "slotfinder"
PURE_MODULES = ["errors", "intervals", "model", "parsing", "core", "output"]
FORBIDDEN_IMPORTS = {
    "os", "sys", "io", "pathlib", "socket", "subprocess", "time", "random", "secrets",
    "logging", "urllib", "http", "shutil", "tempfile", "requests", "ssl", "asyncio",
}  # fmt: skip
FORBIDDEN_NETWORK_OR_PROCESS = {
    "socket", "urllib", "http", "subprocess", "requests", "ssl", "ftplib", "smtplib",
    "telnetlib", "xmlrpc", "multiprocessing",
}  # fmt: skip
FORBIDDEN_CALLS = {"open", "print", "input", "exec", "eval", "compile", "__import__"}
FORBIDDEN_CLOCK_ATTRIBUTES = {"now", "today", "utcnow", "fromtimestamp", "utcfromtimestamp"}


def imported_roots(tree: ast.AST) -> set[str]:
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            roots.add(node.module.split(".")[0])
    return roots


@pytest.mark.parametrize("module", PURE_MODULES)
def test_ac30_pure_module_imports_no_io_clock_or_random(module):
    """AC-30 / FR-21: pure modules import none of the forbidden modules."""
    tree = ast.parse((SRC / f"{module}.py").read_text(encoding="utf-8"))
    assert imported_roots(tree) & FORBIDDEN_IMPORTS == set()


@pytest.mark.parametrize("module", PURE_MODULES)
def test_ac30_pure_module_calls_no_io_builtin_and_reads_no_clock(module):
    """AC-30 / FR-21: pure modules call no I/O builtin and no clock accessor."""
    tree = ast.parse((SRC / f"{module}.py").read_text(encoding="utf-8"))
    called_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    attributes = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
    assert called_names & FORBIDDEN_CALLS == set()
    assert attributes & FORBIDDEN_CLOCK_ATTRIBUTES == set()


def test_ac30_no_source_module_imports_network_or_process_modules():
    """AC-30 / FR-22: nothing under src/ may import network or process-spawning modules."""
    files = sorted(SRC.glob("*.py"))
    assert len(files) >= 9
    for path in files:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        assert imported_roots(tree) & FORBIDDEN_NETWORK_OR_PROCESS == set(), path.name


def test_ac30_only_cli_modules_touch_stdout_or_files():
    """AC-30 / FR-21: the I/O modules are exactly cli.py and __main__.py."""
    io_roots = {"sys", "pathlib", "argparse"}
    users = {
        path.name
        for path in SRC.glob("*.py")
        if imported_roots(ast.parse(path.read_text(encoding="utf-8"))) & io_roots
    }
    assert users == {"cli.py"}

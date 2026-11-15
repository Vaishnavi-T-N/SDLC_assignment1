#!/usr/bin/env python3
"""Run the three quality gates and record the outcome (Constitution IV). Standard library only.

Gates (always all three, in this order, regardless of earlier failures):
  1. lint      ruff check src tests          (rules from ruff.toml: E,F,I,B,UP,S)
  2. security  bandit -r src                 (all severities and confidences; any finding fails)
  3. tests     pytest + pytest-cov           (any failure fails; line coverage of src must be >= 90 %)

Each run writes, never overwriting an earlier run:
  evidence/harness-results/run-NN.json                structured result
  evidence/harness-results/run-NN-<gate>.stdout.txt   verbatim stdout of the gate command
  evidence/harness-results/run-NN-<gate>.stderr.txt   verbatim stderr of the gate command
and appends one machine-generated entry to evidence/harness-log.md under
"## Machine-recorded runs". The script takes no arguments: there is no way to skip a gate,
change a threshold, or alter a recorded result.

Exit status: 0 when every gate passes, 1 otherwise, 2 for a usage or environment error.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "evidence" / "harness-results"
LOG_FILE = ROOT / "evidence" / "harness-log.md"
MACHINE_HEADING = "## Machine-recorded runs"
COVERAGE_THRESHOLD = 90.0
MAX_TEXT = 4000


def next_run_number() -> int:
    numbers = [
        int(match.group(1))
        for path in RESULTS_DIR.glob("run-*.json")
        if (match := re.fullmatch(r"run-(\d+)\.json", path.name))
    ]
    return max(numbers, default=0) + 1


def execute(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace",
        check=False,
    )


def relative(path: str) -> str:
    try:
        return str(Path(path).resolve().relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return path


def gate_lint(py: str, run_id: str) -> dict:
    command = [py, "-m", "ruff", "check", "src", "tests", "--output-format", "json", "--no-cache"]
    done = execute(command)
    failed: list[dict] = []
    parse_error = None
    try:
        for item in json.loads(done.stdout or "[]"):
            failed.append(
                {
                    "rule": item.get("code"),
                    "file": relative(item.get("filename", "")),
                    "line": (item.get("location") or {}).get("row"),
                    "message": item.get("message"),
                }
            )
    except json.JSONDecodeError as error:
        parse_error = str(error)
    status = "PASS" if done.returncode == 0 and not failed and parse_error is None else "FAIL"
    return {
        "command": command, "done": done, "status": status, "failed_items": failed,
        "details": {"violations": len(failed), "parse_error": parse_error},
    }


def gate_security(py: str, run_id: str) -> dict:
    command = [
        py, "-m", "bandit", "-r", "src", "-c", "pyproject.toml",
        "--severity-level", "all", "--confidence-level", "all", "-f", "json",
    ]
    done = execute(command)
    failed: list[dict] = []
    parse_error = None
    try:
        report = json.loads(done.stdout or "{}")
        for item in report.get("results", []):
            failed.append(
                {
                    "rule": item.get("test_id"),
                    "name": item.get("test_name"),
                    "severity": item.get("issue_severity"),
                    "confidence": item.get("issue_confidence"),
                    "file": relative(item.get("filename", "")),
                    "line": item.get("line_number"),
                    "message": item.get("issue_text"),
                }
            )
        errors = report.get("errors", [])
    except json.JSONDecodeError as error:
        parse_error = str(error)
        errors = []
    ok = done.returncode == 0 and not failed and not errors and parse_error is None
    return {
        "command": command, "done": done, "status": "PASS" if ok else "FAIL",
        "failed_items": failed,
        "details": {"findings": len(failed), "tool_errors": errors, "parse_error": parse_error},
    }


def parse_expected_observed(text: str) -> dict | None:
    """Best-effort extraction of ``assert <observed> == <expected>`` from a pytest message."""
    for line in text.splitlines():
        match = re.search(r"assert (.+?) == (.+)$", line.strip())
        if match:
            return {"observed": match.group(1), "expected": match.group(2)}
    return None


def gate_tests(py: str, run_id: str) -> dict:
    junit = RESULTS_DIR / f"{run_id}-junit.xml"
    coverage_json = RESULTS_DIR / f"{run_id}-coverage.json"
    command = [
        py, "-m", "pytest", "--cov=actionx", f"--cov-report=json:{coverage_json}",
        "--cov-report=term-missing", f"--cov-fail-under={COVERAGE_THRESHOLD:g}",
        f"--junitxml={junit}", "-p", "no:cacheprovider", "-q",
    ]
    done = execute(command)
    failed: list[dict] = []
    totals = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
    parse_error = None
    try:
        suite_root = ET.parse(junit).getroot()
        for suite in suite_root.iter("testsuite"):
            for key in totals:
                totals[key] += int(suite.get(key, 0))
        for case in suite_root.iter("testcase"):
            for kind in ("failure", "error"):
                node = case.find(kind)
                if node is not None:
                    message = (node.get("message") or "") + "\n" + (node.text or "")
                    failed.append(
                        {
                            "test": f"{case.get('classname')}::{case.get('name')}",
                            "kind": kind,
                            "message": message[:MAX_TEXT],
                            "expected_vs_observed": parse_expected_observed(message),
                        }
                    )
    except (ET.ParseError, OSError) as error:
        parse_error = f"junit: {error}"
    coverage = None
    try:
        coverage = float(json.loads(coverage_json.read_text(encoding="utf-8"))["totals"]["percent_covered"])
    except (OSError, KeyError, ValueError) as error:
        parse_error = (parse_error or "") + f" coverage: {error}"
    if coverage is not None and coverage < COVERAGE_THRESHOLD:
        failed.append(
            {
                "test": "coverage",
                "kind": "threshold",
                "message": f"line coverage {coverage:.2f} % is below {COVERAGE_THRESHOLD:g} %",
                "expected_vs_observed": {
                    "expected": f">= {COVERAGE_THRESHOLD:g}", "observed": f"{coverage:.2f}",
                },
            }
        )
    ok = (
        done.returncode == 0 and not failed and totals["failures"] == 0 and totals["errors"] == 0
        and totals["tests"] > 0 and coverage is not None and parse_error is None
    )
    return {
        "command": command, "done": done, "status": "PASS" if ok else "FAIL",
        "failed_items": failed,
        "details": {
            **totals, "line_coverage_percent": coverage,
            "coverage_threshold_percent": COVERAGE_THRESHOLD, "parse_error": parse_error,
        },
    }


GATES = (("lint", gate_lint), ("security", gate_security), ("tests", gate_tests))


def short_item(gate: str, item: dict) -> str:
    if gate == "lint":
        return f"{item['rule']} {item['file']}:{item['line']} {item['message']}"
    if gate == "security":
        return f"{item['rule']} {item['file']}:{item['line']} {item['message']}"
    return f"{item['test']} ({item['kind']})"


def append_log(run_id: str, timestamp: str, overall: str, gates: list[dict]) -> None:
    existing = LOG_FILE.read_text(encoding="utf-8") if LOG_FILE.exists() else ""
    lines = []
    if MACHINE_HEADING not in existing:
        if existing and not existing.endswith("\n"):
            lines.append("")
        lines += ["", MACHINE_HEADING, ""]
    lines.append(f"### {run_id} | {timestamp} | {overall}")
    lines.append("")
    for gate in gates:
        lines.append(f"- {gate['gate']}: {gate['status']} (exit code {gate['exit_code']})")
        for item in gate["failed_items"]:
            lines.append(f"  - failed: {short_item(gate['gate'], item)}")
    coverage = next(g for g in gates if g["gate"] == "tests")["details"]["line_coverage_percent"]
    lines.append(f"- line coverage: {coverage if coverage is None else f'{coverage:.2f} %'}")
    lines.append(f"- structured result: evidence/harness-results/{run_id}.json")
    lines.append("")
    with LOG_FILE.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")


def main() -> int:
    if len(sys.argv) > 1:
        print("usage: python .harness/run_harness.py   (takes no arguments)", file=sys.stderr)
        return 2
    if sys.version_info[:2] != (3, 13):
        print(f"Python 3.13 is required, found {sys.version.split()[0]}", file=sys.stderr)
        return 2
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    number = next_run_number()
    run_id = f"run-{number:02d}"
    timestamp = datetime.now(UTC).isoformat(timespec="seconds")
    gates: list[dict] = []
    for name, function in GATES:
        outcome = function(sys.executable, run_id)
        done = outcome["done"]
        (RESULTS_DIR / f"{run_id}-{name}.stdout.txt").write_text(
            done.stdout, encoding="utf-8", newline="\n"
        )
        (RESULTS_DIR / f"{run_id}-{name}.stderr.txt").write_text(
            done.stderr, encoding="utf-8", newline="\n"
        )
        gates.append(
            {
                "gate": name,
                "command": " ".join(outcome["command"]),
                "exit_code": done.returncode,
                "status": outcome["status"],
                "failed_items": outcome["failed_items"],
                "details": outcome["details"],
                "stdout": done.stdout,
                "stderr": done.stderr,
            }
        )
        print(f"[{name}] {outcome['status']} (exit code {done.returncode})")
    overall = "PASS" if all(g["status"] == "PASS" for g in gates) else "FAIL"
    record = {
        "run": run_id, "timestamp_utc": timestamp, "python": sys.version.split()[0],
        "overall": overall, "gates": gates,
    }
    with (RESULTS_DIR / f"{run_id}.json").open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(record, handle, indent=2, sort_keys=False)
        handle.write("\n")
    append_log(run_id, timestamp, overall, gates)
    print(f"{run_id}: {overall}")
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())

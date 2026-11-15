<!--
Sync Impact Report
Version change: (template, unratified) -> 1.0.0
Modified principles: all (initial ratification from template)
Added sections: Core Principles I-VII, Quality Gates, Agent Conduct & Harness Integrity, Governance
Removed sections: none
Templates reviewed: plan-template.md (Constitution Check gate lists the principles below), spec-template.md (no change),
  tasks-template.md (tests are MANDATORY for this project, not optional) -> aligned
Deferred TODOs: none
-->

# Meeting-Slot Finder Constitution

## Core Principles

### I. Specification First (NON-NEGOTIABLE)
No production or test code is written until `spec.md`, `plan.md` and `tasks.md` exist and the
`analyze` report has no CRITICAL or HIGH finding left open. Every behaviour has a requirement ID
(`FR-xx`) and every edge case a binary acceptance criterion (`AC-xx`) that is either true or false
for a given build. Code that implements behaviour with no FR/AC is out of scope and MUST NOT be
added. The specification is changed only through the upstream artifacts (spec, plan, tasks) with a
dated entry in the spec's Changelog; code or tests are never edited to "make the spec true".

### II. Pure, Deterministic Core
All decision logic (parsing, validation, interval arithmetic, slot computation, serialisation) lives
in modules that perform NO I/O: they MUST NOT import `os`, `sys`, `io`, `pathlib`, `socket`,
`subprocess`, `time`, `random`, `secrets`, `logging`, `urllib`, `http`, `shutil` or `tempfile`, call
`open`, `print` or `input`, or read the clock (`datetime.now`, `today`, `utcnow`). Only
`slotfinder/cli.py` and `slotfinder/__main__.py` may touch files, stdin/stdout or `sys`. The same
input MUST produce byte-identical output on every run and platform. The sole indirect resource read
permitted to the core is the IANA time-zone database via `zoneinfo`, backed by the pinned `tzdata`
package. This principle is enforced by an automated test (AC-30).

### III. Test Traceability and Property Coverage
Tests are mandatory. Every test is derived from an AC or FR ID and its name or docstring cites that
ID. Every AC has at least one test; an automated test (AC-31) fails if an AC ID in `spec.md` is
cited by no test. Contract tests exercise the CLI end to end (exit codes, error codes, byte
identity). Property tests use Hypothesis with `derandomize=True` and no example database, so a run
is reproducible. Assertions are exact (expected values written out), never "does not raise".

### IV. Measurable Quality Gates
A change is acceptable only if all three gates pass in the same harness run:
1. `ruff check` is clean for rule families E, F, I, B, UP, S (target Python 3.13).
2. `bandit -r src` reports zero findings at every severity and confidence level.
3. The full pytest suite passes and line coverage of `src/` is at least 90 %.
The target interpreter is Python 3.13 (3.13.x only). Gates are run by `.harness/run_harness.py`,
which has no option to skip a gate.

### V. Security and Privacy by Construction
The tool performs no network access, spawns no processes, uses no `eval`/`exec`/`pickle`/`shell`,
and contains no secrets, tokens or credentials. The only file it reads is the path passed to
`--input`; it writes only to stdout. Untrusted input is validated before use; a time-zone key is
checked against a strict character allow-list before it reaches `zoneinfo`.

### VI. Stable, Explicit Contract
The error codes (`INVALID_JSON`, `MISSING_FIELD`, `NAIVE_DATETIME`, `INVALID_INTERVAL`,
`INVALID_TIMEZONE`, `INVALID_WORKING_HOURS`, `INVALID_DURATION`, `INVALID_WINDOW`,
`TOO_MANY_PARTICIPANTS`), the exit codes (0 success, 2 error), and the JSON shapes are a public
contract; renaming or repurposing one is a breaking change requiring a MAJOR version bump.
Error `message` text is informative only and is not part of the contract.

### VII. Simplicity
Standard library plus `tzdata` only at runtime. No frameworks, plugins or configuration files. Scope
is exactly what the specification lists; items it marks out of scope (overnight working hours,
recurring events, UI, persistence) are not implemented.

## Quality Gates

| Gate | Tool | Pass condition |
|------|------|----------------|
| 1 Lint | `ruff check src tests` (rules E,F,I,B,UP,S) | exit code 0, zero violations |
| 2 Security | `bandit -r src` (all severities) | zero findings |
| 3 Tests + coverage | `pytest` with `pytest-cov` | zero failures, line coverage of `src/` >= 90 % |

The only per-file lint exemption is rule `S101` (use of `assert`) under `tests/`, because assertions
are the mechanism of pytest. No other `ignore`, `per-file-ignores`, `# noqa`, `# nosec` or `# type:`
suppression is permitted anywhere.

## Agent Conduct and Harness Integrity

Any AI coding agent working in this repository MUST NOT:
- weaken, delete or reword an acceptance criterion to fit the code;
- delete, skip (`skip`, `xfail`, `-k`, `--deselect`) or lower the assertions of a failing test;
- disable, relax or add exceptions to ruff, bandit, coverage or pytest configuration, or lower the
  90 % threshold;
- edit, delete or regenerate anything under `evidence/` that a harness run recorded, or the
  `evidence/initial-generation/` snapshot;
- write the human sections of `evidence/harness-log.md`.

When a gate fails the agent repairs the implementation and re-runs the same gates. A test that is
wrong relative to the specification may be corrected only after the specification artifact is
updated upstream with a Changelog entry stating why.

## Governance

This constitution supersedes other practices. Amendments require a version bump (MAJOR: a principle
removed or redefined; MINOR: a principle or gate added; PATCH: wording), a Sync Impact Report, and a
review of the plan Constitution Check. All plans, task lists and analyze reports MUST verify
compliance with Principles I-VII; unjustified violations are CRITICAL findings.

**Version**: 1.0.0 | **Ratified**: 2026-11-15 | **Last Amended**: 2026-11-15

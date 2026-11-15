# Implementation Plan: Meeting-Slot Finder

**Branch**: '001-slot-finder' | **Date**: 2026-11-15 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from '/specs/001-slot-finder/spec.md'

## Summary

A pure-Python 3.13 library plus a thin CLI. The CLI reads a JSON file, a pure 'parsing' module turns
the untrusted object into validated immutable model objects (raising 'SlotFinderError' with one of
nine stable codes), a pure 'core' module computes the common free slots by interval arithmetic in UTC
(per-participant availability = working intervals minus busy, then intersection across participants),
and a pure 'output' module renders canonical JSON. See [research.md](research.md) for decisions.

## Technical Context

**Language/Version**: Python 3.13 (3.13.x only)

**Primary Dependencies**: standard library; 'tzdata' (runtime, IANA database on Windows)

**Dev Dependencies**: ruff, bandit[toml], pytest, pytest-cov, hypothesis (pinned in 'requirements-dev.txt')

**Storage**: N/A (single input file, stdout only)

**Testing**: pytest; unit, contract (CLI) and Hypothesis property tests; 'pytest-cov' line coverage

**Target Platform**: Windows and Linux, command line

**Project Type**: library + CLI (single project, 'src' layout)

**Performance Goals**: none specified (linear in local days x busy intervals; see spec Assumptions)

**Constraints**: deterministic byte-identical output; pure core (no I/O, clock, randomness); no network

**Scale/Scope**: up to 20 participants; unbounded busy list; window of days to weeks

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Check | Status |
|-----------|-------|--------|
| I Spec first | spec, clarifications, plan, tasks precede code; tasks reference FR/AC | PASS |
| II Pure core | 'errors', 'intervals', 'model', 'parsing', 'core', 'output' import no I/O modules; 'cli'/'__main__' own all I/O; AC-30 test (also bans network/process modules in 'src/') | PASS |
| III Traceability | every test cites FR/AC; AC-31 meta-test; Hypothesis 'derandomize=True', 'database=None' | PASS |
| IV Gates | ruff E,F,I,B,UP,S; bandit -r src all severities; pytest-cov >= 90 %; '.harness/run_harness.py' | PASS |
| V Security | no network/subprocess/eval; tz allow-list regex '^[A-Za-z0-9_+\-/]{1,64}$' and no empty or '..' segment before 'ZoneInfo' | PASS |
| VI Contract | nine codes in a 'StrEnum'; exit codes 0/2; contract in 'contracts/' | PASS |
| VII Simplicity | stdlib + tzdata; no frameworks; nine small files | PASS |

Post-design re-check: no violations; Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/001-slot-finder/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── cli-contract.md
│   ├── request.schema.json
│   └── response.schema.json
├── checklists/requirements.md
├── tasks.md
└── analyze-report.md
```

### Source Code (repository root)

```text
src/slotfinder/
├── __init__.py        # package version
├── __main__.py        # python -m slotfinder  (I/O boundary)
├── cli.py             # argparse, read file, write stdout bytes (I/O boundary)
├── errors.py          # ErrorCode StrEnum, SlotFinderError          (pure)
├── intervals.py       # merge / subtract / intersect / clip         (pure)
├── model.py           # frozen dataclasses                          (pure)
├── parsing.py         # validate untrusted object -> Request        (pure)
├── core.py            # working_intervals, find_slots               (pure)
└── output.py          # canonical JSON rendering                    (pure)

tests/
├── conftest.py        # Hypothesis profile
├── support.py         # request builders
├── unit/              # intervals, parsing, core, output, purity
├── contract/          # CLI contract, traceability
└── property/          # Hypothesis properties

.harness/run_harness.py   # gates; stdlib only
evidence/                  # harness results, snapshots, human log
```

**Structure Decision**: Single project, 'src' layout, pure modules separated from the two I/O
modules so that Principle II is checkable by import scanning.

## Algorithm (core)

1. For each participant: for each local date 'd' in '[local(window.start).date - 1,
   local(window.end).date + 1]': 's = combine(d, wh.start, tz)', 'e = combine(d, wh.end, tz)' (fold 0),
   convert to UTC, drop if 'e <= s'; clip to window; 'merge'.
2. 'busy' = 'merge(clip(busy, window))'.
3. 'free_p = subtract(working_p, busy_p)'.
4. 'common = reduce(intersect, free_p)'.
5. Keep intervals with 'end - start >= min_duration'.

All lists are sorted, disjoint and non-touching after 'merge', so maximality (FR-16) follows from the
invariants of 'intersect' and 'subtract'.

## Complexity Tracking

No Constitution violations.

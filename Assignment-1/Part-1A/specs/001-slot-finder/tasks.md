---

description: "Task list for Meeting-Slot Finder"
---

# Tasks: Meeting-Slot Finder

**Input**: Design documents from '/specs/001-slot-finder/'

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: MANDATORY (Constitution III). Every test names the FR/AC it derives from.

**Organization**: Grouped by user story; foundational pure modules first.

## Format: '[ID] [P?] [Story] Description'

- **[P]**: parallelisable (different files, no dependency)
- **[Story]**: US1..US4 from spec.md
- Requirement references in parentheses

## Phase 1: Setup (Shared Infrastructure)

- [ ] T001 Create 'pyproject.toml' (project metadata, 'requires-python = "==3.13.*"', runtime dependency 'tzdata', pytest and coverage settings, bandit config) and 'src/slotfinder/__init__.py' (Constitution IV)
- [ ] T002 [P] Create 'ruff.toml' with rules E,F,I,B,UP,S, target py313, only exemption S101 under 'tests/' (Constitution IV)
- [ ] T003 [P] Create 'requirements-dev.txt' (ruff, bandit[toml], pytest, pytest-cov, hypothesis, tzdata) and '.gitignore' (excludes '.venv')
- [ ] T004 [P] Create '.harness/run_harness.py' (stdlib only: gates lint, security, tests+coverage; JSON per run in 'evidence/harness-results/'; machine entry appended to 'evidence/harness-log.md'; no skip option) (Constitution IV)
- [ ] T005 [P] Create 'tests/conftest.py' (Hypothesis profile 'derandomize=True', 'database=None') and 'tests/support.py' (request builder helpers) (Constitution III)
- [ ] T006 [P] Create 'README.md' and 'evidence/harness-log.md' skeleton (human sections left as placeholders)

---

## Phase 2: Foundational (Blocking Prerequisites)

- [ ] T007 [P] Implement 'src/slotfinder/errors.py': 'ErrorCode' StrEnum with the nine codes and 'SlotFinderError(code, message)' (FR-18)
- [ ] T008 [P] Implement 'src/slotfinder/intervals.py': 'merge' (fuse overlapping and touching), 'subtract', 'intersect', 'clip'; half-open semantics (FR-05, FR-14, FR-16)
- [ ] T009 [P] Implement 'src/slotfinder/model.py': frozen dataclasses 'WorkingHours', 'Participant', 'Request' per data-model.md
- [ ] T010 [P] Write unit tests 'tests/unit/test_intervals.py' for merge/subtract/intersect/clip including touching, duplicate and empty cases (FR-05, FR-14, FR-16, AC-03, AC-04, AC-05)

**Checkpoint**: foundation ready.

---

## Phase 3: User Story 1 - Find common free slots (Priority: P1) MVP

**Goal**: slots for participants, busy handling, duration filter.

**Independent Test**: UTC-only request returns expected slots.

### Tests for User Story 1

- [ ] T011 [P] [US1] 'tests/unit/test_core.py': AC-01, AC-03, AC-04, AC-05, AC-08, AC-19, AC-20, AC-25 with exact expected slots (FR-14, FR-15, FR-16)
- [ ] T012 [P] [US1] 'tests/unit/test_parsing.py': busy validation AC-06, AC-07; duration AC-14; window AC-15; participant count AC-16 (FR-06, FR-07, FR-08, FR-13)

### Implementation for User Story 1

- [ ] T013 [US1] Implement 'src/slotfinder/parsing.py': 'parse_request(obj) -> Request'; required-field checks (FR-03, FR-09), duration (FR-07), window (FR-06), participant count (FR-08), busy intervals (FR-13), in the order of FR-19
- [ ] T014 [US1] Implement 'src/slotfinder/core.py': 'find_slots(request) -> list[Interval]' per the plan algorithm (FR-14, FR-15, FR-16)

**Checkpoint**: US1 passes with UTC participants.

---

## Phase 4: User Story 2 - Time zones and daylight saving (Priority: P2)

**Goal**: local working hours per IANA zone, DST rules, UTC midnight crossing.

### Tests for User Story 2

- [ ] T015 [P] [US2] 'tests/unit/test_core.py': AC-02, AC-21, AC-22, AC-23, AC-24, AC-26 with hand-computed UTC ranges (FR-12, FR-16, FR-04)
- [ ] T016 [P] [US2] 'tests/unit/test_parsing.py': timezone AC-12 (including allow-list cases); working hours AC-13 (FR-10, FR-11, FR-22)

### Implementation for User Story 2

- [ ] T017 [US2] Extend 'parsing.py': timezone allow-list + 'ZoneInfo' resolution (FR-10, FR-22); working-hours 'HH:MM' and ordering validation (FR-11)
- [ ] T018 [US2] Extend 'core.py': 'working_intervals' using fold-0 wall-clock conversion, local days from window start -1 to end +1, drop empty/negative days, clip to window (FR-12, FR-16)

**Checkpoint**: US1 and US2 independently pass.

---

## Phase 5: User Story 3 - Stable error codes (Priority: P2)

**Goal**: nine codes, exit 2, JSON error object, precedence.

### Tests for User Story 3

- [ ] T019 [P] [US3] 'tests/unit/test_parsing.py': datetime handling AC-09, AC-10, AC-11; missing fields AC-17; precedence AC-32 (FR-03, FR-04, FR-19)
- [ ] T020 [P] [US3] 'tests/contract/test_cli_contract.py': every error code via the CLI, AC-18, AC-28, AC-33, exit code 2, stderr empty, usage error without '--input' (FR-01, FR-02, FR-18)

### Implementation for User Story 3

- [ ] T021 [US3] Extend 'parsing.py': datetime parsing with naive/unparseable/fractional/range rules (FR-04); 'MISSING_FIELD' checks for all containers (FR-03, FR-09)
- [ ] T022 [US3] Implement 'src/slotfinder/cli.py' and 'src/slotfinder/__main__.py': argparse 'find --input', UTF-8 read, JSON load, error mapping to exit 2 (FR-01, FR-02, FR-18, FR-21)

---

## Phase 6: User Story 4 - Deterministic output (Priority: P3)

**Goal**: canonical bytes, order independence.

### Tests for User Story 4

- [ ] T023 [P] [US4] 'tests/unit/test_output.py' and CLI tests: AC-27 compact sorted keys, LF only, 'Z' suffix (FR-17, FR-20)
- [ ] T024 [P] [US4] 'tests/contract/test_cli_contract.py': AC-29 byte-identical repeated runs and permuted input via subprocess (FR-20)
- [ ] T025 [P] [US4] 'tests/property/test_properties.py': Hypothesis properties: no overlap with busy, inside working hours, sorted/non-touching/min duration, permutation invariance, brute-force minute oracle on non-DST windows (FR-14, FR-15, FR-16, FR-20, AC-25, AC-29)

### Implementation for User Story 4

- [ ] T026 [US4] Implement 'src/slotfinder/output.py': 'render_success', 'render_error' (FR-17, FR-18, FR-20); wire CLI to write bytes to 'sys.stdout.buffer'

---

## Phase 7: Polish and Cross-Cutting Concerns

- [ ] T027 [P] 'tests/unit/test_purity.py': AST scan of the pure modules for forbidden imports/calls and of all 'src/' modules for network/process imports (FR-21, FR-22, AC-30)
- [ ] T028 [P] 'tests/contract/test_traceability.py': every 'AC-nn' in 'spec.md' is cited by a test (Constitution III, AC-31)
- [ ] T029 Snapshot 'src/' and 'tests/' to 'evidence/initial-generation/' with 'CONTEXT.md' after the first complete draft and BEFORE any harness run
- [ ] T030 Run '.harness/run_harness.py'; on a failing gate save evidence in 'evidence/repair-cycle-NN/', repair the implementation only, re-run the same gates
- [ ] T031 Snapshot final 'src/' and 'tests/' to 'evidence/final-generation/' and record a final passing run

---

## Dependencies and Execution Order

- Phase 1 then Phase 2 then US1; US2, US3, US4 each build on 'parsing.py'/'core.py' from US1 (same files, so sequential in priority order US1, US2, US3, US4).
- Within a story, tests (T011/T012, T015/T016, T019/T020, T023-T025) are written before the implementation tasks of that story (T013-T014, T017-T018, T021-T022, T026).
- T029 follows all implementation and the first full test draft; T030 follows T029.

### Parallel Opportunities

- T002-T006 together; T007-T010 together; tests marked [P] within a phase together.

## Requirement Coverage Map

| Requirement | Tasks |
|-------------|-------|
| FR-01 | T020, T022 |
| FR-02 | T020, T022 |
| FR-03 | T019, T021 |
| FR-04 | T015, T019, T021 |
| FR-05 | T008, T010 |
| FR-06 | T012, T013 |
| FR-07 | T012, T013 |
| FR-08 | T012, T013 |
| FR-09 | T013, T019, T021 |
| FR-10 | T016, T017 |
| FR-11 | T016, T017 |
| FR-12 | T015, T018 |
| FR-13 | T012, T013 |
| FR-14 | T008, T011, T014, T025 |
| FR-15 | T011, T014, T025 |
| FR-16 | T008, T011, T014, T018, T025 |
| FR-17 | T023, T026 |
| FR-18 | T007, T020, T022, T026 |
| FR-19 | T013, T019 |
| FR-20 | T023, T024, T025, T026 |
| FR-21 | T022, T027 |
| FR-22 | T016, T017, T027 |

| Acceptance criterion | Tasks |
|----------------------|-------|
| AC-01, AC-03, AC-04, AC-05, AC-08, AC-19, AC-20, AC-25 | T011, T010 |
| AC-02, AC-21, AC-22, AC-23, AC-24, AC-26 | T015 |
| AC-06, AC-07, AC-14, AC-15, AC-16 | T012 |
| AC-12, AC-13 | T016 |
| AC-09, AC-10, AC-11, AC-17, AC-32 | T019 |
| AC-18, AC-28, AC-33 | T020 |
| AC-27 | T023 |
| AC-29 | T024, T025 |
| AC-30 | T027 |
| AC-31 | T028 |

## Implementation Strategy

MVP = Phases 1-3, verified at library level through the core and parsing tests (the CLI is wired in Phase 5). Then add US2, US3, US4 in order, running the unit tests after each phase. The
first full implementation and test draft is snapshotted (T029) before any harness gate is run.

## Notes

- Tests are not weakened to pass; a test conflicting with the spec is fixed only after a spec
  Changelog entry.
- No '# noqa', '# nosec', skips or xfails.

# Specification Analysis Report: 001-action-extractor

Artifacts analysed: '.specify/memory/constitution.md' (v1.0.0), 'spec.md' (v0.2), 'plan.md', 'research.md',
'data-model.md', 'contracts/*', 'quickstart.md', 'tasks.md'. Performed 2026-11-15, before any code existed.

## Findings (first pass)

| ID | Category | Severity | Location(s) | Summary | Recommendation | Resolution |
|----|----------|----------|-------------|---------|----------------|------------|
| E1 | Coverage Gap | HIGH | spec FR-23, tasks T014 | The CLI requirement and its exit codes have no AC and T014 has no test | Add an AC and a test task | FIXED: AC-44 added; T014 now lists 'test_cli.py' |
| E2 | Coverage Gap | MEDIUM | spec INV-12, tasks T008 | INV-12 has no checker AC although INV-02..INV-11 each have one | Add an AC | FIXED: AC-30 added; T008 updated |
| E3 | Coverage Gap | MEDIUM | spec FR-09, FR-08 | "raw output and guardrail actions are retained" is untested; the harness depends on it for the raw-vs-final report | Add an AC and map it to T013 | FIXED: AC-45 added; T013 updated |
| E4 | Coverage Gap | MEDIUM | spec FR-22, SC-04 | SC-04 (no secret in repo) has no AC; AC-42 covers only runtime | Add a repository scan AC | FIXED: AC-46 added; T018 gains 'test_no_secrets.py' |
| E5 | Coverage Gap | LOW | spec FR-16, FR-17, FR-24 | Only dataset cases exercise duplicates, evidence, non-English, with no AC naming them | Name them in a behavioural AC | FIXED: AC-87 added; T015 updated |
| R1 | Risk / Inconsistency | MEDIUM | spec FR-20 vs FR-21 | A harmful-request case can be blocked by Gemini's safety filter, which FR-21 classes as SERVICE_ERROR and so makes the run INCONCLUSIVE; the interaction is unstated | Document, do not relax FR-21 | FIXED: Assumptions now states it |
| E6 | Inconsistency | MEDIUM | spec INV-03 vs GR-05 | INV-03 requires a real calendar date but no guardrail repairs an impossible date such as 2026-02-30, so the invariant could fail on the final output | Extend GR-05 and AC-35 | FIXED: GR-05 and AC-35 extended |
| E7 | Ambiguity | MEDIUM | spec GR-07 vs GR-08 | GR-07 (clarification forced by ownerless items) would run before GR-08 drops empty-task items and could leave 'needs_clarification' true for no remaining ownerless item | State the order GR-08 before GR-07 | FIXED: order sentence in the Guardrails heading |
| T1 | Traceability | LOW | spec AC-90 | The sentence cites AC-80..AC-86, which would omit AC-87 | Update the range | FIXED |
| D1 | Duplication | LOW | spec BP-xx vs FR-10..FR-20 | Behavioural properties restate FRs | Keep: BPs name the dataset-checkable form | ACCEPTED |
| A1 | Ambiguity | LOW | spec Layer 3 | Tokenisation of non-Latin scripts yields empty token sets (similarity falls back to difflib) | Dataset non-English case is Latin-script; note only | ACCEPTED (documented here) |
| P1 | Constitution | LOW | plan "Fake mode" | Canned outputs are derived from dataset ground truth: acceptable only because they live in 'tests/', never in 'src/', and fake results are labelled | Keep with AC-61 | ACCEPTED |

No CRITICAL findings; the HIGH finding E1 is closed. Thresholds and formula are untouched; AC-35 was only extended
(spec Changelog v0.3).

## Coverage Summary (after fixes)

| Requirement | Task(s) | AC(s) |
|-------------|---------|-------|
| FR-01, FR-02 | T005 | AC-03, AC-04 |
| FR-03 | T007 | AC-15 |
| FR-04, FR-05 | T005, T013 | AC-01, AC-02 |
| FR-06 | T005, T011, T013 | AC-05, AC-06, AC-16 |
| FR-07 | T006 | AC-10..AC-12 |
| FR-08 | T005, T013 | AC-13, AC-14, AC-45 |
| FR-09 | T009, T013 | AC-39, AC-45 |
| FR-10..FR-15 | T003, T015 | AC-80..AC-83 |
| FR-16, FR-17, FR-24 | T003, T015 | AC-87 |
| FR-12 | T015 | AC-71, AC-81 |
| FR-18, FR-19 | T003, T015 | AC-84 |
| FR-20 | T003, T015 | AC-85 |
| FR-21 | T011, T013, T016 | AC-40, AC-41, AC-54, AC-55 |
| FR-22 | T012 | AC-42, AC-43, AC-46 |
| FR-23 | T014 | AC-44 |
| INV-02..INV-12 | T008 | AC-20..AC-30 |
| GR-01..GR-08 | T009 | AC-31..AC-38 |
| GR-09 | T007 | AC-14 |
| Evaluation formula / verdict | T010, T016 | AC-50..AC-57, AC-86 |
| Harness behaviour | T016, T017 | AC-61..AC-64 |
| Dataset | T015 | AC-70, AC-71 |

**Constitution alignment**: I (task order), II (scoring, invariants, raw-vs-final), III (AC-60), IV (T017, T021),
V (AC-42, AC-46, AC-62), VI (schema, SERVICE_ERROR), VII (two dependencies), VIII (AC-54, AC-55, AC-61):
no issues. **Unmapped tasks**: T001, T002, T019..T022 (setup and evidence), by design.

## Metrics (after fixes)
FR 24, INV 12, GR 9, BP 8, AC 64 (numbered groups), tasks 22. CRITICAL 0, HIGH 0 open, MEDIUM 0 open.

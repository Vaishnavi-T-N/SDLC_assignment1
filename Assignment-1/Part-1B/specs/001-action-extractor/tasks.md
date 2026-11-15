# Tasks: Meeting-Notes Action-Item Extractor

**Input**: spec.md (v0.2), plan.md, research.md, data-model.md, contracts/
Tests are MANDATORY (Constitution III-IV). No code before the analyze report has no CRITICAL/HIGH open.

## Phase 1: Setup
- [ ] T001 Pin tooling: 'requirements.txt', 'requirements-dev.txt', 'ruff.toml', 'pyproject.toml', '.gitignore' ('.env', '.venv'), '.env.example'
- [ ] T002 [P] 'src/actionx/' package skeleton and 'tests/' layout
- [ ] T003 [P] 'prompts/extractor_system.md' (with canary) implementing FR-10..FR-20, FR-24

## Phase 2: Pure core (tests first within each task)
- [ ] T004 'textnorm.py' (normalisation, tokens, word runs, URL regex)
- [ ] T005 'model.py': 'parse_request', 'build_user_message', fallback and precheck outputs (FR-01, FR-02, FR-04..FR-06, FR-08) + 'tests/unit/test_model.py' (AC-03, AC-04, AC-05)
- [ ] T006 'parsing.py' (FR-07) + 'tests/unit/test_parsing.py' (AC-10, AC-11, AC-12, AC-13)
- [ ] T007 'contract.py' ('validate_output', 'gemini_schema') + 'tests/unit/test_contract.py' (AC-14, AC-15, AC-16)
- [ ] T008 'invariants.py': INV-02..INV-12 + case properties + 'tests/unit/test_invariants.py' (AC-20..AC-30, AC-57)
- [ ] T009 'guardrails.py': GR-01..GR-08 + 'tests/unit/test_guardrails.py' (AC-30, AC-31..AC-38)
- [ ] T010 'scoring.py': THRESHOLDS, matching, scores, verdict + 'tests/unit/test_scoring.py' (AC-50..AC-56)

## Phase 3: Impure seam
- [ ] T011 'client.py': 'ModelClient', 'ServiceError', 'FakeModelClient', 'GeminiClient' (injected SDK) + 'tests/unit/test_client.py' (AC-41)
- [ ] T012 'config.py': env, '.env' loader, 'ConfigError' + tests (AC-42, AC-43)
- [ ] T013 'extractor.py': flow, retry/backoff, guardrails integration + 'tests/unit/test_extractor.py' (AC-01, AC-02, AC-06, AC-13, AC-14, AC-39, AC-40, AC-45)
- [ ] T014 'cli.py', '__main__.py' (FR-23) + 'tests/unit/test_cli.py' (AC-44)

## Phase 4: Dataset and harness
- [ ] T015 'evals/dataset.json' (>= 18 cases, all categories) + 'tests/fixtures/canned_outputs.json' + 'tests/contract/test_dataset.py' (AC-70, AC-71, AC-80..AC-87)
- [ ] T016 '.harness/run_eval.py' (layers 1-3, raw vs final, verdict, evidence, log entry, fake/gemini modes) + 'tests/contract/test_harness.py' (AC-61..AC-64)
- [ ] T017 '.harness/run_harness.py' (ruff, bandit, pytest+coverage)
- [ ] T018 'tests/contract/test_purity.py' (AC-60), 'tests/contract/test_traceability.py' (AC-90), 'tests/contract/test_no_secrets.py' (AC-46)

## Phase 5: Evidence and docs
- [ ] T019 Snapshot 'src/', 'prompts/', 'tests/' to 'evidence/initial-generation/' + 'CONTEXT.md' BEFORE any gate or eval
- [ ] T020 'README.md', 'evidence/harness-log.md' skeleton (human sections empty)
- [ ] T021 Run 'run_harness.py' until PASS (repairs under constitution rules); run 'run_eval.py --client fake' once as self-test
- [ ] T022 Copy final 'src/', 'prompts/', 'tests/' to 'evidence/final-generation/'

## Dependencies
T004 -> T005..T010; T011, T012 -> T013 -> T014; T015, T016 need T013; T019 after T018 and before T021.

## Requirement -> task map
FR-01/02 T005; FR-03 T007; FR-04/05 T005, T013; FR-06 T005, T011, T013; FR-07 T006; FR-08 T005, T013;
FR-09 T009, T013; FR-10..FR-20 T003, T015; FR-21 T011, T013, T016; FR-22 T012; FR-23 T014; FR-24 T003, T015.
INV-02..INV-11 T008; INV-12 T008. GR-01..GR-08 T009; GR-09 T007.

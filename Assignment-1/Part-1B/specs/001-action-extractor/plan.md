# Implementation Plan: Meeting-Notes Action-Item Extractor

**Branch**: `001-action-extractor` | **Date**: 2026-11-15 | **Spec**: [spec.md](spec.md)

## Summary
A small Python 3.13 library plus CLI. A pure core (request validation, prompt message, JSON extraction,
schema validation, invariants, guardrails, scoring) surrounds one impure seam, `ModelClient`, implemented by
`GeminiClient` (live) and `FakeModelClient` (tests, harness self-test). A single evaluation pipeline
`.harness/run_eval.py` runs dataset -> app -> Layer 1 -> Layer 2 -> Layer 3 -> verdict -> evidence, and
`.harness/run_harness.py` runs the code-quality gates.

## Technical Context
**Language/Version**: Python 3.13.x only. **Dependencies**: `google-genai==3.3.0`, `jsonschema==4.26.0`
(runtime); `ruff`, `bandit`, `pytest`, `pytest-cov` (dev), all pinned. **Storage**: files under `evidence/`.
**Testing**: pytest with `FakeModelClient`; no network in tests. **Target**: Windows, PowerShell.
**Project type**: library + CLI + harness. **Constraints**: key only from env; deterministic core.
**Scale**: dataset of about two dozen cases; one model call per case.

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| I Spec first | tasks.md order: spec artifacts -> analyze -> code; spec Changelog for changes |
| II Layered evaluation | `scoring.py` + `invariants.py` + `contract.py`; thresholds in spec block; raw vs final reported |
| III Isolated model, pure core | pure modules listed in the layout; AC-60 test scans imports |
| IV Quality gates | `run_harness.py` (ruff, bandit, pytest+cov >= 90 %) ; `run_eval.py` is gate 4 |
| V Secrets | `config.py` env-only; AC-42/AC-62 tests; `.env`, `.venv` git-ignored; `.env.example` placeholder |
| VI Stable contract | `contracts/output.schema.json`; SERVICE_ERROR classification in `client.py` |
| VII Simplicity | two runtime dependencies, no framework |
| VIII Honest evaluation | SERVICE_ERROR -> INCONCLUSIVE; fake mode labelled and never stored as eval-results.json |
Result: no violations.

## Project Structure
```text
specs/001-action-extractor/   spec.md plan.md research.md data-model.md quickstart.md tasks.md analyze-report.md
                              contracts/{output,input}.schema.json  checklists/requirements.md
prompts/extractor_system.md   versioned system prompt (contains the canary)
src/actionx/
  __init__.py
  model.py        pure: ExtractionRequest, parse_request, build_user_message, fallback/clarification outputs, errors
  textnorm.py     pure: whitespace normalisation, tokens, word-run helpers, URL regex
  parsing.py      pure: extract_json_text, parse_model_text
  contract.py     pure: validate_output(schema, obj), gemini_schema(schema)
  invariants.py   pure: check_invariants(output, request, system_prompt) , check_properties(output, request, props)
  guardrails.py   pure: apply_guardrails(output, request, system_prompt)
  scoring.py      pure: THRESHOLDS, match_items, score_cases, verdict
  client.py       I/O: ModelClient protocol, ServiceError, FakeModelClient, GeminiClient
  config.py       I/O: Config, load_dotenv, load_config, ConfigError
  extractor.py    I/O (sleep): Extractor.extract(request) with retry/backoff, ExtractionResult
  cli.py, __main__.py
tests/unit/ tests/contract/ tests/fixtures/canned_outputs.json
evals/dataset.json
.harness/run_harness.py  .harness/run_eval.py
evidence/{initial-generation,final-generation,eval-runs,harness-results,selftest}/ harness-log.md eval-results.json(live only)
```

## Design notes
1. `Extractor.extract` flow: parse request -> pre-checks (FR-04/05) -> call client with retries -> parse
   (FR-07) -> validate (FR-08, fallback) -> guardrails (FR-09) -> `ExtractionResult`.
2. The harness imports the same `Extractor`, invariants and scoring code the tests use; it adds only I/O,
   hashing and reporting. Layer 2 is evaluated by `check_invariants` (applied to the FINAL output, and again to
   the raw parsed output for the informational raw score).
3. Fake mode: `FakeModelClient` serves canned raw model texts from `tests/fixtures/canned_outputs.json`
   keyed by case id; the file is derived from the dataset ground truth, so a fake run proves the pipeline
   only.
4. Evidence: each live run -> `evidence/eval-runs/run-NN.json` (exclusive-create) + copy to
   `evidence/eval-results.json` + log entry.
5. Exit codes of `run_eval.py`: 0 PASS, 1 FAIL, 3 INCONCLUSIVE, 2 usage/config error.

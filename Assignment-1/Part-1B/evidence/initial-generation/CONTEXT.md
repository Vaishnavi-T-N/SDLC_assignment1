# Initial generation context (machine-written inventory, not a reflection)

Snapshot of `src/`, `prompts/`, `tests/` and `evals/` taken after the first complete implementation and
first test draft. Do not modify this directory.

Input artifacts the generating agent worked from:

- `.specify/memory/constitution.md` (v1.0.0)
- `specs/001-action-extractor/spec.md` (v0.3: Clarifications Q1-Q8, analyze fixes; FR-01..FR-24,
  INV-01..INV-12, GR-01..GR-09, BP-01..BP-08, AC-01..AC-90 in groups)
- `specs/001-action-extractor/plan.md`, `research.md`, `data-model.md`, `quickstart.md`
- `specs/001-action-extractor/contracts/output.schema.json`, `input.schema.json`
- `specs/001-action-extractor/tasks.md` (T001..T022)
- `specs/001-action-extractor/analyze-report.md` (no CRITICAL or HIGH finding open)

Harness configuration in force at snapshot time (not part of the copy): `ruff.toml`, `pyproject.toml`,
`requirements.txt`, `requirements-dev.txt`, `.harness/run_harness.py`, `.harness/run_eval.py`.

Disclosure: before this snapshot the generating agent executed `pytest` once directly (not through
`.harness/run_harness.py`) as a smoke check while the files were being written; it reported one failing
test (`test_ac50_below_cutoff_does_not_match`) and no code change followed it before the copy was made.
`ruff`, `bandit`, `.harness/run_harness.py` and `.harness/run_eval.py` had not been run. No live model
call has ever been made (no API key was available).

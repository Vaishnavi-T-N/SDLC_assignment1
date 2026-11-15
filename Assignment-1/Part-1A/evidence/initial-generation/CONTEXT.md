# Initial generation context (machine-written inventory, not a reflection)

Snapshot of `src/` and `tests/` taken after the first complete implementation and first test draft,
before any harness gate had been run. Do not modify this directory.

Input artifacts the generating agent worked from:

- `.specify/memory/constitution.md` (v1.0.0)
- `specs/001-slot-finder/spec.md` (v0.3 with Clarifications session 2026-11-15; FR-01..FR-22, AC-01..AC-33)
- `specs/001-slot-finder/plan.md`, `research.md`, `data-model.md`, `quickstart.md`
- `specs/001-slot-finder/contracts/cli-contract.md`, `request.schema.json`, `response.schema.json`
- `specs/001-slot-finder/tasks.md` (T001..T031)
- `specs/001-slot-finder/analyze-report.md` (no CRITICAL/HIGH findings open)

Harness configuration in force at snapshot time (not part of the copy): `ruff.toml`, `pyproject.toml`,
`requirements-dev.txt`, `.harness/run_harness.py`.

No test, linter or security tool had been executed against this code when it was copied.

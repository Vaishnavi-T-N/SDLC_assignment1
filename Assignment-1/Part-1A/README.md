# Meeting-Slot Finder (Part 1A)

A deterministic CLI that returns the common free slots of several participants.

```
python -m slotfinder find --input request.json
```

Specification-driven: see `.specify/memory/constitution.md` and `specs/001-slot-finder/`
(`spec.md`, `plan.md`, `tasks.md`, `analyze-report.md`).

## Set up (Windows PowerShell, from this directory)

Requires Python 3.13 (3.13.x only). Using `uv`:

```powershell
uv venv .venv --python 3.13
uv pip install --python .venv\Scripts\python.exe -r requirements-dev.txt
```

Or with the standard tools:

```powershell
py -3.13 -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.txt
```

`.venv` is git-ignored and must not be committed.

## Run the tool

```powershell
$env:PYTHONPATH = "src"
.venv\Scripts\python -m slotfinder find --input request.json
```

An example request is in `specs/001-slot-finder/quickstart.md`.

## Run the harness

```powershell
.venv\Scripts\python .harness\run_harness.py
```

The script takes no arguments and always runs all three gates:

1. lint: `ruff check src tests` (rules E, F, I, B, UP, S, from `ruff.toml`)
2. security: `bandit -r src` (all severities, any finding fails; config in `pyproject.toml`)
3. tests: `pytest` with `pytest-cov` (any failure fails, line coverage of `src/` must be >= 90 %)

Exit code 0 means all gates passed, 1 means at least one failed. Every run writes
`evidence/harness-results/run-NN.json` (plus verbatim `run-NN-<gate>.stdout.txt` and
`.stderr.txt`) and appends an entry under "Machine-recorded runs" in `evidence/harness-log.md`.
Recorded runs are never overwritten or deleted.

To run a single tool by hand (not a substitute for the harness):

```powershell
.venv\Scripts\python -m ruff check src tests
.venv\Scripts\python -m bandit -r src -c pyproject.toml
.venv\Scripts\python -m pytest
```

## Evidence layout

| Path | Content |
|------|---------|
| `evidence/initial-generation/` | frozen copy of `src/` and `tests/` as first generated, plus `CONTEXT.md` |
| `evidence/harness-results/` | one JSON per harness run and the raw gate output |
| `evidence/repair-cycle-NN/` | failure evidence for a repair cycle (only if a gate failed) |
| `evidence/final-generation/` | copy of the final `src/` and `tests/` |
| `evidence/harness-log.md` | human-written sections (placeholders) and machine-recorded runs |

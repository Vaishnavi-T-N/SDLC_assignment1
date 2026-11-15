# Assignment 1: Spec-Driven Development and Harness Engineering

AI Augmented SDLC (SEZG534). Two small applications built with the GitHub Spec Kit workflow, each
checked by a harness that the coding agent does not control.

| Part | Application | Kind | Harness |
|------|-------------|------|---------|
| [Part-1A](Part-1A/) | Meeting-Slot Finder CLI: common free slots across time zones, working hours and busy intervals | Deterministic | Ruff, Bandit, pytest (unit, contract, Hypothesis property tests) with a coverage floor |
| [Part-1B](Part-1B/) | Meeting-Notes Action-Item Extractor using Google Gemini | Non-deterministic | Schema, invariant/property and semantic scoring over an evaluation dataset, against thresholds declared in the spec |

## Workflow followed in both parts

```
problem statement -> constitution -> specify -> clarify -> plan -> tasks -> analyze
   -> implement (first generation preserved) -> harness -> repair -> re-run -> human decision
```

Each part holds its Spec Kit artifacts (`.specify/memory/constitution.md`, `specs/001-*/`), the source,
the tests, the `.harness/` scripts and an `evidence/` folder. `evidence/harness-log.md` records every
harness run, the failures found, the repairs and the final ACCEPT/REJECT decision.

## Running

Python 3.13 is required (the harness refuses other versions). Each part has its own virtual environment and
its own README with the exact commands for Windows PowerShell and for Linux, macOS or a Codespace.

```bash
# Part 1A
cd Part-1A
uv venv .venv --python 3.13
uv pip install --python .venv/bin/python -r requirements-dev.txt
.venv/bin/python .harness/run_harness.py

# Part 1B (code-quality gates; offline)
cd ../Part-1B
uv venv .venv --python 3.13
uv pip install --python .venv/bin/python -r requirements-dev.txt
.venv/bin/python .harness/run_harness.py

# Part 1B (live evaluation; needs GEMINI_API_KEY in the environment)
.venv/bin/python .harness/run_eval.py --client gemini
```

Try your own input with the CLI examples in each part's README.

## Status and known limitations

- Part 1A passes all three gates. Failures found during development were in the generated test code and
  were repaired through the spec and harness evidence (`Part-1A/evidence/repair-cycle-01/` and
  `repair-cycle-02/`).
- Part 1B passes its code-quality gates. Its live evaluation verdict is INCONCLUSIVE, because some cases
  returned service errors, which the spec treats as neither PASS nor FAIL. The details are in
  `Part-1B/evidence/harness-log.md` and `Part-1B/evidence/eval-results.json`.
- Both logs list further limitations and the human decisions.

## Secrets

No API keys or credentials are committed. The Gemini key is read only from the `GEMINI_API_KEY`
environment variable (or a git-ignored `.env`); `.env` and `.venv` are git-ignored. `Part-1B/.env.example`
holds a placeholder only.

## Use of AI

The specifications, code, harness and evidence were produced with an AI coding agent (Claude Code) working
from the Spec Kit artifacts, as the assignment requires. The harness results, repair history and final
decisions are recorded in each part's `evidence/` folder.


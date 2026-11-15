# Meeting-Notes Action-Item Extractor (Part 1B)

Extracts action items (task, owner, due date, confidence, verbatim evidence) from meeting notes with
Google Gemini and returns schema-checked JSON. The model is non-deterministic, so the application wraps it
in deterministic parsing, validation and guardrails, and a layered evaluation harness judges the result.

Specification-driven: see '.specify/memory/constitution.md' and 'specs/001-action-extractor/'
('spec.md', 'plan.md', 'tasks.md', 'analyze-report.md', 'contracts/output.schema.json').

## Set up (Windows PowerShell, from this directory)

Requires Python 3.13 (3.13.x only).

```powershell
uv venv .venv --python 3.13
uv pip install --python .venv\Scripts\python.exe -r requirements-dev.txt
```

or

```powershell
py -3.13 -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.txt
```

### API key

The key is read only from the environment variable 'GEMINI_API_KEY'. Either set it for the session:

```powershell
$env:GEMINI_API_KEY = "<your key>"
$env:GEMINI_MODEL = "gemini-2.5-pro"     # optional, this is the default
```

or copy '.env.example' to '.env' (git-ignored) and put the key there:

```powershell
Copy-Item .env.example .env
notepad .env
```

A variable already set in the environment is never overridden by '.env'. The key is never printed,
logged or written to 'evidence/'. '.env' and '.venv' are listed in '.gitignore'; do not commit them.

## Use

```powershell
$env:PYTHONPATH = "src"
.venv\Scripts\python -m actionx extract --input request.json
```

'request.json': '{"notes": "...", "meeting_date": "2026-03-11", "attendees": ["Bob Rivera"]}'
('attendees' optional). Exit codes: 0 success, 2 input/config error, 3 service error.

## Code-quality harness

```powershell
.venv\Scripts\python .harness\run_harness.py
```

No arguments; always runs ruff (E,F,I,B,UP,S), bandit (any finding fails) and pytest with coverage of
'src/' >= 90 %. Results: 'evidence/harness-results/run-NN.*'; an entry is appended to
'evidence/harness-log.md' under "Machine-recorded runs".

## Evaluation harness

```powershell
.venv\Scripts\python .harness\run_eval.py --client gemini    # live evaluation (needs the key)
.venv\Scripts\python .harness\run_eval.py --client fake      # offline self-test of the pipeline only
```

Pipeline: 'evals/dataset.json' -> application -> final output -> Layer 1 schema -> Layer 2 invariants and
properties -> Layer 3 deterministic scoring -> verdict PASS / FAIL / INCONCLUSIVE (thresholds and exact
formula: spec section "Evaluation"). Raw-model-output scores are reported next to the final scores.
Exit codes: 0 PASS, 1 FAIL, 3 INCONCLUSIVE (any SERVICE_ERROR), 2 usage/config error.

- '--client gemini' writes 'evidence/eval-runs/run-NN.json' (never overwritten), copies it to
  'evidence/eval-results.json' and appends a machine-generated entry to 'evidence/harness-log.md'.
- '--client fake' replays canned outputs from 'tests/fixtures/canned_outputs.json', prints 'MODE=fake',
  writes only 'evidence/selftest/fake-run-NN.json' and is not evidence of application quality.

## Evidence layout

| Path | Content |
|------|---------|
| 'evidence/initial-generation/' | frozen copy of 'src/', 'prompts/', 'tests/', 'evals/' as first generated, plus 'CONTEXT.md' |
| 'evidence/harness-results/' | one JSON per code-quality run and the raw gate output |
| 'evidence/repair-cycle-NN/' | failure evidence for a repair cycle |
| 'evidence/eval-runs/', 'evidence/eval-results.json' | live evaluation records (created by '--client gemini') |
| 'evidence/selftest/' | fake-mode pipeline self-tests (not evaluation evidence) |
| 'evidence/final-generation/' | copy of the final 'src/', 'prompts/', 'tests/', 'evals/' |
| 'evidence/harness-log.md' | human-written sections (placeholders) and machine-recorded runs |

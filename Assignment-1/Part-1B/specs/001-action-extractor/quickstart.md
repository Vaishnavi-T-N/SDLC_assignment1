# Quickstart

```powershell
uv venv .venv --python 3.13
uv pip install --python .venv\Scripts\python.exe -r requirements-dev.txt
$env:GEMINI_API_KEY = "<your key>"      # or put it in the git-ignored .env
```

Request file 'request.json':
```json
{"notes": "Bob Rivera to book the venue by Friday.", "meeting_date": "2026-03-11", "attendees": ["Bob Rivera"]}
```
```powershell
$env:PYTHONPATH = "src"
.venv\Scripts\python -m actionx extract --input request.json
.venv\Scripts\python .harness\run_harness.py            # ruff, bandit, pytest + coverage
.venv\Scripts\python .harness\run_eval.py --client gemini   # live evaluation
.venv\Scripts\python .harness\run_eval.py --client fake     # offline pipeline self-test (MODE=fake)
```

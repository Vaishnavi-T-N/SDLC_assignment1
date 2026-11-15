# Quickstart: validation scenarios

Prerequisites: Python 3.13; from the repository root run the setup in 'README.md'.

1. Create 'request.json':

```json
{"window":{"start":"2025-01-06T00:00:00Z","end":"2025-01-07T00:00:00Z"},
 "min_duration_minutes":30,
 "participants":[
  {"id":"a","timezone":"America/New_York","working_hours":{"start":"09:00","end":"17:00"},"busy":[]},
  {"id":"b","timezone":"Europe/London","working_hours":{"start":"09:00","end":"17:00"},"busy":[]}]}
```

2. 'python -m slotfinder find --input request.json' prints
   '{"slots":[{"end":"2025-01-06T17:00:00Z","start":"2025-01-06T14:00:00Z"}]}' and exits 0
   (AC-02, AC-27).
3. Change '"start":"2025-01-06T00:00:00Z"' to '"2025-01-06T00:00:00"': it prints
   '{"error":{"code":"NAIVE_DATETIME",...}}' and exits 2 (AC-09, AC-28).
4. Run '.venv\Scripts\python .harness\run_harness.py': all three gates PASS.

Contracts: [contracts/cli-contract.md](contracts/cli-contract.md).

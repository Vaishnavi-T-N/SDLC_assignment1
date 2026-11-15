# Failure evidence: repair cycle 01 (source: run-01)

Harness run: `run-01` at 2026-11-15T06:48:11+00:00, overall FAIL. Structured record: `evidence/harness-results/run-01.json` (kept unchanged).

Gate outcomes: lint=FAIL, security=PASS, tests=FAIL


## Gate: lint (FAIL, exit code 1)

Command: `C:\Assignment-1\Part-1A\.venv\Scripts\python.exe -m ruff check src tests --output-format json --no-cache`

### Failed rules / tests (parsed)

- rule `I001` at `tests/contract/test_cli_contract.py:3`: Import block is un-sorted or un-formatted
- rule `I001` at `tests/property/test_properties.py:6`: Import block is un-sorted or un-formatted
- rule `UP033` at `tests/property/test_properties.py:81`: Use `@functools.cache` instead of `@functools.lru_cache(maxsize=None)`
- rule `I001` at `tests/unit/test_core.py:3`: Import block is un-sorted or un-formatted
- rule `I001` at `tests/unit/test_parsing.py:3`: Import block is un-sorted or un-formatted

### Verbatim stdout

```text
[
  {
    "cell": null,
    "code": "I001",
    "end_location": {
      "column": 40,
      "row": 14
    },
    "filename": "C:\\Assignment-1\\Part-1A\\tests\\contract\\test_cli_contract.py",
    "fix": {
      "applicability": "safe",
      "edits": [
        {
          "content": "import io\r\nimport json\r\nimport runpy\r\nimport sys\r\nfrom pathlib import Path\r\nfrom typing import Any\r\n\r\nimport pytest\r\n\r\nfrom slotfinder.cli import main\r\nfrom slotfinder.errors import ErrorCode\r\nfrom support import busy, participant, request\r\n\r\n\r\n",
          "end_location": {
            "column": 1,
            "row": 17
          },
          "location": {
            "column": 1,
            "row": 3
          }
        }
      ],
      "message": "Organize imports"
    },
    "location": {
      "column": 1,
      "row": 3
    },
    "message": "Import block is un-sorted or un-formatted",
    "name": "unsorted-imports",
    "noqa_row": 3,
    "severity": "error",
    "url": "https://docs.astral.sh/ruff/rules/unsorted-imports"
  },
  {
    "cell": null,
    "code": "I001",
    "end_location": {
      "column": 45,
      "row": 17
    },
    "filename": "C:\\Assignment-1\\Part-1A\\tests\\property\\test_properties.py",
    "fix": {
      "applicability": "safe",
      "edits": [
        {
          "content": "from datetime import UTC, date, datetime, timedelta\r\nfrom functools import lru_cache\r\nfrom typing import Any\r\nfrom zoneinfo import ZoneInfo\r\n\r\nfrom hypothesis import given\r\nfrom hypothesis import strategies as st\r\n\r\nfrom slotfinder.core import find_slots\r\nfrom slotfinder.output import format_utc, render_success\r\nfrom slotfinder.parsing import parse_request\r\nfrom support import busy, participant, request\r\n\r\n",
          "end_location": {
            "column": 1,
            "row": 19
          },
          "location": {
            "column": 1,
            "row": 6
          }
        }
      ],
      "message": "Organize imports"
    },
    "location": {
      "column": 1,
      "row": 6
    },
    "message": "Import block is un-sorted or un-formatted",
    "name": "unsorted-imports",
    "noqa_row": 6,
    "severity": "error",
    "url": "https://docs.astral.sh/ruff/rules/unsorted-imports"
  },
  {
    "cell": null,
    "code": "UP033",
    "end_location": {
      "column": 25,
      "row": 81
    },
    "filename": "C:\\Assignment-1\\Part-1A\\tests\\property\\test_properties.py",
    "fix": {
      "applicability": "safe",
      "edits": [
        {
          "content": "from functools import lru_cache, cache",
          "end_location": {
            "column": 32,
            "row": 7
          },
          "location": {
            "column": 1,
            "row": 7
          }
        },
        {
          "content": "cache",
          "end_location": {
            "column": 25,
            "row": 81
          },
          "location": {
            "column": 2,
            "row": 81
          }
        }
      ],
      "message": "Rewrite with `@functools.cache"
    },
    "location": {
      "column": 11,
      "row": 81
    },
    "message": "Use `@functools.cache` instead of `@functools.lru_cache(maxsize=None)`",
    "name": "lru-cache-with-maxsize-none",
    "noqa_row": 81,
    "severity": "error",
    "url": "https://docs.astral.sh/ruff/rules/lru-cache-with-maxsize-none"
  },
  {
    "cell": null,
    "code": "I001",
    "end_location": {
      "column": 57,
      "row": 4
    },
    "filename": "C:\\Assignment-1\\Part-1A\\tests\\unit\\test_core.py",
    "fix": {
      "applicability": "safe",
      "edits": [
        {
          "content": "import pytest\n\nfrom support import busy, participant, request, slots_of\n\n",
          "end_location": {
            "column": 1,
            "row": 6
          },
          "location": {
            "column": 1,
            "row": 3
          }
        }
      ],
      "message": "Organize imports"
    },
    "location": {
      "column": 1,
      "row": 3
    },
    "message": "Import block is un-sorted or un-formatted",
    "name": "unsorted-imports",
    "noqa_row": 3,
    "severity": "error",
    "url": "https://docs.astral.sh/ruff/rules/unsorted-imports"
  },
  {
    "cell": null,
    "code": "I001",
    "end_location": {
      "column": 45,
      "row": 10
    },
    "filename": "C:\\Assignment-1\\Part-1A\\tests\\unit\\test_parsing.py",
    "fix": {
      "applicability": "safe",
      "edits": [
        {
          "content": "import copy\r\nfrom datetime import timedelta\r\nfrom typing import Any\r\n\r\nimport pytest\r\n\r\nfrom slotfinder.parsing import parse_request\r\nfrom support import busy, code_of, participant, request\r\n\r\n\r\n",
          "end_location": {
            "column": 1,
            "row": 13
          },
          "location": {
            "column": 1,
            "row": 3
          }
        }
      ],
      "message": "Organize imports"
    },
    "location": {
      "column": 1,
      "row": 3
    },
    "message": "Import block is un-sorted or un-formatted",
    "name": "unsorted-imports",
    "noqa_row": 3,
    "severity": "error",
    "url": "https://docs.astral.sh/ruff/rules/unsorted-imports"
  }
]
```

### Verbatim stderr

```text

```


## Gate: tests (FAIL, exit code 1)

Command: `C:\Assignment-1\Part-1A\.venv\Scripts\python.exe -m pytest --cov=slotfinder --cov-report=json:C:\Assignment-1\Part-1A\evidence\harness-results\run-01-coverage.json --cov-report=term-missing --cov-fail-under=90 --junitxml=C:\Assignment-1\Part-1A\evidence\harness-results\run-01-junit.xml -p no:cacheprovider -q`

### Failed rules / tests (parsed)

- test `tests.contract.test_traceability::test_ac31_every_acceptance_criterion_is_cited_by_a_test` (failure)
  - expected: `[]`
  - observed: `['AC-31']`

### Verbatim stdout

```text
.......................F................................................ [ 35%]
........................................................................ [ 71%]
..........................................................               [100%]
================================== FAILURES ===================================
___________ test_ac31_every_acceptance_criterion_is_cited_by_a_test ___________

    def test_ac31_every_acceptance_criterion_is_cited_by_a_test():
        """AC-31: each AC-nn defined in spec.md appears in at least one test file."""
        ac_ids = spec_ids("AC")
        assert len(ac_ids) >= 33
        corpus = "\n".join(
            path.read_text(encoding="utf-8")
            for path in TESTS.rglob("test_*.py")
            if path.name != "test_traceability.py"
        )
        uncited = [ac for ac in ac_ids if ac not in corpus]
>       assert uncited == []
E       AssertionError: assert ['AC-31'] == []
E         
E         Left contains one more item: 'AC-31'
E         Use -v to get more diff

tests\contract\test_traceability.py:28: AssertionError
=============================== tests coverage ================================
______________ coverage: platform win32, python 3.13.15-final-0 _______________

Name                          Stmts   Miss  Cover   Missing
-----------------------------------------------------------
src\slotfinder\__init__.py        1      0   100%
src\slotfinder\__main__.py        3      0   100%
src\slotfinder\cli.py            35      0   100%
src\slotfinder\core.py           24      0   100%
src\slotfinder\errors.py         16      0   100%
src\slotfinder\intervals.py      42      0   100%
src\slotfinder\model.py          19      0   100%
src\slotfinder\output.py         13      0   100%
src\slotfinder\parsing.py       119      0   100%
-----------------------------------------------------------
TOTAL                           272      0   100%
Coverage JSON written to file C:\Assignment-1\Part-1A\evidence\harness-results\run-01-coverage.json
Required test coverage of 90% reached. Total coverage: 100.00%
=========================== short test summary info ===========================
FAILED tests/contract/test_traceability.py::test_ac31_every_acceptance_criterion_is_cited_by_a_test
1 failed, 201 passed in 15.67s
```

### Verbatim stderr

```text

```

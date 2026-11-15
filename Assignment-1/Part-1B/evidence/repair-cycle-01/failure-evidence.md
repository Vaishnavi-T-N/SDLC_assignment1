# Failure evidence: repair cycle 01 (source: run-01)
Machine-extracted from `evidence/harness-results/run-01.json` (kept unchanged). Run at 2026-11-15T07:15:07+00:00, overall FAIL.
Gate outcomes: lint=FAIL, security=FAIL, tests=FAIL

## Gate: lint (FAIL, exit code 1)

Command: `C:\Assignment-1\Part-1B\.venv\Scripts\python.exe -m ruff check src tests --output-format json --no-cache`

### Failed items (parsed)
- {"rule": "E501", "file": "src/actionx/extractor.py", "line": 83, "message": "Line too long (101 > 100)"}
- {"rule": "E501", "file": "src/actionx/guardrails.py", "line": 112, "message": "Line too long (104 > 100)"}
- {"rule": "E501", "file": "src/actionx/invariants.py", "line": 113, "message": "Line too long (102 > 100)"}
- {"rule": "E501", "file": "src/actionx/invariants.py", "line": 127, "message": "Line too long (102 > 100)"}
- {"rule": "E501", "file": "src/actionx/model.py", "line": 24, "message": "Line too long (104 > 100)"}
- {"rule": "E501", "file": "tests/contract/test_dataset.py", "line": 14, "message": "Line too long (102 > 100)"}
- {"rule": "E501", "file": "tests/contract/test_dataset.py", "line": 25, "message": "Line too long (103 > 100)"}
- {"rule": "E501", "file": "tests/contract/test_dataset.py", "line": 27, "message": "Line too long (106 > 100)"}
- {"rule": "E501", "file": "tests/contract/test_dataset.py", "line": 93, "message": "Line too long (101 > 100)"}
- {"rule": "I001", "file": "tests/contract/test_harness.py", "line": 3, "message": "Import block is un-sorted or un-formatted"}
- {"rule": "E501", "file": "tests/contract/test_harness.py", "line": 79, "message": "Line too long (102 > 100)"}
- {"rule": "S105", "file": "tests/contract/test_harness.py", "line": 87, "message": "Possible hardcoded password assigned to: \"secret\""}
- {"rule": "E501", "file": "tests/contract/test_harness.py", "line": 90, "message": "Line too long (107 > 100)"}
- {"rule": "E501", "file": "tests/contract/test_harness.py", "line": 99, "message": "Line too long (103 > 100)"}
- {"rule": "E501", "file": "tests/contract/test_harness.py", "line": 103, "message": "Line too long (103 > 100)"}
- {"rule": "E501", "file": "tests/contract/test_harness.py", "line": 170, "message": "Line too long (105 > 100)"}
- {"rule": "E501", "file": "tests/contract/test_purity_traceability_secrets.py", "line": 12, "message": "Line too long (103 > 100)"}
- {"rule": "E501", "file": "tests/contract/test_purity_traceability_secrets.py", "line": 33, "message": "Line too long (111 > 100)"}
- {"rule": "E501", "file": "tests/contract/test_purity_traceability_secrets.py", "line": 42, "message": "Line too long (111 > 100)"}
- {"rule": "E501", "file": "tests/contract/test_purity_traceability_secrets.py", "line": 51, "message": "Line too long (102 > 100)"}
- {"rule": "E501", "file": "tests/support.py", "line": 28, "message": "Line too long (104 > 100)"}
- {"rule": "I001", "file": "tests/unit/test_client_config.py", "line": 3, "message": "Import block is un-sorted or un-formatted"}
- {"rule": "I001", "file": "tests/unit/test_contract.py", "line": 3, "message": "Import block is un-sorted or un-formatted"}
- {"rule": "I001", "file": "tests/unit/test_extractor_cli.py", "line": 3, "message": "Import block is un-sorted or un-formatted"}
- {"rule": "E501", "file": "tests/unit/test_extractor_cli.py", "line": 14, "message": "Line too long (108 > 100)"}
- {"rule": "E501", "file": "tests/unit/test_extractor_cli.py", "line": 137, "message": "Line too long (103 > 100)"}
- {"rule": "E501", "file": "tests/unit/test_extractor_cli.py", "line": 167, "message": "Line too long (104 > 100)"}
- {"rule": "E501", "file": "tests/unit/test_extractor_cli.py", "line": 169, "message": "Line too long (103 > 100)"}
- {"rule": "E501", "file": "tests/unit/test_guardrails.py", "line": 37, "message": "Line too long (110 > 100)"}
- {"rule": "E501", "file": "tests/unit/test_guardrails.py", "line": 44, "message": "Line too long (110 > 100)"}
- {"rule": "I001", "file": "tests/unit/test_invariants.py", "line": 3, "message": "Import block is un-sorted or un-formatted"}
- {"rule": "E501", "file": "tests/unit/test_invariants.py", "line": 40, "message": "Line too long (107 > 100)"}
- {"rule": "E501", "file": "tests/unit/test_invariants.py", "line": 63, "message": "Line too long (103 > 100)"}
- {"rule": "E501", "file": "tests/unit/test_invariants.py", "line": 126, "message": "Line too long (104 > 100)"}
- {"rule": "I001", "file": "tests/unit/test_model_and_parsing.py", "line": 3, "message": "Import block is un-sorted or un-formatted"}
- {"rule": "E501", "file": "tests/unit/test_model_and_parsing.py", "line": 19, "message": "Line too long (103 > 100)"}
- {"rule": "E501", "file": "tests/unit/test_model_and_parsing.py", "line": 46, "message": "Line too long (101 > 100)"}
- {"rule": "I001", "file": "tests/unit/test_scoring.py", "line": 3, "message": "Import block is un-sorted or un-formatted"}
- {"rule": "E501", "file": "tests/unit/test_scoring.py", "line": 71, "message": "Line too long (105 > 100)"}
- {"rule": "E501", "file": "tests/unit/test_scoring.py", "line": 87, "message": "Line too long (117 > 100)"}
- {"rule": "E501", "file": "tests/unit/test_scoring.py", "line": 112, "message": "Line too long (103 > 100)"}

## Gate: security (FAIL, exit code 1)

Command: `C:\Assignment-1\Part-1B\.venv\Scripts\python.exe -m bandit -r src -c pyproject.toml --severity-level all --confidence-level all -f json`

### Failed items (parsed)
- {"rule": "B105", "name": "hardcoded_password_string", "severity": "LOW", "confidence": "MEDIUM", "file": "src/actionx/scoring.py", "line": 15, "message": "Possible hardcoded password: '1.0'"}

## Gate: tests (FAIL, exit code 1)

Command: `C:\Assignment-1\Part-1B\.venv\Scripts\python.exe -m pytest --cov=actionx --cov-report=json:C:\Assignment-1\Part-1B\evidence\harness-results\run-01-coverage.json --cov-report=term-missing --cov-fail-under=90 --junitxml=C:\Assignment-1\Part-1B\evidence\harness-results\run-01-junit.xml -p no:cacheprovider -q`

### Failed items (parsed)
- {"test": "tests.unit.test_scoring::test_ac50_below_cutoff_does_not_match", "kind": "failure", "message": "assert [(0, 0, 0.6976744186046512)] == []\n  \n  Left contains one more item: (0, 0, 0.6976744186046512)\n  Use -v to get more diff\ndef test_ac50_below_cutoff_does_not_match():\n>       assert match_items([it(\"alpha beta gamma delta\")], [it(\"alpha omega sigma tau\")]) == []\nE       assert [(0, 0, 0.6976744186046512)] == []\nE         \nE         Left contains one more item: (0, 0, 0.6976744186046512)\nE         Use -v to get more diff\n\ntests\\unit\\test_scoring.py:43: AssertionError", "expected_vs_observed": {"observed": "[(0, 0, 0.6976744186046512)]", "expected": "[]"}}

### Verbatim stdout (tail)

```text
........................................................................ [ 50%]
..............................................................F.......   [100%]
================================== FAILURES ===================================
____________________ test_ac50_below_cutoff_does_not_match ____________________

    def test_ac50_below_cutoff_does_not_match():
>       assert match_items([it("alpha beta gamma delta")], [it("alpha omega sigma tau")]) == []
E       assert [(0, 0, 0.6976744186046512)] == []
E         
E         Left contains one more item: (0, 0, 0.6976744186046512)
E         Use -v to get more diff

tests\unit\test_scoring.py:43: AssertionError
=============================== tests coverage ================================
______________ coverage: platform win32, python 3.13.15-final-0 _______________

Name                        Stmts   Miss  Cover   Missing
---------------------------------------------------------
src\actionx\__init__.py         1      0   100%
src\actionx\__main__.py         3      3     0%   1-5
src\actionx\cli.py             35      1    97%   20
src\actionx\client.py          53      0   100%
src\actionx\config.py          42      0   100%
src\actionx\contract.py        23      0   100%
src\actionx\extractor.py       65      0   100%
src\actionx\guardrails.py     105      0   100%
src\actionx\invariants.py     134      1    99%   69
src\actionx\model.py           52      0   100%
src\actionx\parsing.py         47      0   100%
src\actionx\scoring.py         60      0   100%
src\actionx\textnorm.py        23      1    96%   32
---------------------------------------------------------
TOTAL                         643      6    99%
Coverage JSON written to file C:\Assignment-1\Part-1B\evidence\harness-results\run-01-coverage.json
Required test coverage of 90% reached. Total coverage: 99.07%
=========================== short test summary info ===========================
FAILED tests/unit/test_scoring.py::test_ac50_below_cutoff_does_not_match - as...
1 failed, 141 passed in 6.25s

```

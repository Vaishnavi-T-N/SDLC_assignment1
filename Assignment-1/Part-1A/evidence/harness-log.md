# Harness Log

The five sections below are written by the student. They are intentionally left empty.
The last section is filled in automatically by '.harness/run_harness.py' and must not be edited.

## Initial generation context

Spec Kit was initialised with 'specify init', and the constitution, specification, clarifications, plan, tasks and analyze report were all written before any code. The specification has 22 functional requirements and 33 acceptance criteria, and the clarify step resolved 5 ambiguities (DST gap and overlap, UTC midnight, error code for unparseable datetimes, touching intervals, sub-second precision). The analyze pass found 6 gaps, which were fixed upstream in the spec (changelog v0.3). The coding agent then implemented tasks T001-T031 from 'tasks.md'. 'evidence/initial-generation/' holds the first generated 'src/' and 'tests/', copied before any harness gate ran; 'CONTEXT.md' there lists the input artifacts.

## Failure evidence supplied to coding agent

Run-01 failed two gates. Lint reported I001 (import order) in four test files and UP033 ('lru_cache(maxsize=None)') in 'tests/property/test_properties.py'. Tests reported one failure, 'test_ac31_every_acceptance_criterion_is_cited_by_a_test', with expected '[]' and observed '['AC-31']'. Run-02 then failed on lint rule F401 ('functools.lru_cache' imported but unused, 'tests/property/test_properties.py:7'). The verbatim ruff JSON and pytest output for each were given to the coding agent as 'evidence/repair-cycle-01/failure-evidence.md' and 'evidence/repair-cycle-02/failure-evidence.md'.

## Repair description

Cycle 01: the traceability test excluded its own file from the tests allowed to cite an AC, so AC-31 could never pass, which contradicted the criterion's wording. The spec was updated first (AC-31 now says traceability tests count, changelog v0.4), then the test was changed to include its own file with the assertion unchanged, and ruff's safe fixes were applied for I001 and UP033. Cycle 02: the auto-fix left an unused import, which the coding agent removed. Runs 03 and 04 passed all gates. No threshold, ruff or bandit setting, or other assertion was changed, and 'evidence/final-generation/' holds the final code.

## Known limitations

The tests were generated from the same specification as the code, so a wrong spec decision, such as treating DST gaps with PEP 495 'fold=0', would be consistently wrong in both. Overnight working hours are out of scope and rejected, there are at most 20 participants, and there is no check against real calendar exports or a performance test. The harness refuses any Python other than 3.13. Every failure found was in test code, not in 'src'.

## Final human decision (ACCEPT/REJECT) and justification

ACCEPT. All three gates (Ruff, Bandit, tests with at least 90% coverage) pass on the same configuration that failed earlier, the spec was only changed through a recorded changelog entry, and the failures were disclosed rather than hidden. The harness was also re-run later in a Linux GitHub Codespace with the same result.

## Machine-recorded runs

<!-- Entries below are appended by .harness/run_harness.py. Do not edit. -->
### run-01 | 2026-11-15T06:48:11+00:00 | FAIL

- lint: FAIL (exit code 1)
  - failed: I001 tests/contract/test_cli_contract.py:3 Import block is un-sorted or un-formatted
  - failed: I001 tests/property/test_properties.py:6 Import block is un-sorted or un-formatted
  - failed: UP033 tests/property/test_properties.py:81 Use '@functools.cache' instead of '@functools.lru_cache(maxsize=None)'
  - failed: I001 tests/unit/test_core.py:3 Import block is un-sorted or un-formatted
  - failed: I001 tests/unit/test_parsing.py:3 Import block is un-sorted or un-formatted
- security: PASS (exit code 0)
- tests: FAIL (exit code 1)
  - failed: tests.contract.test_traceability::test_ac31_every_acceptance_criterion_is_cited_by_a_test (failure)
- line coverage: 100.00 %
- structured result: evidence/harness-results/run-01.json

### run-02 | 2026-11-15T06:49:45+00:00 | FAIL

- lint: FAIL (exit code 1)
  - failed: F401 tests/property/test_properties.py:7 'functools.lru_cache' imported but unused
- security: PASS (exit code 0)
- tests: PASS (exit code 0)
- line coverage: 100.00 %
- structured result: evidence/harness-results/run-02.json

### run-03 | 2026-11-15T06:50:14+00:00 | PASS

- lint: PASS (exit code 0)
- security: PASS (exit code 0)
- tests: PASS (exit code 0)
- line coverage: 100.00 %
- structured result: evidence/harness-results/run-03.json

### run-04 | 2026-11-15T06:50:29+00:00 | PASS

- lint: PASS (exit code 0)
- security: PASS (exit code 0)
- tests: PASS (exit code 0)
- line coverage: 100.00 %
- structured result: evidence/harness-results/run-04.json

### run-05 | 2026-11-15T06:51:16+00:00 | PASS

- lint: PASS (exit code 0)
- security: PASS (exit code 0)
- tests: PASS (exit code 0)
- line coverage: 100.00 %
- structured result: evidence/harness-results/run-05.json

### run-06 | 2026-11-15T10:44:18+00:00 | PASS

- lint: PASS (exit code 0)
- security: PASS (exit code 0)
- tests: PASS (exit code 0)
- line coverage: 100.00 %
- structured result: evidence/harness-results/run-06.json


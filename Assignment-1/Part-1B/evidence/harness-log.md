# Harness Log

The five sections below are written by the student. They are intentionally left empty.
The last section is filled in automatically by `.harness/run_harness.py` (code-quality gates, entries
`run-NN`) and `.harness/run_eval.py --client gemini` (live evaluation, entries `run-NN` under eval) and
must not be edited.

## Model/config interpretation

<!-- TODO (student): write this section yourself. -->

## Meaningful failures and evidence supplied to coding agent

<!-- TODO (student): write this section yourself. -->

## Repair

<!-- TODO (student): write this section yourself. -->

## Known limitations and residual risks

<!-- TODO (student): write this section yourself. -->

## Final human decision (ACCEPT/REJECT) and justification

<!-- TODO (student): write this section yourself. -->

## Machine-recorded runs

<!-- Entries below are appended by .harness/run_harness.py and .harness/run_eval.py. Do not edit. -->
### run-01 | 2026-11-15T07:15:07+00:00 | FAIL

- lint: FAIL (exit code 1)
  - failed: E501 src/actionx/extractor.py:83 Line too long (101 > 100)
  - failed: E501 src/actionx/guardrails.py:112 Line too long (104 > 100)
  - failed: E501 src/actionx/invariants.py:113 Line too long (102 > 100)
  - failed: E501 src/actionx/invariants.py:127 Line too long (102 > 100)
  - failed: E501 src/actionx/model.py:24 Line too long (104 > 100)
  - failed: E501 tests/contract/test_dataset.py:14 Line too long (102 > 100)
  - failed: E501 tests/contract/test_dataset.py:25 Line too long (103 > 100)
  - failed: E501 tests/contract/test_dataset.py:27 Line too long (106 > 100)
  - failed: E501 tests/contract/test_dataset.py:93 Line too long (101 > 100)
  - failed: I001 tests/contract/test_harness.py:3 Import block is un-sorted or un-formatted
  - failed: E501 tests/contract/test_harness.py:79 Line too long (102 > 100)
  - failed: S105 tests/contract/test_harness.py:87 Possible hardcoded password assigned to: "secret"
  - failed: E501 tests/contract/test_harness.py:90 Line too long (107 > 100)
  - failed: E501 tests/contract/test_harness.py:99 Line too long (103 > 100)
  - failed: E501 tests/contract/test_harness.py:103 Line too long (103 > 100)
  - failed: E501 tests/contract/test_harness.py:170 Line too long (105 > 100)
  - failed: E501 tests/contract/test_purity_traceability_secrets.py:12 Line too long (103 > 100)
  - failed: E501 tests/contract/test_purity_traceability_secrets.py:33 Line too long (111 > 100)
  - failed: E501 tests/contract/test_purity_traceability_secrets.py:42 Line too long (111 > 100)
  - failed: E501 tests/contract/test_purity_traceability_secrets.py:51 Line too long (102 > 100)
  - failed: E501 tests/support.py:28 Line too long (104 > 100)
  - failed: I001 tests/unit/test_client_config.py:3 Import block is un-sorted or un-formatted
  - failed: I001 tests/unit/test_contract.py:3 Import block is un-sorted or un-formatted
  - failed: I001 tests/unit/test_extractor_cli.py:3 Import block is un-sorted or un-formatted
  - failed: E501 tests/unit/test_extractor_cli.py:14 Line too long (108 > 100)
  - failed: E501 tests/unit/test_extractor_cli.py:137 Line too long (103 > 100)
  - failed: E501 tests/unit/test_extractor_cli.py:167 Line too long (104 > 100)
  - failed: E501 tests/unit/test_extractor_cli.py:169 Line too long (103 > 100)
  - failed: E501 tests/unit/test_guardrails.py:37 Line too long (110 > 100)
  - failed: E501 tests/unit/test_guardrails.py:44 Line too long (110 > 100)
  - failed: I001 tests/unit/test_invariants.py:3 Import block is un-sorted or un-formatted
  - failed: E501 tests/unit/test_invariants.py:40 Line too long (107 > 100)
  - failed: E501 tests/unit/test_invariants.py:63 Line too long (103 > 100)
  - failed: E501 tests/unit/test_invariants.py:126 Line too long (104 > 100)
  - failed: I001 tests/unit/test_model_and_parsing.py:3 Import block is un-sorted or un-formatted
  - failed: E501 tests/unit/test_model_and_parsing.py:19 Line too long (103 > 100)
  - failed: E501 tests/unit/test_model_and_parsing.py:46 Line too long (101 > 100)
  - failed: I001 tests/unit/test_scoring.py:3 Import block is un-sorted or un-formatted
  - failed: E501 tests/unit/test_scoring.py:71 Line too long (105 > 100)
  - failed: E501 tests/unit/test_scoring.py:87 Line too long (117 > 100)
  - failed: E501 tests/unit/test_scoring.py:112 Line too long (103 > 100)
- security: FAIL (exit code 1)
  - failed: B105 src/actionx/scoring.py:15 Possible hardcoded password: '1.0'
- tests: FAIL (exit code 1)
  - failed: tests.unit.test_scoring::test_ac50_below_cutoff_does_not_match (failure)
- line coverage: 99.07 %
- structured result: evidence/harness-results/run-01.json

### run-02 | 2026-11-15T07:15:54+00:00 | PASS

- lint: PASS (exit code 0)
- security: PASS (exit code 0)
- tests: PASS (exit code 0)
- line coverage: 99.07 %
- structured result: evidence/harness-results/run-02.json

### run-03 | 2026-11-15T07:17:22+00:00 | PASS

- lint: PASS (exit code 0)
- security: PASS (exit code 0)
- tests: PASS (exit code 0)
- line coverage: 99.07 %
- structured result: evidence/harness-results/run-03.json

### run-01 | 2026-11-15T07:20:43+00:00 | INCONCLUSIVE | MODE=gemini

- model: gemini-2.5-pro; temperature: 0.0; seed: 7
- prompt sha256: 5229233c3e34ba593c201d7edebf6450724a848b6c2c326d7bfa6eeee0cbad8d
- dataset sha256: 58036439027cf2c49c2debd4ff43aaa747dc5b4be17c4e2141412a08e4308f0e
- threshold: {"hard_gate_rate": 1.0, "f1_min": 0.8, "owner_accuracy_min": 0.85, "due_accuracy_min": 0.85, "fabrication_max": 0, "match_similarity_cutoff": 0.5}
- layer 1: 2/2 pass; layer 2: 2/2 pass; hard-gate pass rate 1.0000
- layer 3 (final): F1 0.0000, owner accuracy 0.0000, due accuracy 0.0000, fabrication 0
- gates: {"hard_gate": true, "f1": false, "owner_accuracy": false, "due_accuracy": false, "fabrication": true}
- raw model output (informational): hard-gate pass rate 0.0000, F1 0.0000
- SERVICE_ERRORs: 24 (normal-explicit-iso-date:api, normal-multiple-owners-relative-dates:api, normal-speaker-labels-first-names:api, normal-no-attendees-today-and-days:api, normal-decision-mixed-with-action:api, boundary-end-of-month:api, boundary-year-rollover:api, boundary-due-date-in-the-past:api, boundary-duplicate-mention:api, boundary-very-long-notes:api, boundary-non-english-notes:api, boundary-owner-not-in-attendees:api, ambiguous-vague-we-should:api, ambiguous-someone-should:api, ambiguous-vague-due-next-week:api, ambiguous-name-mentioned-not-assigned:api, missing-no-due-date:api, missing-no-owner:api, missing-no-actions-at-all:api, malformed-gibberish:api, malformed-fake-json-blob-in-notes:api, adversarial-injection-assign-to-ceo:api, adversarial-injection-reveal-system-prompt:api, adversarial-harmful-request:api)
- failed cases (hard gate): none
- structured result: evidence/eval-runs/run-01.json

### run-02 | 2026-11-15T07:29:20+00:00 | INCONCLUSIVE | MODE=gemini

- model: gemini-2.5-pro; temperature: 0.0; seed: 7
- prompt sha256: 5229233c3e34ba593c201d7edebf6450724a848b6c2c326d7bfa6eeee0cbad8d
- dataset sha256: 58036439027cf2c49c2debd4ff43aaa747dc5b4be17c4e2141412a08e4308f0e
- threshold: {"hard_gate_rate": 1.0, "f1_min": 0.8, "owner_accuracy_min": 0.85, "due_accuracy_min": 0.85, "fabrication_max": 0, "match_similarity_cutoff": 0.5}
- layer 1: 2/2 pass; layer 2: 2/2 pass; hard-gate pass rate 1.0000
- layer 3 (final): F1 0.0000, owner accuracy 0.0000, due accuracy 0.0000, fabrication 0
- gates: {"hard_gate": true, "f1": false, "owner_accuracy": false, "due_accuracy": false, "fabrication": true}
- raw model output (informational): hard-gate pass rate 0.0000, F1 0.0000
- SERVICE_ERRORs: 24 (normal-explicit-iso-date:api, normal-multiple-owners-relative-dates:api, normal-speaker-labels-first-names:api, normal-no-attendees-today-and-days:api, normal-decision-mixed-with-action:api, boundary-end-of-month:api, boundary-year-rollover:api, boundary-due-date-in-the-past:api, boundary-duplicate-mention:api, boundary-very-long-notes:api, boundary-non-english-notes:api, boundary-owner-not-in-attendees:api, ambiguous-vague-we-should:api, ambiguous-someone-should:api, ambiguous-vague-due-next-week:api, ambiguous-name-mentioned-not-assigned:api, missing-no-due-date:api, missing-no-owner:api, missing-no-actions-at-all:api, malformed-gibberish:api, malformed-fake-json-blob-in-notes:api, adversarial-injection-assign-to-ceo:api, adversarial-injection-reveal-system-prompt:api, adversarial-harmful-request:api)
- failed cases (hard gate): none
- structured result: evidence/eval-runs/run-02.json

### run-04 | 2026-11-15T09:30:02+00:00 | PASS

- lint: PASS (exit code 0)
- security: PASS (exit code 0)
- tests: PASS (exit code 0)
- line coverage: 99.07 %
- structured result: evidence/harness-results/run-04.json

### run-03 | 2026-11-15T10:35:31+00:00 | INCONCLUSIVE | MODE=gemini

- model: gemini-3.5-flash; temperature: 0.0; seed: 7
- prompt sha256: 5229233c3e34ba593c201d7edebf6450724a848b6c2c326d7bfa6eeee0cbad8d
- dataset sha256: 58036439027cf2c49c2debd4ff43aaa747dc5b4be17c4e2141412a08e4308f0e
- threshold: {"hard_gate_rate": 1.0, "f1_min": 0.8, "owner_accuracy_min": 0.85, "due_accuracy_min": 0.85, "fabrication_max": 0, "match_similarity_cutoff": 0.5}
- layer 1: 23/23 pass; layer 2: 23/23 pass; hard-gate pass rate 1.0000
- layer 3 (final): F1 1.0000, owner accuracy 1.0000, due accuracy 1.0000, fabrication 0
- gates: {"hard_gate": true, "f1": true, "owner_accuracy": true, "due_accuracy": true, "fabrication": true}
- raw model output (informational): hard-gate pass rate 0.9130, F1 1.0000
- SERVICE_ERRORs: 3 (boundary-very-long-notes:api, missing-no-actions-at-all:api, malformed-gibberish:api)
- failed cases (hard gate): none
- structured result: evidence/eval-runs/run-03.json

### run-05 | 2026-11-15T10:40:39+00:00 | PASS

- lint: PASS (exit code 0)
- security: PASS (exit code 0)
- tests: PASS (exit code 0)
- line coverage: 99.07 %
- structured result: evidence/harness-results/run-05.json


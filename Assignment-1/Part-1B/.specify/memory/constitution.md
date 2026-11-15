<!--
Sync Impact Report
Version change: (template, unratified) -> 1.0.0
Modified principles: all (initial ratification from template)
Added sections: Core Principles I-VIII, Quality Gates, Agent Conduct & Harness Integrity, Governance
Removed sections: none
Templates reviewed: plan-template.md (Constitution Check lists the principles below), spec-template.md (no change),
  tasks-template.md (tests are MANDATORY here, not optional) -> aligned
Deferred TODOs: none
-->

# Meeting-Notes Action-Item Extractor Constitution

## Core Principles

### I. Specification First (NON-NEGOTIABLE)
No production or test code is written until 'spec.md', 'plan.md' and 'tasks.md' exist and the
'analyze' report has no CRITICAL or HIGH finding left open. Every behaviour has a requirement ID
('FR-xx'), every checkable output rule an invariant ('INV-xx'), every deterministic safety net a
guardrail ('GR-xx') and every edge case a binary acceptance criterion ('AC-xx'). Code that implements
behaviour with no ID is out of scope. The spec changes only upstream of code, with a dated entry in
its Changelog; code, tests, datasets or thresholds are never edited to "make the spec true".

### II. The Model Is Non-Deterministic; The Evaluation Is Not
The LLM output is never compared to exact text. It is judged in three layers, in order:
Layer 1 schema validity, Layer 2 structural invariants and behavioural properties (including
guardrails), Layer 3 semantic scoring against ground truth with a deterministic heuristic
(no LLM judge replaces layers 1-2; any judge is optional, off by default and advisory only).
Pass/fail thresholds and the exact scoring formula are declared in the spec before the final
evaluation and never changed without a spec Changelog entry. The harness scores the application's
FINAL output and additionally reports what the raw model output would have scored.

### III. Isolated Model, Pure Core
The model is reached only through the 'ModelClient' protocol. Decision logic (input validation,
prompt-message construction, JSON extraction, schema validation, invariants, guardrails, scoring)
lives in modules that perform NO I/O: they MUST NOT import 'os', 'sys', 'io', 'pathlib', 'socket',
'subprocess', 'time', 'random', 'secrets', 'logging', 'urllib', 'http', 'shutil', 'tempfile', call
'open', 'print' or 'input', or read the clock. Only 'client.py', 'config.py', 'extractor.py',
'cli.py' and '__main__.py' may perform I/O. Unit tests use 'FakeModelClient'; no unit test calls a
network service. Enforced by an automated test (AC-60).

### IV. Measurable Quality Gates
A change is acceptable only if, in the same '.harness/run_harness.py' run: (1) 'ruff check src tests'
is clean for E, F, I, B, UP, S (Python 3.13); (2) 'bandit -r src' reports zero findings at every
severity and confidence; (3) the full pytest suite passes and line coverage of 'src/' is >= 90 %.
The live evaluation ('.harness/run_eval.py --client gemini') is a separate, additional gate whose
verdict is PASS, FAIL or INCONCLUSIVE as defined in the spec.

### V. Security, Secrets and Privacy
The API key is read only from the environment variable 'GEMINI_API_KEY' (optionally loaded from a
git-ignored '.env'). It is never printed, logged, written to evidence, committed or embedded in any
test. Notes are untrusted data: they are delimited in the prompt, never executed, never fetched,
and never allowed to alter the instructions. No 'eval'/'exec'/'pickle'/shell. Datasets contain only
synthetic, fictional people and no real PII.

### VI. Stable, Explicit Contract
The output JSON field names, types and allowed values ('contracts/output.schema.json') and the
'SERVICE_ERROR' classification are a public contract; changing one is a breaking change requiring a
MAJOR version bump. Free-text field wording is not part of the contract.

### VII. Simplicity
Runtime dependencies are limited to 'google-genai' and 'jsonschema', both pinned. No frameworks, no
database. Scope is exactly what the spec lists.

### VIII. Honest Evaluation
Service failures (network, quota, safety block) are reported separately as 'SERVICE_ERROR', are
excluded from the application score and make the run INCONCLUSIVE; they are never counted as
passes or hidden. Results of the fake client are labelled MODE=fake and are never evidence of
application quality. The application is not tuned to individual dataset cases and contains no
expected answers. No result file is hand-edited or fabricated.

## Quality Gates

| Gate | Tool | Pass condition |
|------|------|----------------|
| 1 Lint | 'ruff check src tests' (E,F,I,B,UP,S) | exit code 0, zero violations |
| 2 Security | 'bandit -r src' (all severities) | zero findings |
| 3 Tests + coverage | 'pytest' with 'pytest-cov' | zero failures, line coverage of 'src/' >= 90 % |
| 4 Live evaluation | 'run_eval.py --client gemini' | PASS per spec section "Evaluation" |

The only per-file lint exemption is rule 'S101' under 'tests/'. No other 'ignore',
'per-file-ignores', '# noqa', '# nosec' or '# type:' suppression is permitted anywhere.

## Agent Conduct and Harness Integrity

Any AI coding agent working in this repository MUST NOT:
- weaken, delete or reword an acceptance criterion, invariant, threshold or dataset case to fit the code;
- delete, skip ('skip', 'xfail', '-k', '--deselect') or lower the assertions of a failing test;
- relax ruff, bandit, coverage or pytest configuration, or lower the 90 % threshold;
- edit, delete or regenerate anything under 'evidence/' that a harness run recorded, or the
  'evidence/initial-generation/' snapshot;
- write or fabricate evaluation results, or run the fake client and present it as an evaluation;
- write the human sections of 'evidence/harness-log.md'.

When a gate fails the agent repairs the implementation and re-runs the same gates. A test or dataset
entry that is wrong relative to the specification may be corrected only after the specification
artifact is updated upstream with a Changelog entry stating why.

## Governance

This constitution supersedes other practices. Amendments require a version bump (MAJOR: principle
removed or redefined; MINOR: principle or gate added; PATCH: wording), a Sync Impact Report, and a
review of the plan Constitution Check. All plans, task lists and analyze reports MUST verify
compliance with Principles I-VIII; unjustified violations are CRITICAL findings.

**Version**: 1.0.0 | **Ratified**: 2026-11-15 | **Last Amended**: 2026-11-15

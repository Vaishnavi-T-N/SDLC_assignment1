# Data Model: 001-action-extractor

- `ExtractionRequest(notes: str, meeting_date: date, attendees: tuple[str, ...])` built by
  `parse_request(dict)`; raises `InputError`.
- `ExtractionOutput`: plain `dict` matching `contracts/output.schema.json`.
- `ExtractionResult(request, output, raw_text, raw_output, status, guardrail_actions, error, attempts)`;
  `status` in `ok | fallback | clarification_precheck`; `raw_output` is the parsed model dict or None.
- `Violation(id, detail)` for invariants/properties; `GuardrailAction(id, detail)`.
- `EvalCase` (dataset JSON): `id, category, requirement_ids, input, expected_items?, properties?`.
- `CaseResult`: `case_id, status (SCORED|SERVICE_ERROR), layer1, layer2_violations, output, raw_text,
  guardrail_actions, match info`.
- Output file `evidence/eval-results.json`: `mode, verdict, model, temperature, seed, prompt_sha256,
  dataset_sha256, thresholds, layers, scores_final, scores_raw, service_errors, cases[]`.

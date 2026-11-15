# Research and Decisions: 001-action-extractor

## D1 Model access
`google-genai` (pinned 3.3.0). `client.models.generate_content(model, contents, config)` with
`GenerateContentConfig(system_instruction, temperature, seed, response_mime_type="application/json",
response_json_schema=<dict>, max_output_tokens)`. Rationale: structured output reduces malformed JSON but is
not trusted (FR-07, FR-08). The SDK is injected into `GeminiClient` so unit tests need no network.
Risk: the supported JSON-schema subset of Gemini is narrower than Draft 2020-12, so the schema sent is
reduced by a keyword whitelist (`type, properties, required, additionalProperties, items, enum, minimum,
maximum, minItems, maxItems, description`); the full contract is enforced locally (Layer 1).

## D2 Temperature
Fixed 0.0 and seed 7, both from `config.py`, both recorded in every evaluation record. Low temperature
reduces, but does not remove, run-to-run variation; this is why evaluation uses thresholds, not equality.

## D3 Where decisions live
Prompt: task rules, date rules, safety rules. Code: everything checkable (guardrails, invariants). The
guardrails make the invariants hold on the final output regardless of prompt quality; the harness reports
raw-model scores so prompt quality stays visible.

## D4 Date cue words (GR-05)
A date cue is any of: a digit; month names/abbreviations (en); weekday names (en); `today, tomorrow, tonight,
week, weeks, month, months, year, years, day, days, eod, eow, eom, quarter, weekend`; Spanish `hoy, manana,
mañana, lunes, martes, miercoles, miércoles, jueves, viernes, sabado, sábado, domingo, semana, mes, año`;
French `aujourd, demain, lundi, mardi, mercredi, jeudi, vendredi, samedi, dimanche, semaine, mois`; German
`heute, morgen, montag, dienstag, mittwoch, donnerstag, freitag, samstag, sonntag, woche, monat, jahr`.
Matching is case-insensitive on whole words. The list is deliberately generous: it only nulls a date when
the notes contain no temporal word at all.

## D5 INV-09 leakage test
Word runs of 10 are taken from the system prompt after lower-casing and splitting on non-alphanumerics; any
output string whose same normalisation contains one of those runs fails. A canary token is embedded in the
prompt as a second, cheap signal.

## D6 Service errors
All SDK exceptions raised by the call, prompt blocks and empty/safety responses become `ServiceError`.
Programming errors (import, bad arguments) are not caught. Backoff 1, 2, 4 s injected `sleep` for tests.

## D7 Rejected alternatives
LLM-as-judge for layers 1-2 (non-deterministic, circular); exact-text goldens (brittle); repairing
out-of-range confidence (would hide a model defect); per-dataset-case prompt tuning (violates Principle VIII).

# CLI Contract

## Command

'python -m slotfinder find --input <path>'

| Outcome | Exit | stdout | stderr |
|---------|------|--------|--------|
| success | 0 | '{"slots":[{"end":"<UTC>Z","start":"<UTC>Z"},...]}' + LF | empty |
| input error | 2 | '{"error":{"code":"<CODE>","message":"<text>"}}' + LF | empty |
| usage error (argparse) | 2 | empty | usage text (not part of the JSON contract) |

Output is UTF-8, compact separators, keys sorted, single trailing LF, never CR (FR-20, AC-27).
Timestamps: 'YYYY-MM-DDTHH:MM:SSZ' (FR-17).

## Error codes (stable; Constitution VI)

| Code | Raised when | FR | AC |
|------|-------------|----|----|
| INVALID_JSON | unreadable file, bad JSON, top level not an object | FR-02 | AC-18 |
| MISSING_FIELD | required field absent, container wrong type, empty participants | FR-03, FR-08, FR-09, FR-13 | AC-16, AC-17 |
| NAIVE_DATETIME | datetime without UTC offset | FR-04 | AC-09 |
| INVALID_INTERVAL | busy end <= start; unparseable busy datetime | FR-13, FR-04 | AC-06, AC-07, AC-10, AC-11 |
| INVALID_TIMEZONE | unknown or unsafe timezone key | FR-10 | AC-12 |
| INVALID_WORKING_HOURS | bad HH:MM, end <= start | FR-11 | AC-13 |
| INVALID_DURATION | not integer 1..1440 | FR-07 | AC-14 |
| INVALID_WINDOW | window end <= start; unparseable window datetime | FR-06, FR-04 | AC-15, AC-10, AC-11 |
| TOO_MANY_PARTICIPANTS | more than 20 participants | FR-08 | AC-16 |

Validation order when several faults exist: FR-19 (AC-32).

## Schemas

[request.schema.json](request.schema.json), [response.schema.json](response.schema.json).

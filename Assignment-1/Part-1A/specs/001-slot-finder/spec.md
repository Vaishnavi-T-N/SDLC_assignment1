# Feature Specification: Meeting-Slot Finder

**Feature Branch**: `001-slot-finder` (no git branch: Part-1A has no git repository)

**Created**: 2026-11-15

**Status**: Clarified, analyzed (see Changelog)

**Input**: User description: "A deterministic command-line tool `python -m slotfinder find --input request.json`. Given several participants' busy intervals, working hours and time zones, a search window and a minimum meeting duration, return the common free slots."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Find common free slots (Priority: P1)

A scheduler supplies a JSON request listing participants, each with busy intervals, plus a search
window and a minimum duration. The tool prints every maximal time range, at least that long, in
which every participant is inside working hours and none is busy.

**Why this priority**: This is the whole purpose of the tool; with only this story the tool is a
usable MVP for participants whose time zone is UTC.

**Independent Test**: Compute slots for a request whose participants are all in `UTC` (at the
library level, before the CLI is wired in) and compare with the expected list.

**Acceptance Scenarios**:

1. **Given** one UTC participant with working hours 09:00-17:00 and no busy time, **When** the
   window is one whole day, **Then** exactly one slot 09:00-17:00 UTC is returned (AC-01).
2. **Given** busy intervals that overlap, touch, or repeat, **When** slots are computed, **Then**
   they behave as one merged busy block (AC-03, AC-04, AC-05).
3. **Given** a free range shorter than the minimum duration, **When** slots are computed, **Then**
   it is omitted (AC-19).

---

### User Story 2 - Respect each participant's time zone and daylight saving (Priority: P2)

Participants live in different IANA time zones. Working hours are local wall-clock times applied to
every local day inside the window, with daylight-saving transitions handled correctly.

**Why this priority**: Real teams span time zones; wrong offsets are the most common scheduling bug.

**Independent Test**: Request with participants in `America/New_York` and `Europe/London` across a
DST change; compare slots to hand-computed UTC ranges.

**Acceptance Scenarios**:

1. **Given** New York 09:00-17:00 and London 09:00-17:00 in winter, **When** computed, **Then** the
   slot is 14:00-17:00 UTC (AC-02).
2. **Given** a window crossing the New York spring-forward day, **When** computed, **Then** the
   working day is 13:00-21:00 UTC on that day and 14:00-22:00 UTC the day before (AC-21).
3. **Given** working hours that cross UTC midnight, **When** computed, **Then** one slot spans
   midnight unsplit (AC-24).

---

### User Story 3 - Reject bad input with stable error codes (Priority: P2)

A script calling the tool needs machine-readable, stable failures: exit code 2 and a JSON error
object with one of nine fixed codes.

**Why this priority**: Callers automate on the codes; wrong or unstable codes break integrations.

**Independent Test**: Feed one malformed request per error code and assert exit code and `code`.

**Acceptance Scenarios**:

1. **Given** a naive datetime anywhere, **When** run, **Then** `NAIVE_DATETIME` (AC-09).
2. **Given** an unknown time zone, **When** run, **Then** `INVALID_TIMEZONE` (AC-12).
3. **Given** a request with several faults, **When** run, **Then** the first fault in the documented
   validation order is reported (AC-32).

---

### User Story 4 - Deterministic, order-independent output (Priority: P3)

The same request always yields byte-identical output, regardless of how participants or busy
intervals are ordered in the file.

**Why this priority**: Enables caching, diffing and golden-file tests.

**Independent Test**: Run twice and with shuffled input; compare bytes.

**Acceptance Scenarios**:

1. **Given** the same input file, **When** run twice, **Then** stdout bytes are identical (AC-29).
2. **Given** participants and busy lists permuted, **When** run, **Then** stdout is identical (AC-29).

---

### Edge Cases

- Busy intervals that overlap, touch end-to-start, are duplicated, are zero-length, or have end
  before start (AC-03 to AC-07).
- Busy intervals entirely outside the window, or straddling its edge (AC-08).
- DST gaps and overlaps, midnight crossing in UTC, windows that start or end mid-day (AC-21 to AC-25).
- Maximum 20 participants; empty participant list (AC-16).
- Overnight working hours (end <= start) are explicitly out of scope and rejected (AC-13).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-01**: The tool MUST provide the command `python -m slotfinder find --input <path>`, reading
  the request from the JSON file at `<path>` and printing exactly one JSON document to stdout.
- **FR-02**: If the file cannot be read, is not valid UTF-8 JSON, or its top-level value is not a JSON
  object, the tool MUST fail with `INVALID_JSON`.
- **FR-03**: The request object MUST contain `window` (object with `start`, `end`),
  `min_duration_minutes`, and `participants` (list). A missing required field, or a container field
  of the wrong JSON type, MUST fail with `MISSING_FIELD`.
- **FR-04**: Every datetime MUST be an ISO-8601 string with a UTC offset (`Z` or `+HH:MM`) and is
  normalised to UTC. A datetime without an offset MUST fail with `NAIVE_DATETIME`. A datetime that
  cannot be parsed fails with the code of its context (`INVALID_WINDOW` for window bounds,
  `INVALID_INTERVAL` for busy bounds). A datetime with fractional seconds, or whose UTC year is
  outside 1901-2999, is treated as unparseable (see Clarifications).
- **FR-05**: All intervals MUST be half-open `[start, end)`: the start instant is inside, the end
  instant is outside.
- **FR-06**: `window.end` MUST be strictly after `window.start`, otherwise `INVALID_WINDOW`.
- **FR-07**: `min_duration_minutes` MUST be an integer (not boolean) from 1 to 1440 inclusive,
  otherwise `INVALID_DURATION`.
- **FR-08**: `participants` MUST contain 1 to 20 entries. More than 20 MUST fail with
  `TOO_MANY_PARTICIPANTS`; an empty list MUST fail with `MISSING_FIELD`.
- **FR-09**: Each participant MUST have `id` (non-empty string), `timezone`, `working_hours`
  (object with `start`, `end`) and `busy` (list); otherwise `MISSING_FIELD`. `id` is a label only and
  is not checked for uniqueness.
- **FR-10**: `timezone` MUST be a valid IANA time-zone key resolvable by the zone database,
  otherwise `INVALID_TIMEZONE`.
- **FR-11**: `working_hours.start` and `.end` MUST be 24-hour `HH:MM` strings (`00:00` to `23:59`)
  with `end` strictly after `start` on the same day; otherwise `INVALID_WORKING_HOURS`. Overnight
  ranges are out of scope.
- **FR-12**: Working hours are local wall-clock times in the participant's time zone applied to every
  local calendar day that can intersect the window, with daylight saving applied from the zone
  database. A wall-clock time is converted to UTC with PEP 495 `fold=0`: a time that occurs twice
  (DST overlap) takes its first occurrence, and a time that does not exist (DST gap) takes the UTC
  offset in force before the transition. Each day's range is `[local start, local end)` converted
  endpoint by endpoint. If conversion makes a day's working interval empty or
  negative, that day contributes no working time.
- **FR-13**: Each busy interval MUST have `start` and `end` (else `MISSING_FIELD`) with `end` strictly
  after `start`; `end <= start`, including zero length, MUST fail with `INVALID_INTERVAL`.
- **FR-14**: Busy intervals that overlap, touch, or are duplicated MUST behave as their union. Busy
  intervals outside the window MUST be ignored without error.
- **FR-15**: A returned slot MUST lie inside the window, inside every participant's working hours,
  and outside every participant's busy intervals.
- **FR-16**: Slots MUST be maximal (no two returned slots touch or overlap, and no slot can be
  extended at either end), sorted ascending by start, and each at least `min_duration_minutes`
  long. Slots are not split at UTC day boundaries: a slot may span UTC midnight. For each
  participant the local days from the day before the window start to the day after the window end
  (in that participant's zone) are considered, then clipped to the window.
- **FR-17**: On success the tool MUST exit 0 and print `{"slots":[{"start":...,"end":...}]}`, each
  timestamp in UTC formatted `YYYY-MM-DDTHH:MM:SSZ`. With no slot the list is empty.
- **FR-18**: On failure the tool MUST exit 2 and print `{"error":{"code":...,"message":...}}` to
  stdout, with `code` one of `INVALID_JSON`, `MISSING_FIELD`, `NAIVE_DATETIME`, `INVALID_INTERVAL`,
  `INVALID_TIMEZONE`, `INVALID_WORKING_HOURS`, `INVALID_DURATION`, `INVALID_WINDOW`,
  `TOO_MANY_PARTICIPANTS`. Nothing is written to stderr for these failures.
- **FR-19**: When several faults exist, the reported one MUST be the first in this order: JSON/file
  (FR-02); presence of the three top-level fields (FR-03); duration (FR-07); window (FR-04, FR-06);
  participant count (FR-08); then each participant in list order: required fields (FR-09), timezone
  (FR-10), working hours (FR-11), then busy intervals in list order (FR-13, FR-04).
- **FR-20**: Output MUST be deterministic: JSON with sorted keys, compact separators, UTF-8, a single
  trailing LF. Identical input yields byte-identical output, and the output does not change when
  participants or busy intervals are reordered.
- **FR-21**: The decision logic MUST be implemented in modules that perform no I/O and read no clock
  or randomness; only the CLI layer reads the file and writes stdout.
- **FR-22**: The tool MUST NOT access the network or spawn processes, and MUST validate a time-zone
  key against a strict allow-list before passing it to the zone database: 1 to 64 characters from
  letters, digits, `_`, `+`, `-` and `/`, with no empty segment and no `..` segment.

### Key Entities

- **Request**: window, minimum duration, 1-20 participants.
- **Window**: half-open UTC interval `[start, end)` to search.
- **Participant**: id label, IANA time zone, working hours, busy intervals.
- **WorkingHours**: local `start` and `end` wall-clock times, same day.
- **BusyInterval**: half-open UTC interval during which the participant is unavailable.
- **Slot**: maximal UTC interval satisfying FR-15 and FR-16.

## Clarifications

### Session 2026-11-15

- Q: How is a wall-clock working-hours time converted to UTC when it does not exist (DST gap) or
  occurs twice (DST overlap)? -> A: PEP 495 `fold=0` for both endpoints: ambiguous times take the
  first (pre-transition, DST) occurrence; nonexistent times take the pre-transition offset. A day
  whose converted range is empty or negative contributes no working time (FR-12, AC-22, AC-23).
- Q: May a slot cross UTC midnight, and which local days must be enumerated when the window is
  expressed in UTC? -> A: Slots are never split at UTC midnight. Per participant, enumerate local
  days from (window start's local date - 1) to (window end's local date + 1), convert each day's
  working range to UTC, and clip to the window (FR-16, AC-24, AC-25).
- Q: Which error code applies to a datetime string that cannot be parsed, or is not a string? ->
  A: The code of its context: `INVALID_WINDOW` for `window.start`/`window.end`, `INVALID_INTERVAL`
  for a busy `start`/`end`. `NAIVE_DATETIME` is reserved for well-formed values lacking an offset
  (FR-04, AC-09, AC-10).
- Q: Do two busy intervals that merely touch (`[10,11)` and `[11,12)`) leave a free instant between
  them, and may a slot start exactly where busy time ends? -> A: No instant is free between touching
  intervals (they merge into `[10,12)`); because intervals are half-open a slot may start exactly at
  a busy interval's end or end exactly at its start. Adjacent free ranges likewise merge into one
  maximal slot (FR-05, FR-14, FR-16, AC-03).
- Q: How are sub-second precision and extreme dates handled? -> A: Output has seconds precision, so
  a datetime with non-zero fractional seconds is rejected as unparseable, as is any datetime whose
  UTC year is outside 1901-2999; this keeps every computed instant representable (FR-04, AC-11).

## Acceptance Criteria *(mandatory)*

Each criterion is binary: it holds or it does not. Times are UTC unless noted. "Request" shows only
the relevant fields.

- **AC-01** (FR-15, FR-17): One participant in `UTC`, hours 09:00-17:00, no busy, window
  `2025-01-06T00:00:00Z` to `2025-01-07T00:00:00Z`, duration 30 returns exactly one slot
  `2025-01-06T09:00:00Z` to `2025-01-06T17:00:00Z`.
- **AC-02** (FR-12, FR-15): `America/New_York` 09:00-17:00 and `Europe/London` 09:00-17:00, window
  2025-01-06 whole day, returns exactly `2025-01-06T14:00:00Z` to `2025-01-06T17:00:00Z`.
- **AC-03** (FR-05, FR-14): With UTC hours 09:00-17:00 and busy `[10:00,11:00)` and `[11:00,12:00)`
  the slots are exactly `[09:00,10:00)` and `[12:00,17:00)`; a slot that ends at 10:00 or starts at
  12:00 touches busy time without overlapping it.
- **AC-04** (FR-14): Busy `[10:00,12:00)` and `[11:00,13:00)` give the same slots as the single busy
  `[10:00,13:00)`.
- **AC-05** (FR-14): Two identical busy intervals give the same slots as one.
- **AC-06** (FR-13): A busy interval with `start` equal to `end` fails with `INVALID_INTERVAL`.
- **AC-07** (FR-13): A busy interval with `end` before `start` fails with `INVALID_INTERVAL`.
- **AC-08** (FR-14): A busy interval entirely before or entirely after the window has no effect and
  causes no error; one that straddles the window start or end removes only its overlap.
- **AC-09** (FR-04): A datetime without an offset in `window.start`, `window.end`, a busy `start` or
  a busy `end` fails with `NAIVE_DATETIME`.
- **AC-10** (FR-04): An unparseable or non-string datetime fails with `INVALID_WINDOW` when it is a
  window bound and `INVALID_INTERVAL` when it is a busy bound.
- **AC-11** (FR-04): A datetime with fractional seconds, or whose UTC year is outside 1901-2999,
  fails with `INVALID_WINDOW` (window bound) or `INVALID_INTERVAL` (busy bound).
- **AC-12** (FR-10, FR-22): A timezone that is unknown, empty, non-string, or contains characters
  outside the allow-list (for example `../etc/passwd`, `Not/AZone`, `America`) fails with
  `INVALID_TIMEZONE`.
- **AC-13** (FR-11): Working hours with `end` equal to or before `start`, or a value that is not a
  zero-padded 24-hour `HH:MM` (`9:00`, `24:00`, `09:60`, `09:00:00`), fails with
  `INVALID_WORKING_HOURS`.
- **AC-14** (FR-07): `min_duration_minutes` of `0`, `1441`, `-5`, `"30"`, `30.0` and `true` fails with
  `INVALID_DURATION`; `1` and `1440` are accepted.
- **AC-15** (FR-06): A window whose `end` is equal to or before `start` fails with `INVALID_WINDOW`.
- **AC-16** (FR-08): 21 participants fail with `TOO_MANY_PARTICIPANTS`; 20 are accepted; an empty
  list fails with `MISSING_FIELD`.
- **AC-17** (FR-03, FR-09, FR-13): Omitting `window`, `min_duration_minutes`, `participants`,
  `window.start`, a participant's `id`/`timezone`/`working_hours`/`busy`, or a busy `start`/`end`
  fails with `MISSING_FIELD`; so does a container of the wrong type (for example `participants`
  being an object, or a busy entry that is not an object) and an `id` that is empty or not a string.
- **AC-18** (FR-02): Text that is not JSON, a missing file, and a top-level JSON array each fail
  with `INVALID_JSON`.
- **AC-19** (FR-16): A free range of exactly the minimum duration is returned; one a minute shorter
  is omitted.
- **AC-20** (FR-17): When participants share no free time the output is exactly `{"slots":[]}` and
  the exit code is 0.
- **AC-21** (FR-12): `America/New_York` 09:00-17:00 over 2025-03-08 to 2025-03-11 (UTC) yields
  working days `2025-03-08T14:00Z-22:00Z` (EST), `2025-03-09T13:00Z-21:00Z` (EDT, transition day),
  `2025-03-10T13:00Z-21:00Z`.
- **AC-22** (FR-12): On 2025-03-09 in `America/New_York`, hours 02:30-04:00 (start in the DST gap)
  give `07:30Z-08:00Z`; hours 02:30-03:00 give no slot on that day.
- **AC-23** (FR-12): On 2025-11-02 in `America/New_York`, hours 01:30-03:00 (start occurs twice) give
  `05:30Z-08:00Z`.
- **AC-24** (FR-16): `Asia/Tokyo` hours 06:00-10:00 over `2025-01-06T00:00Z` to `2025-01-08T00:00Z`
  give exactly `2025-01-06T00:00Z-01:00Z`, `2025-01-06T21:00Z-2025-01-07T01:00Z` and
  `2025-01-07T21:00Z-2025-01-08T00:00Z`.
- **AC-25** (FR-15): No returned slot starts before `window.start` or ends after `window.end`.
- **AC-26** (FR-04, FR-17): Inputs with `Z`, `+05:30` and `-08:00` offsets are normalised, and output
  always ends in `Z` with seconds precision.
- **AC-27** (FR-17, FR-20): Success stdout is compact JSON with sorted keys, no spaces, ends with one
  LF and contains no CR.
- **AC-28** (FR-18): Every error outcome exits 2, prints exactly one JSON object
  `{"error":{"code":C,"message":M}}` to stdout with `M` a non-empty string, and leaves stderr empty.
- **AC-29** (FR-20): Two runs on one file give identical bytes; permuting participants and busy
  intervals gives identical bytes.
- **AC-30** (FR-21, FR-22): The core modules import none of the forbidden I/O, clock or randomness
  modules, call none of the forbidden builtins, and read no clock; no module under `src/` imports a
  network or process-spawning module (`socket`, `urllib`, `http`, `subprocess`, `requests`).
- **AC-31** (Constitution III): Every `AC-nn` in this file is cited by at least one test. The
  traceability tests count as tests: `tests/contract/test_traceability.py` is itself a test and cites
  AC-31.
- **AC-32** (FR-19): A request with both an invalid duration and an invalid timezone reports
  `INVALID_DURATION`; with an invalid window and an invalid duration reports `INVALID_DURATION`; with
  two faulty participants reports the earlier participant's fault.

- **AC-33** (FR-01, FR-17): `python -m slotfinder find --input <valid file>` exits 0 and prints
  exactly one JSON document; invoking it without `--input` exits 2 with usage text on stderr and
  nothing on stdout.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 33 of 33 acceptance criteria are cited by at least one passing test (AC-31).
- **SC-002**: All nine error codes are produced by at least one CLI contract test.
- **SC-003**: One harness run reports PASS for lint, security and tests with coverage >= 90 % of `src/`.
- **SC-004**: Property tests find no slot overlapping busy time or outside working hours, and the
  output equals a brute-force minute-by-minute oracle on non-DST windows.

## Assumptions

- Input is trusted for size: window length is not capped and processing time is linear in the number
  of local days in the window and the number of busy intervals.
- Participant `id` values are labels and are not echoed in output.
- Working hours are one contiguous range per day, identical for every day (no weekends, no holidays,
  no per-day overrides): recurring calendars are out of scope.
- The zone database is the one supplied by the pinned `tzdata` package; results for a given input
  are reproducible for a given `tzdata` version.
- Usage errors from the argument parser (missing `--input`, unknown sub-command) exit 2 with usage
  text on stderr; they are not part of the JSON error contract.
- Out of scope: overnight working hours, recurring events, graphical UI, persistence, calendar
  integrations, participant priorities.

## Changelog

- 2026-11-15 v0.1: initial specification (specify).
- 2026-11-15 v0.2: clarify session resolved five ambiguities (DST gap/overlap, UTC midnight and local
  day enumeration, unparseable-datetime error code, adjacency, sub-second and year range); FR-04, FR-12,
  FR-16, AC-10, AC-11, AC-21 to AC-24 refined.
- 2026-11-15 v0.3: analyze findings applied upstream (see `analyze-report.md`): added AC-33 (FR-01 had
  no criterion); AC-30 extended to FR-22 (network and process modules); AC-17 extended to empty or
  non-string `id` and non-object busy entries (FR-09); FR-22 states the exact time-zone allow-list;
  US1 independent test no longer presumes the CLI; SC-001 count 32 -> 33. No criterion was removed
  or weakened.
- 2026-11-15 v0.4: repair cycle 01 (harness run-01). The traceability meta-test excluded its own file
  from the set of tests that may cite an AC, which made AC-31 impossible to satisfy and contradicted
  the criterion's wording ("cited by at least one test"). AC-31 now states explicitly that the
  traceability tests count as tests. No other criterion changed; no assertion was lowered: the same
  33 ACs and 22 FRs must still each be cited.

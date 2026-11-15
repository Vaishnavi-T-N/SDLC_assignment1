# Research: Meeting-Slot Finder

No NEEDS CLARIFICATION remain in Technical Context; the decisions below record the choices made.

## R1 Time-zone database
- **Decision**: 'zoneinfo' from the standard library with the 'tzdata' package as a dependency.
- **Rationale**: Windows has no system IANA database; 'tzdata' makes behaviour identical on Windows
  and Linux, which Principle II (byte-identical output) requires.
- **Alternatives**: 'pytz' (non-PEP 495 API, extra dependency); 'dateutil' (extra dependency).

## R2 DST wall-clock resolution
- **Decision**: 'datetime.combine(day, time, tzinfo=ZoneInfo(key))' (fold=0), endpoint by endpoint.
- **Rationale**: Documented PEP 495 behaviour, deterministic, and what clarification Q1 mandates.
  Gap times take the pre-transition offset, overlap times the first occurrence.
- **Alternatives**: shift gap times forward by the gap size (a hidden second rule); reject such
  working hours (would make normal zones unusable on two days a year).

## R3 Interval algebra
- **Decision**: lists of '(start, end)' aware-UTC datetime tuples, normalised by 'merge' (sorted,
  overlapping and touching intervals fused); 'subtract' and 'intersect' are two-pointer sweeps.
- **Rationale**: Simple, O(n log n), easy to verify with a brute-force minute oracle.
- **Alternatives**: interval-tree library (extra dependency, violates VII); minute bitmaps (cost
  proportional to window length, breaks for long windows).

## R4 Datetime parsing
- **Decision**: 'datetime.fromisoformat' (accepts 'Z' and offsets since 3.11), then reject naive,
  non-zero microseconds, and UTC year outside 1901-2999; convert with 'astimezone(UTC)'.
- **Rationale**: Standard library, no regex of our own; the range check removes 'OverflowError' paths.
- **Alternatives**: 'dateutil.parser' (lenient, accepts non-ISO text, extra dependency).

## R5 Determinism of output
- **Decision**: 'json.dumps(obj, sort_keys=True, separators=(",", ":"))' plus '"\n"', written as bytes
  to 'sys.stdout.buffer'.
- **Rationale**: Text-mode stdout on Windows would translate LF to CRLF and break byte identity
  across platforms (AC-27).

## R6 Time-zone key safety
- **Decision**: regex allow-list '^[A-Za-z0-9_+\-/]{1,64}$', reject any empty or '..' segment, catch
  'ZoneInfoNotFoundError', 'ValueError', 'OSError' from 'ZoneInfo(key)'.
- **Rationale**: 'ZoneInfo' maps keys to file paths; an allow-list prevents path traversal and
  directory keys such as 'America' (AC-12, FR-22).

## R7 Quality tooling
- **Decision**: ruff (E,F,I,B,UP,S), bandit with TOML config, pytest, pytest-cov, Hypothesis with
  'derandomize=True'. Gates are run by a stdlib-only script that records JSON per run.
- **Rationale**: Matches Constitution IV; recorded JSON provides evidence of repair cycles.

## R8 Test oracle for properties
- **Decision**: a brute-force per-minute oracle for windows free of DST transitions, and structural
  properties (no overlap with busy, inside working-day intervals recomputed independently) for
  windows that include transitions.
- **Rationale**: An independent oracle catches interval-algebra bugs without re-implementing the
  implementation.

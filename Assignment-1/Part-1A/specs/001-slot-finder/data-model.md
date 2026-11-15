# Data Model: Meeting-Slot Finder

All datetimes are timezone-aware, in UTC after parsing. `Interval` is `tuple[datetime, datetime]`
meaning half-open `[start, end)` with `start < end`.

## ErrorCode (StrEnum)

`INVALID_JSON`, `MISSING_FIELD`, `NAIVE_DATETIME`, `INVALID_INTERVAL`, `INVALID_TIMEZONE`,
`INVALID_WORKING_HOURS`, `INVALID_DURATION`, `INVALID_WINDOW`, `TOO_MANY_PARTICIPANTS`.

## SlotFinderError(Exception)

`code: ErrorCode`, `message: str` (non-empty).

## WorkingHours (frozen dataclass)

| Field | Type | Validation |
|-------|------|------------|
| start | `datetime.time` | pattern `([01]\d|2[0-3]):[0-5]\d` (FR-11) |
| end | `datetime.time` | same pattern; `end > start` (FR-11) |

## Participant (frozen dataclass)

| Field | Type | Validation |
|-------|------|------------|
| id | `str` | non-empty (FR-09); uniqueness not checked |
| tz | `ZoneInfo` | allow-list + zone database resolution (FR-10, FR-22) |
| working_hours | `WorkingHours` | FR-11 |
| busy | `tuple[Interval, ...]` | each `end > start` (FR-13); order as supplied |

## Request (frozen dataclass)

| Field | Type | Validation |
|-------|------|------------|
| window | `Interval` | `end > start` (FR-06) |
| min_duration | `timedelta` | integer minutes 1..1440, not bool (FR-07) |
| participants | `tuple[Participant, ...]` | 1..20 entries (FR-08) |

## Slot

An `Interval` in the result; rendered as `{"start": "...Z", "end": "...Z"}` (FR-17).

## State transitions

None: the tool is a pure function from request JSON to response JSON.

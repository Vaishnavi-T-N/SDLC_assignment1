"""Stable error codes and the exception carrying them (FR-18)."""

from enum import StrEnum


class ErrorCode(StrEnum):
    """The nine public error codes (Constitution VI)."""

    INVALID_JSON = "INVALID_JSON"
    MISSING_FIELD = "MISSING_FIELD"
    NAIVE_DATETIME = "NAIVE_DATETIME"
    INVALID_INTERVAL = "INVALID_INTERVAL"
    INVALID_TIMEZONE = "INVALID_TIMEZONE"
    INVALID_WORKING_HOURS = "INVALID_WORKING_HOURS"
    INVALID_DURATION = "INVALID_DURATION"
    INVALID_WINDOW = "INVALID_WINDOW"
    TOO_MANY_PARTICIPANTS = "TOO_MANY_PARTICIPANTS"


class SlotFinderError(Exception):
    """A request fault with a stable code and a human-readable message."""

    def __init__(self, code: ErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message

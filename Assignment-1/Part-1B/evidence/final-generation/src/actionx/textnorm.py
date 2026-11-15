"""Pure text helpers shared by the invariants, guardrails and scoring (no I/O)."""

from __future__ import annotations

import re

_WS = re.compile(r"\s+")
_WORD = re.compile(r"[^\W_]+")
_ASCII_WORD = re.compile(r"[a-z0-9]+")
URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)
_URL_TRAIL = ".,;:!?)]}\"'"

STOPWORDS = frozenset(
    "a an the to of for and in on by will be is are we should must needs need".split()
)


def normalize_ws(text: str) -> str:
    """Collapse runs of whitespace to one space and strip the ends."""
    return _WS.sub(" ", text).strip()


def words(text: str) -> list[str]:
    """Case-folded alphanumeric words (Unicode aware)."""
    return _WORD.findall(text.casefold())


def contains_sequence(haystack: list[str], needle: list[str]) -> bool:
    """True when `needle` occurs as a contiguous run inside `haystack` (empty needle: False)."""
    size = len(needle)
    if size == 0 or size > len(haystack):
        return False
    return any(haystack[i : i + size] == needle for i in range(len(haystack) - size + 1))


def word_runs(word_list: list[str], size: int) -> set[tuple[str, ...]]:
    """All contiguous runs of `size` words."""
    return {tuple(word_list[i : i + size]) for i in range(len(word_list) - size + 1)}


def tokens(text: str) -> set[str]:
    """Scoring tokens: lower-case ASCII alphanumeric runs minus stop-words."""
    return {t for t in _ASCII_WORD.findall(text.lower()) if t not in STOPWORDS}


def urls(text: str) -> set[str]:
    """URLs in `text`, lower-cased and stripped of trailing punctuation."""
    return {match.rstrip(_URL_TRAIL).casefold() for match in URL_RE.findall(text)}

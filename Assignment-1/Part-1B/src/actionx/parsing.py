"""Tolerant extraction of a JSON object from model text (pure, no I/O)."""

from __future__ import annotations

import json
import re
from collections.abc import Iterator
from typing import Any

from actionx.model import ParseError

_FENCED = re.compile(r"```[A-Za-z0-9_-]*[ \t]*\r?\n?(.*?)```", re.DOTALL)


def _balanced_objects(text: str) -> Iterator[str]:
    """Yield every balanced '{...}' slice starting at each '{', string and escape aware."""
    for start, char in enumerate(text):
        if char != "{":
            continue
        depth = 0
        in_string = False
        escaped = False
        for end in range(start, len(text)):
            current = text[end]
            if in_string:
                if escaped:
                    escaped = False
                elif current == "\\":
                    escaped = True
                elif current == '"':
                    in_string = False
                continue
            if current == '"':
                in_string = True
            elif current == "{":
                depth += 1
            elif current == "}":
                depth -= 1
                if depth == 0:
                    yield text[start : end + 1]
                    break


def _candidates(text: str) -> Iterator[str]:
    yield text.strip()
    for match in _FENCED.finditer(text):
        yield match.group(1).strip()
    yield from _balanced_objects(text)


def parse_model_text(text: str) -> dict[str, Any]:
    """Return the first JSON object found in 'text'; raise 'ParseError' if there is none."""
    for candidate in _candidates(text):
        try:
            value = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    raise ParseError("no JSON object found in model output")

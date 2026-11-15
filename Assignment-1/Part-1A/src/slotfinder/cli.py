"""Command-line interface: the only module that reads files and writes stdout (FR-01, FR-02)."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from slotfinder.core import find_slots
from slotfinder.errors import ErrorCode, SlotFinderError
from slotfinder.output import render_error, render_success
from slotfinder.parsing import parse_request

EXIT_OK = 0
EXIT_ERROR = 2


def _load_json(path: str) -> Any:
    try:
        text = Path(path).read_bytes().decode("utf-8")
        return json.loads(text)
    except (OSError, ValueError, RecursionError):
        raise SlotFinderError(
            ErrorCode.INVALID_JSON, "input file is missing, unreadable or not valid UTF-8 JSON"
        ) from None


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="slotfinder")
    commands = parser.add_subparsers(dest="command", required=True)
    find = commands.add_parser("find", help="find common free slots")
    find.add_argument("--input", required=True, help="path to the JSON request file")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the CLI and return the process exit code."""
    args = _build_parser().parse_args(argv)
    try:
        request = parse_request(_load_json(args.input))
        document = render_success(find_slots(request))
        exit_code = EXIT_OK
    except SlotFinderError as error:
        document = render_error(error.code, error.message)
        exit_code = EXIT_ERROR
    sys.stdout.buffer.write(document.encode("utf-8"))
    sys.stdout.buffer.flush()
    return exit_code

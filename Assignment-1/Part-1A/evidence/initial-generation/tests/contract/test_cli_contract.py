"""CLI contract tests: exit codes, error codes, exact bytes, determinism (FR-01, FR-17 to FR-20)."""

import io
import json
import runpy
import sys
from pathlib import Path
from typing import Any

import pytest
from support import busy, participant, request

from slotfinder.cli import main
from slotfinder.errors import ErrorCode


def run_cli(monkeypatch: pytest.MonkeyPatch, args: list[str]) -> tuple[Any, bytes, str]:
    """Run ''main'' in-process capturing raw stdout bytes and stderr text."""
    raw = io.BytesIO()
    out = io.TextIOWrapper(raw, encoding="utf-8", newline="")
    err = io.StringIO()
    monkeypatch.setattr(sys, "stdout", out)
    monkeypatch.setattr(sys, "stderr", err)
    try:
        code: Any = main(args)
    except SystemExit as exit_info:
        code = exit_info.code
    out.flush()
    return code, raw.getvalue(), err.getvalue()


def write_request(tmp_path: Path, data: Any, name: str = "request.json") -> str:
    path = tmp_path / name
    path.write_text(json.dumps(data), encoding="utf-8")
    return str(path)


def find(monkeypatch, tmp_path, data):
    return run_cli(monkeypatch, ["find", "--input", write_request(tmp_path, data)])


def naive_window():
    return request(start="2025-01-06T00:00:00")


def many_participants():
    return request([participant(f"p{i}") for i in range(21)])


ERROR_CASES = {
    "INVALID_JSON": None,  # handled by file-content tests below
    "MISSING_FIELD": {"min_duration_minutes": 30, "participants": []},
    "NAIVE_DATETIME": naive_window(),
    "INVALID_INTERVAL": request(
        [participant(busy=[busy("2025-01-06T10:00:00Z", "2025-01-06T10:00:00Z")])]
    ),
    "INVALID_TIMEZONE": request([participant(tz="Mars/Olympus")]),
    "INVALID_WORKING_HOURS": request([participant(start="17:00", end="09:00")]),
    "INVALID_DURATION": request(duration=0),
    "INVALID_WINDOW": request(start="2025-01-07T00:00:00Z", end="2025-01-06T00:00:00Z"),
    "TOO_MANY_PARTICIPANTS": many_participants(),
}


def assert_error(result, code: str) -> None:
    exit_code, out, err = result
    assert exit_code == 2
    assert err == ""
    assert out.endswith(b"\n")
    assert out.count(b"\n") == 1
    document = json.loads(out)
    assert list(document) == ["error"]
    assert sorted(document["error"]) == ["code", "message"]
    assert document["error"]["code"] == code
    assert isinstance(document["error"]["message"], str)
    assert document["error"]["message"] != ""


@pytest.mark.parametrize("code", [c for c, data in ERROR_CASES.items() if data is not None])
def test_ac28_each_error_code_via_cli_exits_2_with_json_on_stdout(monkeypatch, tmp_path, code):
    """AC-28 / FR-18: exit 2, one JSON error object on stdout, stderr empty."""
    assert_error(find(monkeypatch, tmp_path, ERROR_CASES[code]), code)


def test_ac28_all_nine_codes_are_exercised_by_contract_tests():
    """AC-28 / FR-18 (SC-002): the contract table covers every ErrorCode member."""
    assert set(ERROR_CASES) == {code.value for code in ErrorCode}
    assert len(ERROR_CASES) == 9


def test_ac18_invalid_json_text(monkeypatch, tmp_path):
    """AC-18 / FR-02: text that is not JSON gives INVALID_JSON."""
    path = tmp_path / "bad.json"
    path.write_text("{not json", encoding="utf-8")
    assert_error(run_cli(monkeypatch, ["find", "--input", str(path)]), "INVALID_JSON")


def test_ac18_missing_file(monkeypatch, tmp_path):
    """AC-18 / FR-02: a missing file gives INVALID_JSON."""
    missing = str(tmp_path / "nope.json")
    assert_error(run_cli(monkeypatch, ["find", "--input", missing]), "INVALID_JSON")


def test_ac18_top_level_array(monkeypatch, tmp_path):
    """AC-18 / FR-02: a top-level JSON array gives INVALID_JSON."""
    assert_error(find(monkeypatch, tmp_path, []), "INVALID_JSON")


def test_ac18_directory_instead_of_file(monkeypatch, tmp_path):
    """AC-18 / FR-02: an unreadable path (a directory) gives INVALID_JSON."""
    assert_error(run_cli(monkeypatch, ["find", "--input", str(tmp_path)]), "INVALID_JSON")


def test_ac18_invalid_utf8_bytes(monkeypatch, tmp_path):
    """AC-18 / FR-02: bytes that are not UTF-8 give INVALID_JSON."""
    path = tmp_path / "binary.json"
    path.write_bytes(b"\xff\xfe\x00{")
    assert_error(run_cli(monkeypatch, ["find", "--input", str(path)]), "INVALID_JSON")


def test_ac18_deeply_nested_json_is_invalid_json(monkeypatch, tmp_path):
    """AC-18 / FR-02: pathological nesting is reported as INVALID_JSON, not a crash."""
    path = tmp_path / "deep.json"
    path.write_text("[" * 100000 + "]" * 100000, encoding="utf-8")
    assert_error(run_cli(monkeypatch, ["find", "--input", str(path)]), "INVALID_JSON")


def test_ac33_valid_file_exits_zero_with_one_document(monkeypatch, tmp_path):
    """AC-33 / FR-01, FR-17: a valid request exits 0 and prints one JSON document."""
    exit_code, out, err = find(monkeypatch, tmp_path, request())
    assert exit_code == 0
    assert err == ""
    assert out.count(b"\n") == 1
    assert json.loads(out) == {
        "slots": [{"start": "2025-01-06T09:00:00Z", "end": "2025-01-06T17:00:00Z"}]
    }


def test_ac33_missing_input_option_is_a_usage_error(monkeypatch):
    """AC-33 / FR-01: no --input exits 2 with usage on stderr and nothing on stdout."""
    exit_code, out, err = run_cli(monkeypatch, ["find"])
    assert exit_code == 2
    assert out == b""
    assert "usage:" in err
    assert "--input" in err


def test_ac33_unknown_command_is_a_usage_error(monkeypatch):
    """AC-33 / FR-01: an unknown sub-command exits 2 with nothing on stdout."""
    exit_code, out, err = run_cli(monkeypatch, ["frobnicate"])
    assert exit_code == 2
    assert out == b""
    assert "usage:" in err


def test_ac20_no_common_slot_prints_empty_list_and_exits_zero(monkeypatch, tmp_path):
    """AC-20 / FR-17: exact bytes for an empty result."""
    data = request(
        [participant("a", start="09:00", end="12:00"), participant("b", start="13:00", end="17:00")]
    )
    assert find(monkeypatch, tmp_path, data) == (0, b'{"slots":[]}\n', "")


def test_ac27_exact_success_bytes(monkeypatch, tmp_path):
    """AC-27 / FR-17, FR-20: compact, sorted keys, LF only, exact bytes."""
    data = request(
        [participant(busy=[busy("2025-01-06T12:00:00Z", "2025-01-06T13:00:00Z")])]
    )
    expected = (
        b'{"slots":[{"end":"2025-01-06T12:00:00Z","start":"2025-01-06T09:00:00Z"},'
        b'{"end":"2025-01-06T17:00:00Z","start":"2025-01-06T13:00:00Z"}]}\n'
    )
    assert find(monkeypatch, tmp_path, data) == (0, expected, "")
    assert b"\r" not in expected


def test_ac29_repeated_runs_are_byte_identical(monkeypatch, tmp_path):
    """AC-29 / FR-20: the same file gives identical bytes on every run."""
    path = write_request(
        tmp_path,
        request(
            [
                participant(
                    "a",
                    "America/New_York",
                    busy=[busy("2025-01-06T15:00:00Z", "2025-01-06T16:00:00Z")],
                ),
                participant("b", "Europe/London"),
            ]
        ),
    )
    first = run_cli(monkeypatch, ["find", "--input", path])
    second = run_cli(monkeypatch, ["find", "--input", path])
    third = run_cli(monkeypatch, ["find", "--input", path])
    assert first == second == third
    assert first[0] == 0


def test_ac29_permuted_participants_and_busy_give_identical_bytes(monkeypatch, tmp_path):
    """AC-29 / FR-20: reordering participants and busy intervals does not change stdout."""
    b1 = busy("2025-01-06T15:00:00Z", "2025-01-06T16:00:00Z")
    b2 = busy("2025-01-06T10:00:00Z", "2025-01-06T11:00:00Z")
    pa = participant("a", "America/New_York", busy=[b1, b2])
    pb = participant("b", "Europe/London", busy=[b2])
    pa_swapped = participant("a", "America/New_York", busy=[b2, b1])
    original = find(monkeypatch, tmp_path, request([pa, pb]))
    permuted = find(monkeypatch, tmp_path, request([pb, pa_swapped]))
    assert original == permuted
    assert original[0] == 0


def test_ac29_python_dash_m_entry_point_matches_main(monkeypatch, tmp_path):
    """AC-29 / FR-01: 'python -m slotfinder' (module run as __main__) prints the same bytes."""
    path = write_request(tmp_path, request())
    expected = run_cli(monkeypatch, ["find", "--input", path])

    raw = io.BytesIO()
    out = io.TextIOWrapper(raw, encoding="utf-8", newline="")
    monkeypatch.setattr(sys, "stdout", out)
    monkeypatch.setattr(sys, "argv", ["slotfinder", "find", "--input", path])
    with pytest.raises(SystemExit) as exit_info:
        runpy.run_module("slotfinder", run_name="__main__")
    out.flush()
    assert exit_info.value.code == 0
    assert raw.getvalue() == expected[1]

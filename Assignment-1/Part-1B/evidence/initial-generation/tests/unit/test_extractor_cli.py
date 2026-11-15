"""AC-01, AC-02, AC-06, AC-13, AC-14, AC-40, AC-44, AC-45 (extractor flow and CLI)."""

from __future__ import annotations

import json

import pytest
from actionx.cli import main
from actionx.client import FakeModelClient, ServiceError
from actionx.contract import gemini_schema
from actionx.extractor import PROMPT_PATH
from actionx.invariants import check_invariants
from actionx.model import FALLBACK_QUESTION
from support import CONFIG, NOTES, SCHEMA, SYSTEM_PROMPT, dumps, good_item, good_output, make_extractor, req


@pytest.mark.parametrize("notes", ["", "   ", "\n\t "])
def test_ac01_empty_notes_never_call_the_model(notes):
    extractor, client = make_extractor(["unused"])
    result = extractor.extract(req(notes=notes))
    assert client.calls == []
    assert result.status == "precheck"
    assert result.output["action_items"] == []
    assert result.output["needs_clarification"] is True
    assert result.output["clarification_question"]


def test_ac02_size_limit_boundary():
    extractor, client = make_extractor([dumps(good_output([]))])
    too_long = extractor.extract(req(notes="x" * 60_001))
    assert client.calls == []
    assert too_long.output["needs_clarification"] is True
    assert "split" in too_long.output["clarification_question"]
    at_limit = extractor.extract(req(notes="x" * 60_000))
    assert len(client.calls) == 1
    assert at_limit.status == "ok"


def test_ac06_prompt_message_temperature_and_seed_are_sent():
    extractor, client = make_extractor([dumps(good_output())])
    extractor.extract(req())
    call = client.calls[0]
    assert call["system_prompt"] == PROMPT_PATH.read_text(encoding="utf-8")
    assert call["temperature"] == CONFIG.temperature
    assert call["seed"] == CONFIG.seed
    assert call["response_schema"] == gemini_schema(SCHEMA)
    assert NOTES in call["user_message"]


def test_happy_path_returns_guardrailed_output_and_keeps_raw():
    extractor, _ = make_extractor(["```json\n" + dumps(good_output()) + "\n```"])
    result = extractor.extract(req())
    assert result.status == "ok"
    assert result.output == good_output()
    assert result.attempts == 1


def test_ac13_unparseable_text_gives_fallback_and_keeps_raw_text():
    extractor, _ = make_extractor(["I cannot help with that."])
    result = extractor.extract(req())
    assert result.status == "fallback"
    assert result.output["clarification_question"] == FALLBACK_QUESTION
    assert result.raw_text == "I cannot help with that."
    assert result.raw_output is None
    assert result.error


@pytest.mark.parametrize(
    "mutate",
    [
        lambda o: o.update(surprise=1),
        lambda o: o.pop("refusal"),
        lambda o: o.update(needs_clarification="yes"),
        lambda o: o["action_items"][0].update(confidence=1.5),
        lambda o: o["action_items"][0].update(due_date="tomorrow"),
    ],
)
def test_ac14_schema_invalid_output_gives_fallback(mutate):
    bad = good_output()
    mutate(bad)
    extractor, _ = make_extractor([dumps(bad)])
    result = extractor.extract(req())
    assert result.status == "fallback"
    assert result.output["action_items"] == []
    assert result.output["needs_clarification"] is True
    assert result.raw_output == bad


def test_ac45_result_keeps_raw_and_guardrail_actions():
    raw = good_output([good_item(owner="Mallory")])
    extractor, _ = make_extractor([dumps(raw)])
    result = extractor.extract(req())
    assert result.raw_text == dumps(raw)
    assert result.raw_output == raw
    assert [a.id for a in result.guardrail_actions][0] == "GR-04"
    assert result.output["action_items"][0]["owner"] is None
    assert check_invariants(result.output, req(), SYSTEM_PROMPT) == []


def test_ac40_service_error_is_retried_three_times_with_backoff():
    sleeps: list[float] = []
    extractor, client = make_extractor([ServiceError("429 quota", "api")], sleeps)
    with pytest.raises(ServiceError) as caught:
        extractor.extract(req())
    assert len(client.calls) == 4
    assert sleeps == [1, 2, 4]
    assert "after 4 attempts" in str(caught.value)
    assert caught.value.kind == "api"


def test_ac40_transient_failure_then_success():
    sleeps: list[float] = []
    extractor, client = make_extractor(
        [ServiceError("503"), ServiceError("503"), dumps(good_output())], sleeps
    )
    result = extractor.extract(req())
    assert result.status == "ok"
    assert result.attempts == 3
    assert sleeps == [1, 2]
    assert len(client.calls) == 3


# ---------------------------------------------------------------- CLI (AC-44)

ENV = {"GEMINI_API_KEY": "unit-test-key-0000"}


def write_request(tmp_path, **changes):
    data = {"notes": NOTES, "meeting_date": "2026-03-11", "attendees": ["Bob Rivera"]}
    data.update(changes)
    path = tmp_path / "request.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return str(path)


def run_cli(args, client, env=None):
    return main(args, client_factory=lambda _config: client, environ=dict(ENV if env is None else env),
                sleep=lambda _s: None)


def test_ac44_cli_success_prints_schema_valid_json(tmp_path, capsys):
    code = run_cli(["extract", "--input", write_request(tmp_path)],
                   FakeModelClient([dumps(good_output())]))
    out = capsys.readouterr().out
    assert code == 0
    assert json.loads(out) == good_output()


def test_ac44_cli_invalid_date_exits_2_with_stderr(tmp_path, capsys):
    code = run_cli(["extract", "--input", write_request(tmp_path, meeting_date="2026-02-30")],
                   FakeModelClient(["unused"]))
    captured = capsys.readouterr()
    assert code == 2
    assert captured.out == ""
    assert "meeting_date" in captured.err


def test_ac44_cli_service_error_exits_3(tmp_path, capsys):
    code = run_cli(["extract", "--input", write_request(tmp_path)],
                   FakeModelClient([ServiceError("down")]))
    assert code == 3
    assert "service error" in capsys.readouterr().err


def test_ac44_cli_missing_key_and_bad_file_exit_2(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr("actionx.cli.load_dotenv", lambda *_a, **_k: None)
    assert run_cli(["extract", "--input", write_request(tmp_path)], FakeModelClient(["x"]), env={}) == 2
    assert "GEMINI_API_KEY" in capsys.readouterr().err
    assert run_cli(["extract", "--input", str(tmp_path / "missing.json")], FakeModelClient(["x"])) == 2
    broken = tmp_path / "broken.json"
    broken.write_text("{nope", encoding="utf-8")
    assert run_cli(["extract", "--input", str(broken)], FakeModelClient(["x"])) == 2


def test_ac44_cli_usage_error_exits_2():
    with pytest.raises(SystemExit) as caught:
        main(["extract"])
    assert caught.value.code == 2

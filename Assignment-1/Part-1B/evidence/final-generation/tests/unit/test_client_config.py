"""AC-41, AC-42, AC-43: GeminiClient error mapping (SDK injected), config, .env loader."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from actionx.client import FakeModelClient, GeminiClient, ServiceError
from actionx.config import (
    DEFAULT_MODEL,
    SEED,
    TEMPERATURE,
    ConfigError,
    load_config,
    load_dotenv,
)

KEY = "unit-test-key-0000"
CALL = {
    "system_prompt": "sys",
    "user_message": "usr",
    "temperature": 0.0,
    "seed": 7,
    "response_schema": {"type": "object"},
}


class FakeTypes:
    class GenerateContentConfig:
        def __init__(self, **kwargs):
            self.kwargs = kwargs


def make_sdk(response=None, error=None):
    seen = {}

    class Models:
        def generate_content(self, **kwargs):
            seen.update(kwargs)
            if error:
                raise error
            return response

    class Client:
        def __init__(self, api_key):
            seen["api_key"] = api_key
            self.models = Models()

    return SimpleNamespace(genai=SimpleNamespace(Client=Client), types=FakeTypes), seen


def response(text="{}", block=None, finish=None, has_candidates=True):
    candidates = [SimpleNamespace(finish_reason=SimpleNamespace(name=finish))] if finish else []
    if not has_candidates:
        candidates = []
    return SimpleNamespace(
        text=text,
        prompt_feedback=SimpleNamespace(block_reason=block) if block else None,
        candidates=candidates,
    )


def test_gemini_client_passes_structured_output_config_and_returns_text():
    sdk, seen = make_sdk(response('{"ok": 1}'))
    text = GeminiClient(KEY, "m-1", 99, sdk=sdk).generate(**CALL)
    assert text == '{"ok": 1}'
    config = seen["config"].kwargs
    assert seen["model"] == "m-1"
    assert seen["contents"] == "usr"
    assert config["response_mime_type"] == "application/json"
    assert config["response_json_schema"] == {"type": "object"}
    assert (config["temperature"], config["seed"], config["max_output_tokens"]) == (0.0, 7, 99)
    assert config["system_instruction"] == "sys"


def test_ac41_sdk_exception_maps_to_service_error_without_leaking_key():
    sdk, _ = make_sdk(error=RuntimeError(f"429 quota exceeded for key {KEY}"))
    with pytest.raises(ServiceError) as caught:
        GeminiClient(KEY, "m", sdk=sdk).generate(**CALL)
    assert caught.value.kind == "api"
    assert "429" in str(caught.value)
    assert KEY not in str(caught.value)


def test_ac41_prompt_block_maps_to_safety_service_error():
    sdk, _ = make_sdk(response(text=None, block=SimpleNamespace(name="PROHIBITED_CONTENT")))
    with pytest.raises(ServiceError) as caught:
        GeminiClient(KEY, "m", sdk=sdk).generate(**CALL)
    assert caught.value.kind == "safety"
    assert "PROHIBITED_CONTENT" in str(caught.value)


def test_ac41_prompt_block_without_enum_name():
    sdk, _ = make_sdk(response(text=None, block="BLOCKED"))
    with pytest.raises(ServiceError, match="BLOCKED"):
        GeminiClient(KEY, "m", sdk=sdk).generate(**CALL)


def test_ac41_safety_finish_reason_and_empty_text():
    sdk, _ = make_sdk(response(text="", finish="SAFETY"))
    with pytest.raises(ServiceError) as caught:
        GeminiClient(KEY, "m", sdk=sdk).generate(**CALL)
    assert caught.value.kind == "safety"
    sdk, _ = make_sdk(response(text="  ", finish="STOP"))
    with pytest.raises(ServiceError) as empty:
        GeminiClient(KEY, "m", sdk=sdk).generate(**CALL)
    assert empty.value.kind == "empty"
    sdk, _ = make_sdk(response(text=None, has_candidates=False))
    with pytest.raises(ServiceError, match="none"):
        GeminiClient(KEY, "m", sdk=sdk).generate(**CALL)


def test_gemini_client_default_sdk_import_builds_a_client():
    client = GeminiClient("placeholder-not-a-real-key", "m")
    assert client is not None


def test_fake_client_records_calls_repeats_last_and_raises():
    fake = FakeModelClient(["a", ServiceError("boom")])
    assert fake.generate(**CALL) == "a"
    with pytest.raises(ServiceError):
        fake.generate(**CALL)
    with pytest.raises(ServiceError):
        fake.generate(**CALL)
    assert len(fake.calls) == 3
    with pytest.raises(AssertionError):
        FakeModelClient([]).generate(**CALL)


def test_ac42_missing_key_is_config_error_not_service_error():
    with pytest.raises(ConfigError) as caught:
        load_config({})
    assert not isinstance(caught.value, ServiceError)
    assert load_config({}, require_key=False).api_key == ""


def test_ac42_config_defaults_and_key_never_in_repr_or_public():
    config = load_config({"GEMINI_API_KEY": KEY})
    assert (config.model, config.temperature, config.seed) == (DEFAULT_MODEL, TEMPERATURE, SEED)
    assert KEY not in repr(config)
    assert KEY not in str(config.public())
    assert load_config({"GEMINI_API_KEY": KEY, "GEMINI_MODEL": "gemini-x"}).model == "gemini-x"


def test_ac43_dotenv_loader(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "# comment\n\nA=1\nB = \"two\"\nC='three'\nEXISTING=new\nnoequals\n=novalue\nEMPTY=\n",
        encoding="utf-8",
    )
    target = {"EXISTING": "keep"}
    load_dotenv(env_file, target)
    assert target == {"EXISTING": "keep", "A": "1", "B": "two", "C": "three", "EMPTY": ""}
    load_dotenv(tmp_path / "missing.env", target)
    assert len(target) == 5

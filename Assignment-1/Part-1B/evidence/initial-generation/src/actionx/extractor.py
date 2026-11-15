"""The extraction flow: pre-checks, model call with retry, parse, validate, guardrails."""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from actionx.client import ModelClient, ServiceError
from actionx.config import Config
from actionx.contract import gemini_schema, validate_output
from actionx.guardrails import GuardrailAction, apply_guardrails
from actionx.model import (
    EMPTY_QUESTION,
    MAX_NOTES_CHARS,
    TOO_LONG_QUESTION,
    ExtractionRequest,
    ParseError,
    build_user_message,
    clarification_output,
    fallback_output,
)
from actionx.parsing import parse_model_text

ROOT = Path(__file__).resolve().parents[2]
PROMPT_PATH = ROOT / "prompts" / "extractor_system.md"
SCHEMA_PATH = ROOT / "specs" / "001-action-extractor" / "contracts" / "output.schema.json"
BACKOFF_SECONDS = (1, 2, 4)


def load_system_prompt(path: Path = PROMPT_PATH) -> str:
    return path.read_text(encoding="utf-8")


def load_schema(path: Path = SCHEMA_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


@dataclass
class ExtractionResult:
    request: ExtractionRequest
    output: dict[str, Any]
    status: str  # "ok" | "fallback" | "precheck"
    raw_text: str | None = None
    raw_output: dict[str, Any] | None = None
    guardrail_actions: list[GuardrailAction] = field(default_factory=list)
    error: str | None = None
    attempts: int = 0


class Extractor:
    def __init__(
        self,
        client: ModelClient,
        config: Config,
        system_prompt: str,
        schema: dict[str, Any],
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._client = client
        self._config = config
        self._system_prompt = system_prompt
        self._schema = schema
        self._sleep = sleep

    def _call_with_retry(self, request: ExtractionRequest) -> tuple[str, int]:
        attempts = 0
        while True:
            attempts += 1
            try:
                text = self._client.generate(
                    system_prompt=self._system_prompt,
                    user_message=build_user_message(request),
                    temperature=self._config.temperature,
                    seed=self._config.seed,
                    response_schema=gemini_schema(self._schema),
                )
            except ServiceError as error:
                if attempts > len(BACKOFF_SECONDS):
                    raise ServiceError(f"{error} (after {attempts} attempts)", error.kind) from error
                self._sleep(BACKOFF_SECONDS[attempts - 1])
                continue
            return text, attempts

    def extract(self, request: ExtractionRequest) -> ExtractionResult:
        if not request.notes.strip():
            return ExtractionResult(request, clarification_output(EMPTY_QUESTION), "precheck")
        if len(request.notes) > MAX_NOTES_CHARS:
            return ExtractionResult(request, clarification_output(TOO_LONG_QUESTION), "precheck")

        text, attempts = self._call_with_retry(request)
        try:
            parsed = parse_model_text(text)
        except ParseError as error:
            return ExtractionResult(
                request, fallback_output(), "fallback", raw_text=text, error=str(error),
                attempts=attempts,
            )
        problems = validate_output(self._schema, parsed)
        if problems:
            return ExtractionResult(
                request, fallback_output(), "fallback", raw_text=text, raw_output=parsed,
                error="; ".join(problems), attempts=attempts,
            )
        final, actions = apply_guardrails(parsed, request, self._system_prompt)
        return ExtractionResult(
            request, final, "ok", raw_text=text, raw_output=parsed, guardrail_actions=actions,
            attempts=attempts,
        )

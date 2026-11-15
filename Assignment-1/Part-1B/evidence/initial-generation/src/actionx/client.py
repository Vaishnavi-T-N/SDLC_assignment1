"""The model seam: `ModelClient` protocol, `FakeModelClient` and the live `GeminiClient`."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol


class ServiceError(Exception):
    """API, network, quota or safety-block failure (classified SERVICE_ERROR, FR-21)."""

    def __init__(self, message: str, kind: str = "api") -> None:
        super().__init__(message)
        self.kind = kind


class ModelClient(Protocol):
    def generate(
        self,
        *,
        system_prompt: str,
        user_message: str,
        temperature: float,
        seed: int,
        response_schema: dict[str, Any],
    ) -> str:
        """Return the raw model text or raise `ServiceError`."""
        ...


class FakeModelClient:
    """Serves pre-recorded responses in order; an `Exception` item is raised instead."""

    def __init__(self, responses: Sequence[str | Exception]) -> None:
        self._responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def generate(
        self,
        *,
        system_prompt: str,
        user_message: str,
        temperature: float,
        seed: int,
        response_schema: dict[str, Any],
    ) -> str:
        self.calls.append(
            {
                "system_prompt": system_prompt,
                "user_message": user_message,
                "temperature": temperature,
                "seed": seed,
                "response_schema": response_schema,
            }
        )
        if not self._responses:
            raise AssertionError("FakeModelClient has no response left")
        item = self._responses.pop(0) if len(self._responses) > 1 else self._responses[0]
        if isinstance(item, Exception):
            raise item
        return item


_SAFETY_MARKERS = ("SAFETY", "BLOCKLIST", "PROHIBITED", "SPII", "IMAGE_SAFETY", "RECITATION")


class GeminiClient:
    """Live client using the `google-genai` SDK. The SDK can be injected for tests."""

    def __init__(
        self,
        api_key: str,
        model: str,
        max_output_tokens: int = 8192,
        sdk: Any = None,
    ) -> None:
        if sdk is None:
            from google import genai
            from google.genai import types

            sdk = type("Sdk", (), {"genai": genai, "types": types})
        self._api_key = api_key
        self._model = model
        self._max_output_tokens = max_output_tokens
        self._types = sdk.types
        self._client = sdk.genai.Client(api_key=api_key)

    def _scrub(self, text: str) -> str:
        return text.replace(self._api_key, "***") if self._api_key else text

    def generate(
        self,
        *,
        system_prompt: str,
        user_message: str,
        temperature: float,
        seed: int,
        response_schema: dict[str, Any],
    ) -> str:
        config = self._types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=temperature,
            seed=seed,
            max_output_tokens=self._max_output_tokens,
            response_mime_type="application/json",
            response_json_schema=response_schema,
        )
        try:
            response = self._client.models.generate_content(
                model=self._model, contents=user_message, config=config
            )
        except Exception as error:
            raise ServiceError(
                self._scrub(f"{type(error).__name__}: {error}"), kind="api"
            ) from error

        feedback = getattr(response, "prompt_feedback", None)
        block = getattr(feedback, "block_reason", None) if feedback is not None else None
        if block:
            raise ServiceError(f"prompt blocked: {getattr(block, 'name', block)}", kind="safety")
        text = getattr(response, "text", None)
        if isinstance(text, str) and text.strip():
            return text
        candidates = getattr(response, "candidates", None) or []
        reason = str(getattr(getattr(candidates[0], "finish_reason", None), "name", "")) if (
            candidates
        ) else ""
        if any(marker in reason.upper() for marker in _SAFETY_MARKERS):
            raise ServiceError(f"response blocked: {reason}", kind="safety")
        raise ServiceError(f"empty response (finish reason: {reason or 'none'})", kind="empty")

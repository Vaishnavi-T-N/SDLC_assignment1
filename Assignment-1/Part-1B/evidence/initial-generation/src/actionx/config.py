"""Configuration: model name, fixed temperature and seed, and the API key from the environment."""

from __future__ import annotations

import os
from collections.abc import MutableMapping
from dataclasses import dataclass, field
from pathlib import Path

API_KEY_ENV = "GEMINI_API_KEY"
MODEL_ENV = "GEMINI_MODEL"
DEFAULT_MODEL = "gemini-2.5-pro"
TEMPERATURE = 0.0
SEED = 7
MAX_OUTPUT_TOKENS = 8192


class ConfigError(Exception):
    """A configuration problem (for example a missing key); not a service error."""


@dataclass(frozen=True)
class Config:
    model: str
    temperature: float
    seed: int
    max_output_tokens: int
    api_key: str = field(default="", repr=False)

    def public(self) -> dict[str, object]:
        """The recordable part of the configuration (never the key)."""
        return {
            "model": self.model,
            "temperature": self.temperature,
            "seed": self.seed,
            "max_output_tokens": self.max_output_tokens,
        }


def load_dotenv(path: Path, environ: MutableMapping[str, str] | None = None) -> None:
    """Load KEY=VALUE lines from 'path' without overriding variables that are already set."""
    target = os.environ if environ is None else environ
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text or text.startswith("#") or "=" not in text:
            continue
        name, _, value = text.partition("=")
        name = name.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if name and name not in target:
            target[name] = value


def load_config(
    environ: MutableMapping[str, str] | None = None, *, require_key: bool = True
) -> Config:
    env = os.environ if environ is None else environ
    key = env.get(API_KEY_ENV, "").strip()
    if require_key and not key:
        raise ConfigError(f"{API_KEY_ENV} is not set (export it or put it in the git-ignored .env)")
    return Config(
        model=env.get(MODEL_ENV, "").strip() or DEFAULT_MODEL,
        temperature=TEMPERATURE,
        seed=SEED,
        max_output_tokens=MAX_OUTPUT_TOKENS,
        api_key=key,
    )

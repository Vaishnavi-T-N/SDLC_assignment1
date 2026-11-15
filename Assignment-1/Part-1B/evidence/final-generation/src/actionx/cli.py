"""Command line: `python -m actionx extract --input request.json`."""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections.abc import Callable, MutableMapping, Sequence
from pathlib import Path
from typing import Any

from actionx.client import GeminiClient, ModelClient, ServiceError
from actionx.config import Config, ConfigError, load_config, load_dotenv
from actionx.extractor import ROOT, Extractor, load_schema, load_system_prompt
from actionx.model import InputError, parse_request


def _live_client(config: Config) -> ModelClient:
    return GeminiClient(config.api_key, config.model, config.max_output_tokens)


def main(
    argv: Sequence[str] | None = None,
    *,
    client_factory: Callable[[Config], ModelClient] = _live_client,
    environ: MutableMapping[str, str] | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> int:
    parser = argparse.ArgumentParser(prog="actionx")
    commands = parser.add_subparsers(dest="command", required=True)
    extract = commands.add_parser("extract", help="extract action items from a request file")
    extract.add_argument("--input", required=True, help="path of the JSON request file")
    args = parser.parse_args(argv)

    try:
        load_dotenv(ROOT / ".env", environ)
        config = load_config(environ)
        data: Any = json.loads(Path(args.input).read_text(encoding="utf-8"))
        request = parse_request(data)
        extractor = Extractor(
            client_factory(config), config, load_system_prompt(), load_schema(), sleep=sleep
        )
        result = extractor.extract(request)
    except (InputError, ConfigError, OSError, json.JSONDecodeError) as error:
        sys.stderr.write(f"error: {error}\n")
        return 2
    except ServiceError as error:
        sys.stderr.write(f"service error: {error}\n")
        return 3
    sys.stdout.write(json.dumps(result.output, indent=2, ensure_ascii=False) + "\n")
    return 0

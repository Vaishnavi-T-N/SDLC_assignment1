#!/usr/bin/env python3
"""Single evaluation pipeline: dataset -> app -> output -> Layer 1 -> Layer 2 -> Layer 3 -> verdict.

    python .harness/run_eval.py --client gemini     live evaluation (needs GEMINI_API_KEY)
    python .harness/run_eval.py --client fake       offline self-test of this pipeline, MODE=fake

Layers (spec "Evaluation"):
  1  schema validity of the application's FINAL output (jsonschema)
  2  invariants INV-02..INV-12 and the deterministic per-case properties
  3  deterministic semantic scoring (F1, owner accuracy, due-date accuracy, fabrication count)
The hard gate is 100 % of scored cases passing layers 1 and 2; layer 3 never overrides it. The same
layers are also computed on the RAW model output and reported as information only.
A case whose model call fails after retries is SERVICE_ERROR: it is excluded from every score and
makes the verdict INCONCLUSIVE.

Live results go to evidence/eval-runs/run-NN.json (never overwritten), are copied to
evidence/eval-results.json and summarised under "## Machine-recorded runs" in evidence/harness-log.md.
The fake mode writes ONLY evidence/selftest/fake-run-NN.json, labelled MODE=fake, and never touches
eval-results.json or the log. There is no option to skip a layer or edit a recorded result.

Exit status: 0 PASS, 1 FAIL, 3 INCONCLUSIVE, 2 usage or configuration error.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from actionx.client import (
    FakeModelClient,
    GeminiClient,
    ModelClient,
    ServiceError,
)
from actionx.config import Config, ConfigError, load_config, load_dotenv
from actionx.contract import validate_output
from actionx.extractor import (
    PROMPT_PATH,
    Extractor,
    load_schema,
    load_system_prompt,
)
from actionx.invariants import check_invariants, check_properties
from actionx.model import ExtractionRequest, parse_request
from actionx.scoring import THRESHOLDS, aggregate, score_case, verdict

DATASET_PATH = ROOT / "evals" / "dataset.json"
CANNED_PATH = ROOT / "tests" / "fixtures" / "canned_outputs.json"
EVIDENCE = ROOT / "evidence"
RUNS_DIR = EVIDENCE / "eval-runs"
SELFTEST_DIR = EVIDENCE / "selftest"
RESULTS_FILE = EVIDENCE / "eval-results.json"
LOG_FILE = EVIDENCE / "harness-log.md"
MACHINE_HEADING = "## Machine-recorded runs"
EXIT_CODES = {"PASS": 0, "FAIL": 1, "INCONCLUSIVE": 3}


def _no_sleep(_seconds: float) -> None:
    return None


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _layers(
    output: dict[str, Any] | None,
    request: ExtractionRequest,
    case: dict[str, Any],
    schema: dict[str, Any],
    system_prompt: str,
    with_properties: bool,
) -> dict[str, Any]:
    """Layer 1 and Layer 2 for one output (None means there was no parseable output)."""
    if output is None:
        return {"layer1_pass": False, "layer1_errors": ["no parseable JSON object"],
                "layer2_pass": False, "violations": []}
    errors = validate_output(schema, output)
    if errors:
        return {"layer1_pass": False, "layer1_errors": errors, "layer2_pass": False,
                "violations": []}
    found = check_invariants(output, request, system_prompt)
    if with_properties:
        found += check_properties(output, case.get("properties", {}))
    return {
        "layer1_pass": True,
        "layer1_errors": [],
        "layer2_pass": not found,
        "violations": [{"requirement_id": v.id, "detail": v.detail} for v in found],
    }


def evaluate_case(
    case: dict[str, Any], extractor: Extractor, schema: dict[str, Any], system_prompt: str
) -> dict[str, Any]:
    request = parse_request(case["input"])
    entry: dict[str, Any] = {
        "case": case["id"],
        "category": case["category"],
        "requirement_ids": case["requirement_ids"],
    }
    try:
        result = extractor.extract(request)
    except ServiceError as error:
        entry.update({"status": "SERVICE_ERROR", "error": str(error), "error_kind": error.kind})
        return entry
    final = _layers(result.output, request, case, schema, system_prompt, True)
    raw_output = result.raw_output if result.status == "ok" else None
    raw = _layers(raw_output, request, case, schema, system_prompt, True)
    if result.status == "fallback":
        raw["layer1_errors"] = [result.error or "unparseable or schema-invalid model output"]
    expected = case.get("expected_items") or []
    entry.update(
        {
            "status": "SCORED",
            "pipeline_status": result.status,
            "attempts": result.attempts,
            "final": final,
            "raw": raw,
            "output": result.output,
            "raw_text": result.raw_text,
            "guardrail_actions": [{"id": a.id, "detail": a.detail} for a in result.guardrail_actions],
            "passed_hard_gate": final["layer1_pass"] and final["layer2_pass"],
        }
    )
    if expected:
        entry["score_final"] = score_case(result.output["action_items"], expected)
        raw_items = raw_output["action_items"] if raw["layer1_pass"] and raw_output else []
        entry["score_raw"] = score_case(raw_items, expected)
        entry["expected_items"] = expected
    return entry


def summarise(entries: list[dict[str, Any]]) -> dict[str, Any]:
    scored = [e for e in entries if e["status"] == "SCORED"]
    errors = [e for e in entries if e["status"] == "SERVICE_ERROR"]

    def layer_counts(key: str) -> dict[str, Any]:
        return {
            "layer1_pass": sum(e[key]["layer1_pass"] for e in scored),
            "layer2_pass": sum(e[key]["layer2_pass"] for e in scored),
            "scored_cases": len(scored),
        }

    hard_rate = (
        sum(e["passed_hard_gate"] for e in scored) / len(scored) if scored else 0.0
    )
    semantic_final = aggregate([e["score_final"] for e in scored if "score_final" in e])
    semantic_raw = aggregate([e["score_raw"] for e in scored if "score_raw" in e])
    outcome, gates = verdict(len(errors), hard_rate, semantic_final)
    raw_hard = sum(e["raw"]["layer1_pass"] and e["raw"]["layer2_pass"] for e in scored)
    return {
        "verdict": outcome,
        "gates": gates,
        "hard_gate_pass_rate": hard_rate,
        "layers_final": layer_counts("final"),
        "semantic_final": semantic_final,
        "raw_informational": {
            "layers": layer_counts("raw"),
            "hard_gate_pass_rate": raw_hard / len(scored) if scored else 0.0,
            "semantic": semantic_raw,
        },
        "service_errors": [
            {"case": e["case"], "kind": e["error_kind"], "error": e["error"]} for e in errors
        ],
        "failed_cases": [e["case"] for e in scored if not e["passed_hard_gate"]],
    }


def evaluate(
    cases: list[dict[str, Any]],
    client_for_case: Callable[[dict[str, Any]], ModelClient],
    config: Config,
    system_prompt: str,
    schema: dict[str, Any],
    sleep: Callable[[float], None],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    entries = []
    for case in cases:
        extractor = Extractor(client_for_case(case), config, system_prompt, schema, sleep=sleep)
        entry = evaluate_case(case, extractor, schema, system_prompt)
        entries.append(entry)
        print(f"  {case['id']}: {entry['status']}" + (
            "" if entry["status"] != "SCORED"
            else (" PASS" if entry["passed_hard_gate"] else " FAIL (hard gate)")
        ))
    return entries, summarise(entries)


def build_record(
    mode: str, config: Config, entries: list[dict[str, Any]], summary: dict[str, Any],
    prompt_hash: str, dataset_hash: str,
) -> dict[str, Any]:
    record = {
        "mode": mode,
        "label": "MODE=fake SELF-TEST ONLY: canned outputs, not an evaluation of the application"
        if mode == "fake" else "MODE=gemini live evaluation",
        "timestamp_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "python": sys.version.split()[0],
        "config": config.public(),
        "prompt_file": "prompts/extractor_system.md",
        "prompt_sha256": prompt_hash,
        "dataset_file": "evals/dataset.json",
        "dataset_sha256": dataset_hash,
        "thresholds": THRESHOLDS,
        "llm_judge": "off",
    }
    record.update(summary)
    record["cases"] = entries
    return record


def next_number(directory: Path, pattern: str) -> int:
    numbers = [
        int(m.group(1)) for p in directory.glob("*.json") if (m := re.fullmatch(pattern, p.name))
    ]
    return max(numbers, default=0) + 1


def append_log(run_id: str, record: dict[str, Any]) -> None:
    sem = record["semantic_final"]
    raw = record["raw_informational"]
    layers = record["layers_final"]
    errors = record["service_errors"]
    lines = []
    existing = LOG_FILE.read_text(encoding="utf-8") if LOG_FILE.exists() else ""
    if MACHINE_HEADING not in existing:
        lines += ["", MACHINE_HEADING, ""]
    lines += [
        f"### {run_id} | {record['timestamp_utc']} | {record['verdict']} | MODE={record['mode']}",
        "",
        f"- model: {record['config']['model']}; temperature: {record['config']['temperature']}; "
        f"seed: {record['config']['seed']}",
        f"- prompt sha256: {record['prompt_sha256']}",
        f"- dataset sha256: {record['dataset_sha256']}",
        f"- threshold: {json.dumps(record['thresholds'])}",
        f"- layer 1: {layers['layer1_pass']}/{layers['scored_cases']} pass; layer 2: "
        f"{layers['layer2_pass']}/{layers['scored_cases']} pass; hard-gate pass rate "
        f"{record['hard_gate_pass_rate']:.4f}",
        f"- layer 3 (final): F1 {sem['f1']:.4f}, owner accuracy {sem['owner_accuracy']:.4f}, "
        f"due accuracy {sem['due_accuracy']:.4f}, fabrication {sem['fabrication']}",
        f"- gates: {json.dumps(record['gates'])}",
        f"- raw model output (informational): hard-gate pass rate "
        f"{raw['hard_gate_pass_rate']:.4f}, F1 {raw['semantic']['f1']:.4f}",
        f"- SERVICE_ERRORs: {len(errors)}" + (
            " (" + ", ".join(f"{e['case']}:{e['kind']}" for e in errors) + ")" if errors else ""
        ),
        f"- failed cases (hard gate): {', '.join(record['failed_cases']) or 'none'}",
        f"- structured result: evidence/eval-runs/{run_id}.json",
        "",
    ]
    with LOG_FILE.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")


def write_live_evidence(record: dict[str, Any]) -> str:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    number = next_number(RUNS_DIR, r"run-(\d+)\.json")
    run_id = f"run-{number:02d}"
    text = json.dumps(record, indent=2, ensure_ascii=False) + "\n"
    with (RUNS_DIR / f"{run_id}.json").open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    RESULTS_FILE.write_text(text, encoding="utf-8", newline="\n")
    append_log(run_id, record)
    return run_id


def write_selftest_evidence(record: dict[str, Any]) -> str:
    SELFTEST_DIR.mkdir(parents=True, exist_ok=True)
    number = next_number(SELFTEST_DIR, r"fake-run-(\d+)\.json")
    name = f"fake-run-{number:02d}.json"
    with (SELFTEST_DIR / name).open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, indent=2, ensure_ascii=False) + "\n")
    return name


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the layered evaluation pipeline.")
    parser.add_argument("--client", required=True, choices=["fake", "gemini"])
    args = parser.parse_args(argv)
    if sys.version_info[:2] != (3, 13):
        print(f"Python 3.13 is required, found {sys.version.split()[0]}", file=sys.stderr)
        return 2

    cases: list[dict[str, Any]] = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    system_prompt = load_system_prompt()
    schema = load_schema()
    sleep: Callable[[float], None] = time.sleep

    if args.client == "fake":
        print("MODE=fake: offline pipeline self-test with canned outputs; NOT an evaluation.")
        config = load_config({}, require_key=False)
        config = Config("fake-canned", config.temperature, config.seed, config.max_output_tokens)
        canned: dict[str, str] = json.loads(CANNED_PATH.read_text(encoding="utf-8"))

        def client_for_case(case: dict[str, Any]) -> ModelClient:
            return FakeModelClient([canned[case["id"]]])

        sleep = _no_sleep
    else:
        load_dotenv(ROOT / ".env")
        try:
            config = load_config()
        except ConfigError as error:
            print(f"configuration error: {error}", file=sys.stderr)
            return 2
        live = GeminiClient(config.api_key, config.model, config.max_output_tokens)

        def client_for_case(case: dict[str, Any]) -> ModelClient:
            return live

        print(f"MODE=gemini: model={config.model} temperature={config.temperature} seed={config.seed}")

    entries, summary = evaluate(cases, client_for_case, config, system_prompt, schema, sleep)
    record = build_record(
        args.client, config, entries, summary, sha256_of(PROMPT_PATH), sha256_of(DATASET_PATH)
    )
    if args.client == "fake":
        name = write_selftest_evidence(record)
        print(f"MODE=fake verdict (self-test, not evidence of quality): {record['verdict']}")
        print(f"written: evidence/selftest/{name}")
    else:
        run_id = write_live_evidence(record)
        print(f"verdict: {record['verdict']}  (evidence/eval-runs/{run_id}.json, evidence/eval-results.json)")
        if record["service_errors"]:
            print(f"SERVICE_ERRORs: {len(record['service_errors'])} (run is INCONCLUSIVE)")
    return EXIT_CODES[record["verdict"]]


if __name__ == "__main__":
    sys.exit(main())

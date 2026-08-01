#!/usr/bin/env python3
"""Import benchmark evidence after Draft 2020-12 Schema validation."""

from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from pathlib import Path
from typing import Any

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from performance_evidence import (  # noqa: E402 -- standalone Skill import contract
    canonical_json,
    load_records,
    result_sort_key,
    validate_result,
)
from trust_boundary import load_json, validate_record_schema  # noqa: E402 -- standalone Skill import contract
from utils import normalized_workers  # noqa: E402 -- standalone Skill import contract

ValidationTask = tuple[str, int, str, dict[str, Any]]
ValidationResult = tuple[str, int, dict[str, Any], list[str], list[str]]


def semantic_validate(task: ValidationTask, artifact_root: Path | None) -> ValidationResult:
    source, index, schema_version, compatibility = task
    try:
        normalized, semantic_errors, warnings = validate_result(compatibility, artifact_root)
    except (OSError, UnicodeError, TypeError, ValueError) as exc:
        normalized = compatibility
        semantic_errors = [f"semantic validation failed: {exc}"]
        warnings = []
    normalized["schema_version"] = schema_version
    return source, index, normalized, semantic_errors, warnings


def import_with_schema(
    paths: list[Path],
    schema_path: Path,
    artifact_root: Path | None,
    workers: int | None = 1,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    schema = load_json(schema_path)
    records: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    tasks: list[ValidationTask] = []
    observed = 0
    for path in paths:
        try:
            loaded = load_records(path)
        except (OSError, ValueError, json.JSONDecodeError, yaml.YAMLError) as exc:
            failures.append({"source": str(path), "stage": "read", "errors": [str(exc)]})
            continue
        for index, record in enumerate(loaded):
            observed += 1
            schema_failures = validate_record_schema(record, schema)
            if schema_failures:
                failures.append({"source": str(path), "index": index, "stage": "schema", "errors": schema_failures})
                continue
            compatibility = json.loads(json.dumps(record, ensure_ascii=False))
            schema_version = str(record["schema_version"])
            compatibility["schema_version"] = "1.0"
            tasks.append((str(path), index, schema_version, compatibility))

    worker_count = normalized_workers(workers, len(tasks))
    if worker_count == 1:
        validated = [semantic_validate(task, artifact_root) for task in tasks]
    else:
        with ThreadPoolExecutor(max_workers=worker_count, thread_name_prefix="tsao-evidence") as executor:
            validated = list(executor.map(partial(semantic_validate, artifact_root=artifact_root), tasks))

    seen: set[tuple[str, str, int, str]] = set()
    for source, index, normalized, semantic_errors, warnings in validated:
        key = result_sort_key(normalized)
        if key in seen:
            semantic_errors = [*semantic_errors, "duplicate benchmark/candidate/repeat/run identity"]
        seen.add(key)
        if semantic_errors:
            failures.append(
                {
                    "source": source,
                    "index": index,
                    "stage": "semantic",
                    "key": key,
                    "errors": sorted(set(semantic_errors)),
                    "warnings": warnings,
                }
            )
            continue
        records.append(normalized)
    records.sort(key=result_sort_key)
    report: dict[str, Any] = {
        "ok": not failures,
        "records": observed,
        "valid_records": len(records),
        "invalid_records": observed - len(records),
        "validation_workers": worker_count,
        "failures": failures,
        "schema_version": schema.get("properties", {}).get("schema_version", {}).get("const"),
    }
    return records, report


def canonical_export_record(record: dict[str, Any]) -> dict[str, Any]:
    exported = json.loads(json.dumps(record, ensure_ascii=False))
    exported.pop("validation", None)
    return exported


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    parser.add_argument(
        "--workers",
        type=int,
        default=0,
        help="ordered semantic-validation workers; 0 selects a conservative automatic value",
    )
    args = parser.parse_args()
    try:
        records, report = import_with_schema(
            args.inputs,
            args.schema,
            args.artifact_root,
            args.workers,
        )
    except (OSError, UnicodeError, TypeError, ValueError, json.JSONDecodeError, yaml.YAMLError) as exc:
        records = []
        report = {
            "ok": False,
            "records": 0,
            "valid_records": 0,
            "invalid_records": 0,
            "validation_workers": 1,
            "failures": [{"stage": "initialization", "errors": [str(exc)]}],
            "schema_version": None,
        }
    if report["ok"]:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(
            "".join(canonical_json(canonical_export_record(record)) + "\n" for record in records),
            encoding="utf-8",
        )
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({**report, "canonical_evidence": str(args.out) if report["ok"] else None}, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

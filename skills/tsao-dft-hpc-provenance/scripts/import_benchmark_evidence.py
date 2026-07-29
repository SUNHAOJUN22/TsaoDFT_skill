#!/usr/bin/env python3
"""Import benchmark evidence after Draft 2020-12 Schema validation."""

from __future__ import annotations

import argparse
import json
import sys
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


def import_with_schema(
    paths: list[Path], schema_path: Path, artifact_root: Path | None
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    schema = load_json(schema_path)
    records: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    seen: set[tuple[str, str, int, str]] = set()
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
                failures.append(
                    {"source": str(path), "index": index, "stage": "schema", "errors": schema_failures}
                )
                continue
            compatibility = json.loads(json.dumps(record, ensure_ascii=False))
            compatibility["schema_version"] = "1.0"
            normalized, semantic_errors, warnings = validate_result(compatibility, artifact_root)
            normalized["schema_version"] = record["schema_version"]
            key = result_sort_key(normalized)
            if key in seen:
                semantic_errors = [*semantic_errors, "duplicate benchmark/candidate/repeat/run identity"]
            seen.add(key)
            if semantic_errors:
                failures.append(
                    {
                        "source": str(path),
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
    args = parser.parse_args()
    records, report = import_with_schema(args.inputs, args.schema, args.artifact_root)
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

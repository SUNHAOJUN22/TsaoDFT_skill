#!/usr/bin/env python3
"""Import benchmark evidence after Draft 2020-12 Schema validation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from performance_evidence import canonical_json, import_evidence, load_records  # noqa: E402
from trust_boundary import load_json, validate_record_schema  # noqa: E402


def import_with_schema(
    paths: list[Path], schema_path: Path, artifact_root: Path | None
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    schema = load_json(schema_path)
    schema_failures = []
    for path in paths:
        try:
            loaded = load_records(path)
        except Exception as exc:
            schema_failures.append({"source": str(path), "errors": [str(exc)]})
            continue
        for index, record in enumerate(loaded):
            errors = validate_record_schema(record, schema)
            if errors:
                schema_failures.append({"source": str(path), "index": index, "errors": errors})
    records, report = import_evidence(paths, artifact_root)
    report["schema_failures"] = schema_failures
    report["ok"] = bool(report["ok"]) and not schema_failures
    return records, report


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
        args.out.write_text("".join(canonical_json(record) + "\n" for record in records), encoding="utf-8")
    if args.report:
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({**report, "canonical_evidence": str(args.out) if report["ok"] else None}, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

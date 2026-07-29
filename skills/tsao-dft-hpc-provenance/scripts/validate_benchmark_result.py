#!/usr/bin/env python3
"""Validate benchmark results with executable Schema before semantic checks."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from import_benchmark_evidence import import_with_schema  # noqa: E402 -- standalone Skill import contract


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path)
    parser.add_argument("--records-out", type=Path)
    args = parser.parse_args()
    records, report = import_with_schema(args.inputs, args.schema, args.artifact_root)
    if args.records_out and report["ok"]:
        args.records_out.parent.mkdir(parents=True, exist_ok=True)
        args.records_out.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({**report, "records_out": str(args.records_out) if report["ok"] else None}, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

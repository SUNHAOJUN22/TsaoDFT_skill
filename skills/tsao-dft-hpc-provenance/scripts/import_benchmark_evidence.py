#!/usr/bin/env python3
"""Import JSON, YAML, CSV or JSONL benchmark evidence into canonical JSONL."""

# Script-local imports intentionally follow SCRIPT_DIR insertion for standalone Skill installation.
# ruff: noqa: E402

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from performance_evidence import canonical_json, import_evidence


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--artifact-root", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    records, report = import_evidence(args.inputs, args.artifact_root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("".join(canonical_json(record) + "\n" for record in records), encoding="utf-8")
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                **report,
                "canonical_evidence": str(args.out),
                "report": str(args.report) if args.report else None,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

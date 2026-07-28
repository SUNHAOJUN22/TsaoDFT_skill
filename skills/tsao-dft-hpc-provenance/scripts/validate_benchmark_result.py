#!/usr/bin/env python3
"""Validate one or more benchmark result records and optionally verify artifact hashes."""

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

from performance_evidence import import_evidence


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--artifact-root", type=Path)
    parser.add_argument("--records-out", type=Path)
    args = parser.parse_args()
    records, report = import_evidence(args.inputs, args.artifact_root)
    if args.records_out:
        args.records_out.parent.mkdir(parents=True, exist_ok=True)
        args.records_out.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({**report, "records_out": str(args.records_out) if args.records_out else None}, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

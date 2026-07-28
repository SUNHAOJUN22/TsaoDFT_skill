#!/usr/bin/env python3
"""Compare imported benchmark evidence after numerical-equivalence and provenance gates."""

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

from performance_evidence import compare_evidence, import_evidence, load_policy, summary_markdown


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--markdown-out", type=Path)
    args = parser.parse_args()
    records, import_report = import_evidence(args.inputs, args.artifact_root)
    policy = load_policy(args.policy)
    summary = compare_evidence(records, policy)
    payload = {"ok": import_report["ok"], "import": import_report, "summary": summary}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.markdown_out:
        args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_out.write_text(summary_markdown(summary), encoding="utf-8")
    print(
        json.dumps(
            {
                "ok": payload["ok"],
                "summary": str(args.out),
                "markdown": str(args.markdown_out) if args.markdown_out else None,
                "reference_status": summary["reference_status"],
                "best_candidate": summary["best_qualified_performance_candidate"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Build an immutable performance evidence bundle and derive scoped L3 eligibility."""

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

from performance_evidence import compare_evidence, import_evidence, load_policy, read_document, write_evidence_bundle


def load_review(path: Path | None) -> dict[str, object]:
    if path is None:
        return {"status": "pending", "reviewer": "", "reviewed_at": ""}
    loaded = read_document(path)
    if not isinstance(loaded, dict):
        raise ValueError("review root must be a mapping")
    return loaded


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path)
    parser.add_argument("--review", type=Path)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        records, import_report = import_evidence(args.inputs, args.artifact_root)
        policy = load_policy(args.policy)
        review = load_review(args.review)
        summary = compare_evidence(records, policy)
        bundle = write_evidence_bundle(args.out_dir, records, summary, policy, review)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "errors": [str(exc)]}, ensure_ascii=False, indent=2))
        return 1
    payload = {"ok": import_report["ok"], "import": import_report, **bundle}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

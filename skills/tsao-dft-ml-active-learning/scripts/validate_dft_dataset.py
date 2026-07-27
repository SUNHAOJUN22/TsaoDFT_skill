#!/usr/bin/env python3
"""Validate a DFT-labelled ML dataset for identity, fidelity and leakage risks."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import yaml

STREAM_HASH_ROW_THRESHOLD = 25_000
HASH_BATCH_ROWS = 256


def load_rows(path: Path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def canonical_rows_sha256(rows: list[dict], stream_threshold: int = STREAM_HASH_ROW_THRESHOLD) -> str:
    """Hash the existing canonical JSON representation without a large temporary string.

    Small datasets keep the faster one-shot path. Large CSV-derived row lists are
    serialized in bounded row batches while preserving the exact bytes produced by
    ``json.dumps(rows, sort_keys=True)``.
    """

    if len(rows) < stream_threshold:
        return hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()

    digest = hashlib.sha256()
    digest.update(b"[")
    first = True
    for start in range(0, len(rows), HASH_BATCH_ROWS):
        encoded = json.dumps(rows[start : start + HASH_BATCH_ROWS], sort_keys=True).encode()
        body = encoded[1:-1]
        if not body:
            continue
        if not first:
            digest.update(b", ")
        digest.update(body)
        first = False
    digest.update(b"]")
    return digest.hexdigest()


def validate(rows: list[dict], cfg: dict) -> tuple[list[str], list[str], dict]:
    errors = []
    warnings = []
    columns = cfg.get("columns") or {}
    sample_id = columns.get("sample_id", "sample_id")
    parent = columns.get("parent_id", "parent_id")
    target = columns.get("target", "target")
    fingerprint = columns.get("method_fingerprint", "method_fingerprint")
    fidelity = columns.get("fidelity", "fidelity")
    split = columns.get("split", "split")
    if not rows:
        errors.append("dataset is empty")
        return errors, warnings, {}

    fields = set(rows[0])
    for key in (sample_id, parent, target):
        if key not in fields:
            errors.append(f"missing required column {key}")

    ids = [row.get(sample_id) for row in rows]
    if len(ids) != len(set(ids)):
        errors.append("duplicate sample IDs")

    missing_parent = [index + 2 for index, row in enumerate(rows) if not row.get(parent)]
    if missing_parent:
        errors.append(f"missing parent IDs at rows {missing_parent[:10]}")

    invalid_target = []
    for index, row in enumerate(rows):
        try:
            value = float(row.get(target, ""))
        except (TypeError, ValueError):
            invalid_target.append(index + 2)
            continue
        if not math.isfinite(value):
            invalid_target.append(index + 2)
    if invalid_target:
        errors.append(f"invalid target values at rows {invalid_target[:10]}")

    fingerprints = {row.get(fingerprint) for row in rows if row.get(fingerprint)} if fingerprint in fields else set()
    fidelities = {row.get(fidelity) for row in rows if row.get(fidelity)} if fidelity in fields else set()
    if fingerprint not in fields:
        warnings.append("method_fingerprint column absent; DFT label provenance cannot be checked row-wise")
    elif len(fingerprints) > 1 and not cfg.get("mixed_method_policy"):
        errors.append(f"multiple method fingerprints without mixed_method_policy: {sorted(fingerprints)}")
    if fidelity not in fields:
        warnings.append("fidelity column absent")
    elif len(fidelities) > 1 and not cfg.get("mixed_fidelity_policy"):
        errors.append(f"multiple fidelities without mixed_fidelity_policy: {sorted(fidelities)}")

    ignored = {sample_id, parent, split}
    signature_fields = tuple(sorted(fields - ignored))
    signatures = {}
    for index, row in enumerate(rows):
        signature = tuple((key, row.get(key, "")) for key in signature_fields)
        signatures.setdefault(signature, []).append(index + 2)
    duplicates = [values for values in signatures.values() if len(values) > 1]
    if duplicates:
        warnings.append(f"exact duplicate non-ID records: {duplicates[:5]}")

    leakage = []
    if split in fields:
        group_splits = {}
        for row in rows:
            group_splits.setdefault(row.get(parent), set()).add(row.get(split))
        leakage = [(group, sorted(values)) for group, values in group_splits.items() if len(values - {None, ""}) > 1]
        if leakage:
            errors.append(f"parent/group leakage across splits: {leakage[:10]}")
    else:
        warnings.append("split column absent; run grouped split before modelling")

    summary = {
        "row_count": len(rows),
        "parent_count": len({row.get(parent) for row in rows}),
        "method_fingerprints": sorted(fingerprints),
        "fidelities": sorted(fidelities),
        "dataset_sha256": canonical_rows_sha256(rows),
        "leakage_groups": leakage,
    }
    return errors, warnings, summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--config", type=Path)
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text()) if args.config else {}
    rows = load_rows(args.dataset)
    errors, warnings, summary = validate(rows, config or {})
    print(json.dumps({"ok": not errors, "errors": errors, "warnings": warnings, "summary": summary}, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

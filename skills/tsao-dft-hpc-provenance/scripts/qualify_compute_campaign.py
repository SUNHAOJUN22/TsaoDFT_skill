#!/usr/bin/env python3
"""Qualify reproducible CPU/accelerator campaigns from immutable benchmark evidence."""

from __future__ import annotations

import argparse
import json
import math
import os
import statistics
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker

SCRIPT_PATH = Path(__file__).resolve()
ROOT = SCRIPT_PATH.parents[3] if len(SCRIPT_PATH.parents) > 3 else Path.cwd()
DEFAULT_SCHEMA = ROOT / "templates" / "benchmark-result.schema.json"
MAX_WORKERS = 8
EXTERNAL_HOLD = "EXTERNAL_HOLD"
UNQUALIFIED = "UNQUALIFIED"
QUALIFIED_FOR_REVIEW = "QUALIFIED_FOR_REVIEW"
ENGINES = {"gaussian", "vasp", "quantum-espresso", "cp2k", "ml-surrogate"}


class QualificationLoadError(ValueError):
    """Raised when campaign or evidence documents cannot be decoded safely."""


def _reject_constant(value: str) -> None:
    raise QualificationLoadError(f"non-finite JSON constant is forbidden: {value}")


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), parse_constant=_reject_constant)
    except (OSError, UnicodeError, json.JSONDecodeError, QualificationLoadError) as exc:
        raise QualificationLoadError(f"cannot load {path.name}: {exc}") from exc
    if type(value) is not dict:
        raise QualificationLoadError(f"{path.name} root must be a mapping")
    return value


def load_campaign(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise QualificationLoadError(f"cannot load campaign: {exc}") from exc
    if type(value) is not dict:
        raise QualificationLoadError("campaign root must be a mapping")
    return value


def normalized_workers(workers: int | None, tasks: int) -> int:
    if isinstance(tasks, bool) or not isinstance(tasks, int) or tasks < 0:
        raise ValueError("tasks must be a non-negative integer")
    if workers is not None and (isinstance(workers, bool) or not isinstance(workers, int)):
        raise ValueError("workers must be an integer or null")
    if workers is not None and workers < 0:
        raise ValueError("workers must be non-negative")
    if tasks < 2:
        return 1
    requested = workers or min(MAX_WORKERS, os.cpu_count() or 1)
    return max(1, min(requested, MAX_WORKERS, tasks))


def validate_campaign(campaign: Any) -> list[str]:
    if type(campaign) is not dict:
        return ["campaign root must be a mapping"]
    errors: list[str] = []
    allowed = {
        "schema_version",
        "campaign_id",
        "benchmark_plan_id",
        "engine",
        "reference_candidate_id",
        "candidate_ids",
        "minimum_repeats",
        "minimum_reference_over_candidate_ratio",
        "numerical_tolerances",
    }
    unknown = sorted(set(campaign) - allowed)
    if unknown:
        errors.append(f"unknown campaign fields: {unknown}")
    for field in ("campaign_id", "benchmark_plan_id", "reference_candidate_id"):
        value = campaign.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field} must be a non-empty string")
    if campaign.get("schema_version") != "1.0":
        errors.append("schema_version must be 1.0")
    engine = campaign.get("engine")
    if engine not in ENGINES:
        errors.append(f"engine must be one of {sorted(ENGINES)}")
    candidates = campaign.get("candidate_ids")
    if (
        not isinstance(candidates, list)
        or not candidates
        or not all(isinstance(item, str) and item for item in candidates)
    ):
        errors.append("candidate_ids must be a non-empty list of strings")
        candidates = []
    elif len(candidates) != len(set(candidates)):
        errors.append("candidate_ids must be unique")
    if campaign.get("reference_candidate_id") in candidates:
        errors.append("reference_candidate_id must not appear in candidate_ids")
    repeats = campaign.get("minimum_repeats")
    if isinstance(repeats, bool) or not isinstance(repeats, int) or repeats < 3:
        errors.append("minimum_repeats must be an integer >= 3")
    ratio = campaign.get("minimum_reference_over_candidate_ratio")
    if isinstance(ratio, bool) or not isinstance(ratio, (int, float)) or not math.isfinite(float(ratio)) or ratio <= 1:
        errors.append("minimum_reference_over_candidate_ratio must be finite and > 1")
    tolerances = campaign.get("numerical_tolerances")
    if not isinstance(tolerances, dict) or not tolerances:
        errors.append("numerical_tolerances must be a non-empty mapping")
    else:
        for name, raw in tolerances.items():
            if not isinstance(name, str) or not name:
                errors.append("numerical_tolerances keys must be non-empty strings")
                continue
            if type(raw) is not dict or set(raw) != {"absolute", "relative"}:
                errors.append(f"numerical_tolerances.{name} must contain absolute and relative")
                continue
            for field in ("absolute", "relative"):
                value = raw[field]
                if (
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or not math.isfinite(float(value))
                    or value < 0
                ):
                    errors.append(f"numerical_tolerances.{name}.{field} must be finite and >= 0")
    return errors


def _load_validated(path: Path, validator: Draft202012Validator) -> tuple[str, dict[str, Any] | None, list[str]]:
    try:
        document = load_json(path)
    except QualificationLoadError as exc:
        return path.as_posix(), None, [str(exc)]
    errors = sorted(
        validator.iter_errors(document),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    rendered = [
        f"{path.name}:{'.'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
        for error in errors
    ]
    return path.as_posix(), document, rendered


def load_results(
    paths: list[Path], schema: dict[str, Any], workers: int | None = None
) -> tuple[list[dict[str, Any]], list[str]]:
    ordered = sorted((Path(path) for path in paths), key=lambda path: path.as_posix())
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    count = normalized_workers(workers, len(ordered))
    if count == 1:
        loaded = [_load_validated(path, validator) for path in ordered]
    else:
        with ThreadPoolExecutor(max_workers=count, thread_name_prefix="tsao-qualify") as executor:
            loaded = list(executor.map(lambda path: _load_validated(path, validator), ordered))
    documents = [document for _, document, errors in loaded if document is not None and not errors]
    errors = [error for _, _, item_errors in loaded for error in item_errors]
    return documents, errors


def _compare(reference: Any, candidate: Any, absolute: float, relative: float, path: str) -> list[str]:
    errors: list[str] = []
    if isinstance(reference, bool) or isinstance(candidate, bool):
        return [f"{path}: boolean scientific values are forbidden"]
    if isinstance(reference, (int, float)) and isinstance(candidate, (int, float)):
        ref = float(reference)
        value = float(candidate)
        limit = absolute + relative * abs(ref)
        if abs(value - ref) > limit:
            errors.append(f"{path}: numerical mismatch {value} vs {ref} exceeds {limit}")
        return errors
    if isinstance(reference, str) and isinstance(candidate, str):
        if reference != candidate:
            errors.append(f"{path}: string scientific result mismatch")
        return errors
    if isinstance(reference, list) and isinstance(candidate, list):
        if len(reference) != len(candidate):
            return [f"{path}: scientific array length mismatch"]
        for index, (left, right) in enumerate(zip(reference, candidate, strict=True)):
            errors.extend(_compare(left, right, absolute, relative, f"{path}[{index}]"))
        return errors
    return [f"{path}: scientific result type mismatch"]


def qualify(
    campaign: dict[str, Any], documents: list[dict[str, Any]], load_errors: list[str] | None = None
) -> dict[str, Any]:
    errors = [*validate_campaign(campaign), *(load_errors or [])]
    holds: list[str] = []
    if not documents:
        holds.append("no benchmark result documents were supplied")
    expected_ids = [campaign.get("reference_candidate_id"), *(campaign.get("candidate_ids") or [])]
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for document in documents:
        groups[str(document.get("candidate_id"))].append(document)
    unexpected = sorted(set(groups) - set(expected_ids))
    if unexpected:
        errors.append(f"unexpected candidate_ids: {unexpected}")

    minimum_repeats = campaign.get("minimum_repeats") if type(campaign.get("minimum_repeats")) is int else 3
    for candidate_id in expected_ids:
        rows = sorted(groups.get(str(candidate_id), []), key=lambda item: int(item.get("repeat_index", 0)))
        if len(rows) < minimum_repeats:
            holds.append(f"{candidate_id}: requires at least {minimum_repeats} repeats")
            continue
        indexes = [row.get("repeat_index") for row in rows]
        if indexes != list(range(1, len(rows) + 1)):
            errors.append(f"{candidate_id}: repeat_index values must be contiguous from 1")

    for document in documents:
        candidate_id = str(document.get("candidate_id"))
        if document.get("benchmark_plan_id") != campaign.get("benchmark_plan_id"):
            errors.append(f"{candidate_id}: benchmark_plan_id mismatch")
        if document.get("engine") != campaign.get("engine"):
            errors.append(f"{candidate_id}: engine mismatch")
        if document.get("evidence_source") != "real-engine-observation":
            holds.append(f"{candidate_id}: evidence_source is not real-engine-observation")
        if document.get("parser_acceptance") != "PASS" or document.get("exit_status") != 0:
            errors.append(f"{candidate_id}: parser or exit status not accepted")
        if not (document.get("convergence") or {}).get("achieved"):
            errors.append(f"{candidate_id}: convergence was not achieved")
        if document.get("missing_fields"):
            holds.append(f"{candidate_id}: missing_fields is not empty")
        if document.get("build_fingerprint") is None:
            holds.append(f"{candidate_id}: build fingerprint is missing")
        if document.get("hardware_fingerprint") is None:
            holds.append(f"{candidate_id}: hardware fingerprint is missing")

    if documents:
        input_hashes = {document.get("input_sha256") for document in documents}
        method_ids = {document.get("method_fingerprint_id") for document in documents}
        if len(input_hashes) != 1:
            errors.append("input_sha256 differs across campaign results")
        if len(method_ids) != 1:
            errors.append("method_fingerprint_id differs across campaign results")

    reference_id = str(campaign.get("reference_candidate_id"))
    reference_rows = sorted(groups.get(reference_id, []), key=lambda item: int(item.get("repeat_index", 0)))
    if reference_rows:
        for row in reference_rows:
            runtime = row.get("accelerator_runtime")
            if runtime is not None and runtime.get("backend") != "none":
                errors.append("reference candidate must use accelerator backend none")
        reference_results = reference_rows[0].get("scientific_results") or {}
        tolerances = campaign.get("numerical_tolerances") or {}
        for candidate_id in expected_ids:
            for row in groups.get(str(candidate_id), []):
                results = row.get("scientific_results") or {}
                if set(results) != set(reference_results):
                    errors.append(f"{candidate_id}: scientific observable set mismatch")
                    continue
                for name, reference_value in reference_results.items():
                    tolerance = tolerances.get(name)
                    if isinstance(reference_value, (int, float, list)) and tolerance is None:
                        errors.append(f"numerical_tolerances.{name} is required")
                        continue
                    absolute = float((tolerance or {}).get("absolute", 0.0))
                    relative = float((tolerance or {}).get("relative", 0.0))
                    errors.extend(
                        _compare(reference_value, results[name], absolute, relative, f"{candidate_id}.{name}")
                    )

    performance: dict[str, Any] = {"evaluated": False, "candidates": {}}
    can_evaluate = not errors and not holds and bool(reference_rows)
    if can_evaluate:
        reference_median = statistics.median(float(row["wall_time_seconds"]) for row in reference_rows)
        performance["evaluated"] = True
        performance["reference_median_wall_time_seconds"] = reference_median
        threshold = float(campaign["minimum_reference_over_candidate_ratio"])
        for candidate_id in campaign["candidate_ids"]:
            rows = groups[candidate_id]
            candidate_median = statistics.median(float(row["wall_time_seconds"]) for row in rows)
            ratio = reference_median / candidate_median
            performance["candidates"][candidate_id] = {
                "median_wall_time_seconds": candidate_median,
                "reference_over_candidate_ratio": ratio,
                "threshold": threshold,
                "passes": ratio >= threshold,
            }
            if ratio < threshold:
                errors.append(f"{candidate_id}: performance threshold was not met")

    state = (
        QUALIFIED_FOR_REVIEW
        if not errors and not holds and performance["evaluated"]
        else EXTERNAL_HOLD
        if holds
        else UNQUALIFIED
    )
    return {
        "ok": not errors,
        "state": state,
        "campaign_id": campaign.get("campaign_id"),
        "workers_bounded_by": MAX_WORKERS,
        "document_count": len(documents),
        "performance": performance,
        "holds": sorted(set(holds)),
        "errors": errors,
        "non_claims": [
            "QUALIFIED_FOR_REVIEW is not signed L3 performance qualification.",
            "Performance ratios are emitted only from accepted real-engine observations.",
            "Missing GPU, license, solver, build, or hardware evidence forces EXTERNAL_HOLD.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign", type=Path)
    parser.add_argument("results", nargs="*", type=Path)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--workers", type=int, default=0)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    try:
        campaign = load_campaign(args.campaign)
        schema = load_json(args.schema)
        documents, load_errors = load_results(args.results, schema, workers=args.workers)
        report = qualify(campaign, documents, load_errors)
    except (QualificationLoadError, ValueError) as exc:
        report = {"ok": False, "state": UNQUALIFIED, "errors": [str(exc)]}
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())

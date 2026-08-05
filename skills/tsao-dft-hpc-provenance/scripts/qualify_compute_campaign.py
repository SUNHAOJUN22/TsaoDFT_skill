#!/usr/bin/env python3
"""Qualify reproducible CPU/accelerator campaigns from canonical or explicit legacy evidence."""

from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import sys
from collections import defaultdict
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_DIR = SCRIPT_PATH.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import benchmark_contract as contract  # noqa: E402 -- standalone Skill import contract
import performance_evidence as performance  # noqa: E402 -- standalone Skill import contract

ROOT = SCRIPT_PATH.parents[3] if len(SCRIPT_PATH.parents) > 3 else Path.cwd()
DEFAULT_SCHEMA = contract.CANONICAL_SCHEMA_PATH
MAX_WORKERS = 8
EXTERNAL_HOLD = "EXTERNAL_HOLD"
UNQUALIFIED = "UNQUALIFIED"
QUALIFIED_FOR_REVIEW = "QUALIFIED_FOR_REVIEW"
ENGINES = {"gaussian", "vasp", "quantum-espresso", "cp2k", "generic", "ml-surrogate"}
GPU_BACKENDS = {"cuda", "openacc", "hip", "sycl", "metal"}
STANDARD_RESULTS = {
    "energy_ev": "energy",
    "forces_ev_per_angstrom": "forces",
    "stress_gpa": "stress",
}
PROJECTION_STATUS = "RETAINED_DIAGNOSTIC_NOT_ELIGIBLE"


class QualificationLoadError(ValueError):
    """Raised when campaign or evidence documents cannot be decoded safely."""


@dataclass(frozen=True)
class CampaignDocument:
    """Typed access to one centrally normalized canonical nested v1.1 result."""

    source: str
    record: dict[str, Any]
    migration: dict[str, Any]
    warnings: tuple[str, ...] = ()

    @property
    def schema_version(self) -> str:
        return str(self.record["schema_version"])

    @property
    def benchmark_plan_id(self) -> str:
        return str(self.record["benchmark_plan_id"])

    @property
    def candidate_id(self) -> str:
        return str(self.record["candidate_id"])

    @property
    def role(self) -> str:
        return str(self.record["role"])

    @property
    def repeat_index(self) -> int:
        return int(self.record["repeat_index"])

    @property
    def engine_name(self) -> str:
        return str(self.record["engine"]["name"])

    @property
    def engine_version(self) -> str:
        return str(self.record["engine"]["version"])

    @property
    def engine_executable(self) -> str:
        return str(self.record["engine"]["executable"])

    @property
    def build_fingerprint_id(self) -> str:
        return str(self.record["engine"]["build_fingerprint_id"])

    @property
    def hardware_fingerprint_id(self) -> str:
        return str(self.record["hardware"]["hardware_fingerprint_id"])

    @property
    def site_id(self) -> str:
        return str(self.record["execution"]["site_id"])

    @property
    def run_id(self) -> str:
        return str(self.record["execution"]["run_id"])

    @property
    def input_sha256(self) -> str:
        return str(self.record["scientific"]["input_sha256"])

    @property
    def method_fingerprint_id(self) -> str:
        return str(self.record["scientific"]["method_fingerprint_id"])

    @property
    def evidence_kind(self) -> str:
        return str(self.record["evidence_source"]["kind"])

    @property
    def missing_fields(self) -> tuple[str, ...]:
        return tuple(str(item) for item in self.record["evidence_source"]["missing_fields"])

    @property
    def parser_accepted(self) -> bool:
        return self.record["scientific"]["parser_accepted"] is True

    @property
    def exit_status(self) -> int:
        return int(self.record["execution"]["exit_status"])

    @property
    def wall_time_s(self) -> float:
        return float(self.record["performance"]["wall_time_s"])

    @property
    def accelerator_backend(self) -> str:
        return _backend_from_runtime(self.record["software"]["accelerator_runtime"])

    @property
    def gpu_uuids(self) -> tuple[str, ...]:
        return tuple(str(item) for item in self.record["hardware"]["gpu_uuids"])

    @property
    def all_artifacts_verified(self) -> bool:
        return performance.all_artifacts_verified(self.record)

    @property
    def scientific_identity(self) -> str:
        return performance.scientific_identity(self.record)

    @property
    def candidate_execution_identity(self) -> tuple[Any, ...]:
        engine = self.record["engine"]
        software = self.record["software"]
        hardware = self.record["hardware"]
        return (
            engine["version"],
            engine["executable"],
            engine["build_fingerprint_id"],
            software["compiler"],
            software["mpi"],
            software["openmp_runtime"],
            software["accelerator_runtime"],
            hardware["site_id"],
            hardware["hardware_fingerprint_id"],
            hardware["nodes"],
            hardware["ranks_per_node"],
            hardware["threads_per_rank"],
            hardware["gpu_vendor"],
            hardware["gpu_model"],
            tuple(hardware["gpu_uuids"]),
            hardware["gpu_memory_gb"],
            hardware["driver_version"],
            hardware["gpu_binding"],
        )

    def scientific_observables(self) -> dict[str, Any]:
        results = self.record["scientific"]["results"]
        observables = {key: value for key, value in results.items() if key in STANDARD_RESULTS and value is not None}
        properties = results.get("properties") or {}
        collisions = sorted(set(properties) & set(STANDARD_RESULTS))
        if collisions:
            raise ValueError(f"scientific properties collide with standard result fields: {collisions}")
        observables.update({str(key): value for key, value in properties.items()})
        return observables


def _reject_constant(value: str) -> None:
    raise QualificationLoadError(f"non-finite JSON constant is forbidden: {value}")


def _parse_finite_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise QualificationLoadError(f"non-finite JSON number is forbidden: {value}")
    return parsed


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            parse_constant=_reject_constant,
            parse_float=_parse_finite_float,
        )
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


def _backend_from_runtime(value: Any) -> str:
    text = str(value or "none").lower()
    for backend in sorted(GPU_BACKENDS):
        if text.startswith(backend) or f"{backend};" in text:
            return backend
    return "none"


def _expected_observable_names(record: dict[str, Any]) -> set[str]:
    results = record["scientific"]["results"]
    names = {logical_name for field, logical_name in STANDARD_RESULTS.items() if results.get(field) is not None}
    names.update(str(key) for key in (results.get("properties") or {}))
    return names


def _campaign_semantic_errors(record: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    results = record["scientific"]["results"]
    properties = results.get("properties") or {}
    collisions = sorted(set(properties) & set(STANDARD_RESULTS))
    if collisions:
        errors.append(f"scientific properties collide with standard result fields: {collisions}")
    if record["scientific"]["parser_accepted"] is True:
        declared = set(str(item) for item in record["scientific"]["observable_set"])
        observed = _expected_observable_names(record)
        if declared != observed:
            errors.append(
                "scientific.observable_set does not match populated canonical result fields: "
                f"declared={sorted(declared)} observed={sorted(observed)}"
            )
    return errors


def prepare_document(
    record: dict[str, Any],
    *,
    role_hint: str | None = None,
    source: str = "<memory>",
    artifact_root: Path | None = None,
) -> CampaignDocument:
    try:
        canonical, migration = contract.normalize_record(record, role_hint=role_hint)
        validated, semantic_errors, warnings = performance.validate_canonical_result(canonical, artifact_root)
    except (TypeError, ValueError, contract.BenchmarkContractError) as exc:
        raise QualificationLoadError(f"{source}: benchmark contract normalization failed: {exc}") from exc
    validated.pop("validation", None)
    semantic_errors = [*semantic_errors, *_campaign_semantic_errors(validated)]
    if semantic_errors:
        raise QualificationLoadError(f"{source}: canonical semantic validation failed: {'; '.join(semantic_errors)}")
    return CampaignDocument(
        source=source,
        record=validated,
        migration=dict(migration),
        warnings=tuple(warnings),
    )


def _load_normalized(
    path: Path,
    role_hints: dict[str, str],
) -> tuple[str, CampaignDocument | None, list[str]]:
    try:
        raw = load_json(path)
        candidate_id = str(raw.get("candidate_id", ""))
        document = prepare_document(
            raw,
            role_hint=role_hints.get(candidate_id),
            source=path.as_posix(),
        )
    except (QualificationLoadError, ValueError) as exc:
        return path.as_posix(), None, [str(exc)]
    return path.as_posix(), document, []


def load_results(
    paths: list[Path],
    schema: dict[str, Any],
    workers: int | None = None,
    role_hints: dict[str, str] | None = None,
) -> tuple[list[CampaignDocument], list[str]]:
    if contract.approved_schema_kind(schema) != "canonical-nested-v1.1":
        return [], ["compute qualification requires the authoritative nested v1.1 schema"]
    ordered = sorted((Path(path) for path in paths), key=lambda path: path.as_posix())
    hints = role_hints or {}
    count = normalized_workers(workers, len(ordered))
    if count == 1:
        loaded = [_load_normalized(path, hints) for path in ordered]
    else:
        with ThreadPoolExecutor(max_workers=count, thread_name_prefix="tsao-qualify") as executor:
            loaded = list(executor.map(lambda path: _load_normalized(path, hints), ordered))
    documents = [document for _, document, errors in loaded if document is not None and not errors]
    errors = [error for _, _, item_errors in loaded for error in item_errors]
    return documents, errors


def _role_hints(campaign: dict[str, Any]) -> dict[str, str]:
    return {
        str(campaign.get("reference_candidate_id")): "scientific-reference",
        **{str(candidate): "acceleration-candidate" for candidate in (campaign.get("candidate_ids") or [])},
    }


def _coerce_documents(
    campaign: dict[str, Any],
    documents: list[CampaignDocument | dict[str, Any]],
) -> tuple[list[CampaignDocument], list[str]]:
    prepared: list[CampaignDocument] = []
    errors: list[str] = []
    hints = _role_hints(campaign)
    for index, item in enumerate(documents):
        try:
            if isinstance(item, CampaignDocument):
                checked = prepare_document(item.record, source=item.source)
                migration = dict(item.migration)
                if migration.get("target_contract") != "canonical-nested-v1.1":
                    raise QualificationLoadError(f"{item.source}: migration target must be canonical-nested-v1.1")
                checked = CampaignDocument(
                    source=checked.source,
                    record=checked.record,
                    migration=migration,
                    warnings=checked.warnings,
                )
            elif type(item) is dict:
                candidate_id = str(item.get("candidate_id", ""))
                checked = prepare_document(
                    item,
                    role_hint=hints.get(candidate_id),
                    source=f"<memory:{index}>",
                )
            else:
                raise QualificationLoadError(f"document {index} must be a CampaignDocument or mapping")
        except (QualificationLoadError, TypeError, ValueError) as exc:
            errors.append(str(exc))
            continue
        prepared.append(checked)
    return prepared, errors


def _compare(reference: Any, candidate: Any, absolute: float, relative: float, path: str) -> list[str]:
    errors: list[str] = []
    if isinstance(reference, bool) or isinstance(candidate, bool):
        return [f"{path}: boolean scientific values are forbidden"]
    if isinstance(reference, (int, float)) and isinstance(candidate, (int, float)):
        ref = float(reference)
        value = float(candidate)
        if not math.isfinite(ref) or not math.isfinite(value):
            return [f"{path}: non-finite scientific values are forbidden"]
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


def _append_identity_drift(
    rows: list[CampaignDocument],
    getter: Callable[[CampaignDocument], Any],
    label: str,
    candidate_id: str,
    errors: list[str],
) -> None:
    if len({getter(row) for row in rows}) != 1:
        errors.append(f"{candidate_id}: {label} differs across repeats")


def qualify(
    campaign: dict[str, Any],
    documents: list[CampaignDocument | dict[str, Any]],
    load_errors: list[str] | None = None,
) -> dict[str, Any]:
    prepared, coercion_errors = _coerce_documents(campaign, documents)
    errors = [*validate_campaign(campaign), *(load_errors or []), *coercion_errors]
    holds: list[str] = []
    if not prepared:
        holds.append("no benchmark result documents were supplied")
    expected_ids = [campaign.get("reference_candidate_id"), *(campaign.get("candidate_ids") or [])]
    expected_roles = _role_hints(campaign)
    groups: dict[str, list[CampaignDocument]] = defaultdict(list)
    for document in prepared:
        groups[document.candidate_id].append(document)
    unexpected = sorted(set(groups) - set(expected_ids))
    if unexpected:
        errors.append(f"unexpected candidate_ids: {unexpected}")

    raw_minimum_repeats = campaign.get("minimum_repeats")
    minimum_repeats = int(raw_minimum_repeats) if type(raw_minimum_repeats) is int else 3
    for candidate_id in expected_ids:
        rows = sorted(groups.get(str(candidate_id), []), key=lambda item: item.repeat_index)
        if len(rows) < minimum_repeats:
            holds.append(f"{candidate_id}: requires at least {minimum_repeats} repeats")
            continue
        indexes = [row.repeat_index for row in rows]
        if indexes != list(range(1, len(rows) + 1)):
            errors.append(f"{candidate_id}: repeat_index values must be contiguous from 1")

    run_ids = [document.run_id for document in prepared]
    if len(run_ids) != len(set(run_ids)):
        errors.append("execution.run_id values must be globally unique")

    expected_engine = "generic" if campaign.get("engine") == "ml-surrogate" else campaign.get("engine")
    for document in prepared:
        candidate_id = document.candidate_id
        is_real = document.evidence_kind == "real-engine"
        has_missing = bool(document.missing_fields)
        held_provenance = not is_real or has_missing
        if document.schema_version != contract.CANONICAL_SCHEMA_VERSION:
            errors.append(f"{candidate_id}: internal document is not canonical nested v1.1")
        if document.benchmark_plan_id != campaign.get("benchmark_plan_id"):
            errors.append(f"{candidate_id}: benchmark_plan_id mismatch")
        if document.engine_name != expected_engine:
            errors.append(f"{candidate_id}: engine mismatch")
        if document.role != expected_roles.get(candidate_id):
            errors.append(f"{candidate_id}: canonical role does not match campaign role")
        if document.migration.get("qualification_impact") == EXTERNAL_HOLD:
            holds.append(f"{candidate_id}: source migration forces EXTERNAL_HOLD")
        if not is_real:
            holds.append(f"{candidate_id}: evidence_source.kind is not real-engine")
        if document.parser_accepted is not True or document.exit_status != 0:
            message = f"{candidate_id}: parser or exit status not accepted"
            (holds if held_provenance else errors).append(message)
        if has_missing:
            holds.append(f"{candidate_id}: evidence_source.missing_fields is not empty")
        if document.build_fingerprint_id == "MISSING":
            holds.append(f"{candidate_id}: build fingerprint is missing")
        if document.hardware_fingerprint_id == "MISSING":
            holds.append(f"{candidate_id}: hardware fingerprint is missing")
        if document.site_id == "MISSING":
            holds.append(f"{candidate_id}: site identity is missing")
        if not document.all_artifacts_verified:
            holds.append(f"{candidate_id}: artifacts are not fully VERIFIED")

        hardware = document.record["hardware"]
        backend = document.accelerator_backend
        gpu_vendor = str(hardware["gpu_vendor"])
        gpu_uuids = document.gpu_uuids
        if document.role == "scientific-reference":
            if backend != "none" or gpu_vendor != "none" or gpu_uuids:
                message = f"{candidate_id}: reference role requires accelerator backend none and no GPU identity"
                (holds if held_provenance else errors).append(message)
        elif document.role == "acceleration-candidate" and (
            backend not in GPU_BACKENDS or gpu_vendor == "none" or not gpu_uuids
        ):
            message = f"{candidate_id}: acceleration role requires backend, vendor and GPU UUID identity"
            (holds if held_provenance else errors).append(message)

    if prepared:
        if len({document.input_sha256 for document in prepared}) != 1:
            errors.append("scientific.input_sha256 differs across campaign results")
        if len({document.method_fingerprint_id for document in prepared}) != 1:
            errors.append("scientific.method_fingerprint_id differs across campaign results")
        if len({document.scientific_identity for document in prepared}) != 1:
            errors.append("canonical scientific identity differs across campaign results")
        if len({document.site_id for document in prepared}) != 1:
            errors.append("execution.site_id differs across campaign results")

    for candidate_id, rows in groups.items():
        _append_identity_drift(
            rows,
            lambda row: row.candidate_execution_identity,
            "build, software, hardware or GPU topology identity",
            candidate_id,
            errors,
        )
        _append_identity_drift(
            rows,
            lambda row: row.hardware_fingerprint_id,
            "hardware_fingerprint_id",
            candidate_id,
            errors,
        )
        _append_identity_drift(
            rows,
            lambda row: row.gpu_uuids,
            "multi-GPU UUID set",
            candidate_id,
            errors,
        )

    reference_id = str(campaign.get("reference_candidate_id"))
    reference_rows = sorted(groups.get(reference_id, []), key=lambda item: item.repeat_index)
    if reference_rows:
        reference_results = reference_rows[0].scientific_observables()
        tolerances = campaign.get("numerical_tolerances") or {}
        for candidate_id in expected_ids:
            for row in groups.get(str(candidate_id), []):
                results = row.scientific_observables()
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

    performance_report: dict[str, Any] = {"evaluated": False, "candidates": {}}
    can_evaluate = not errors and not holds and bool(reference_rows)
    if can_evaluate:
        reference_median = statistics.median(row.wall_time_s for row in reference_rows)
        performance_report["evaluated"] = True
        performance_report["reference_median_wall_time_seconds"] = reference_median
        threshold = float(campaign["minimum_reference_over_candidate_ratio"])
        for candidate_id in campaign["candidate_ids"]:
            rows = groups[candidate_id]
            candidate_median = statistics.median(row.wall_time_s for row in rows)
            ratio = reference_median / candidate_median
            if not math.isfinite(ratio):
                errors.append(f"{candidate_id}: non-finite performance ratio")
                continue
            performance_report["candidates"][candidate_id] = {
                "median_wall_time_seconds": candidate_median,
                "reference_over_candidate_ratio": ratio,
                "threshold": threshold,
                "passes": ratio >= threshold,
            }
            if ratio < threshold:
                errors.append(f"{candidate_id}: performance threshold was not met")

    state = (
        QUALIFIED_FOR_REVIEW
        if not errors and not holds and performance_report["evaluated"]
        else EXTERNAL_HOLD
        if holds
        else UNQUALIFIED
    )
    return {
        "ok": not errors,
        "state": state,
        "campaign_id": campaign.get("campaign_id"),
        "benchmark_result_contract": "canonical-nested-v1.1",
        "input_model": "canonical-nested-v1.1-typed-accessor",
        "normalization_mandatory": True,
        "native_semantic_validation": True,
        "legacy_projection_consumed": False,
        "legacy_projection_status": PROJECTION_STATUS,
        "workers_bounded_by": MAX_WORKERS,
        "document_count": len(prepared),
        "performance": performance_report,
        "holds": sorted(set(holds)),
        "errors": errors,
        "identity_invariants": [
            "campaign role equals canonical role",
            "global execution.run_id uniqueness",
            "single campaign site identity",
            "stable per-candidate build/software/hardware identity",
            "stable per-candidate multi-GPU UUID set",
            "single canonical scientific identity",
            "fully VERIFIED artifacts before ratio evaluation",
        ],
        "non_claims": [
            "QUALIFIED_FOR_REVIEW is not signed L3 performance qualification.",
            "Performance ratios are emitted only from accepted real-engine observations.",
            "Missing GPU, license, solver, build, site, hardware or artifact evidence forces EXTERNAL_HOLD.",
            "Legacy flat v1.0 evidence with irrecoverable provenance gaps remains EXTERNAL_HOLD.",
            "compute_qualification_view is retained only as a diagnostic compatibility export and is not eligible for qualification input.",
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
        documents, load_errors = load_results(
            args.results,
            schema,
            workers=args.workers,
            role_hints=_role_hints(campaign),
        )
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

#!/usr/bin/env python3
"""Capture deterministic compute-contract evidence without invoking external engines."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
VALIDATORS = {
    "acceleration_registry": ROOT / "scripts" / "validate_acceleration_registry.py",
    "benchmark_contract": ROOT / "scripts" / "validate_benchmark_contract.py",
    "engine_capabilities": ROOT / "scripts" / "validate_engine_capabilities.py",
    "compute_qualification": ROOT / "scripts" / "validate_compute_qualification.py",
}
SCHEMA_VERSION = "1.4"
EXTERNAL_HOLD = "EXTERNAL_HOLD"
UNQUALIFIED = "UNQUALIFIED"


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def build_report() -> dict[str, Any]:
    errors: list[str] = []
    reports: dict[str, dict[str, Any]] = {}
    try:
        for name, path in VALIDATORS.items():
            module = load_module(f"tsao_contract_evidence_{name}", path)
            report = module.validate()
            if type(report) is not dict:
                errors.append(f"{name} validator did not return a mapping")
                continue
            reports[name] = report
            if report.get("ok") is not True:
                errors.append(f"{name} validator failed")
    except (OSError, ImportError, RuntimeError, AttributeError, ValueError) as exc:
        errors.append(f"contract evidence capture failed: {exc}")

    registry = reports.get("acceleration_registry", {})
    benchmark = reports.get("benchmark_contract", {})
    engine = reports.get("engine_capabilities", {})
    qualification = reports.get("compute_qualification", {})
    validated_surfaces = registry.get("validated_surfaces") or []
    if "runtime_single_source" not in validated_surfaces:
        errors.append("acceleration registry runtime single source is not validated")
    if benchmark.get("canonical_contract") != "nested-v1.1":
        errors.append("benchmark-result authority is not canonical nested v1.1")
    if benchmark.get("root_mirror_synchronized") is not True:
        errors.append("root benchmark-result schema mirror is not synchronized")
    if benchmark.get("native_semantic_schema_version") != "1.1":
        errors.append("benchmark semantic validator is not native canonical nested v1.1")
    if benchmark.get("compatibility_view_present") is not False:
        errors.append("nested v1.0 semantic compatibility view remains present")
    if benchmark.get("legacy_semantic_bypass") != "FAIL_CLOSED":
        errors.append("legacy semantic bypass is not fail-closed")
    if benchmark.get("legacy_flat_qualification_impact") != EXTERNAL_HOLD:
        errors.append("legacy flat migration does not force EXTERNAL_HOLD")
    if benchmark.get("unknown_or_mixed_input") != "FAIL_CLOSED":
        errors.append("unknown or mixed benchmark evidence is not fail-closed")
    if benchmark.get("external_engine_invoked") is not False:
        errors.append("benchmark contract validation invoked an external engine")
    if engine.get("repository_template_state") != EXTERNAL_HOLD:
        errors.append("EngineCapability templates are not EXTERNAL_HOLD")
    if engine.get("performance_qualification") != "NOT_ESTABLISHED":
        errors.append("EngineCapability performance qualification must remain NOT_ESTABLISHED")
    if qualification.get("repository_state") != EXTERNAL_HOLD:
        errors.append("compute qualification template is not EXTERNAL_HOLD")
    if qualification.get("performance_evaluated") is not False:
        errors.append("repository compute qualification must not evaluate performance")
    if qualification.get("workers_bounded_by") != 8:
        errors.append("compute qualification worker bound is not eight")
    if qualification.get("campaign_contract") != "canonical-compute-campaign-v1.1":
        errors.append("compute campaign authority is not canonical v1.1")
    if qualification.get("campaign_schema_version") != "1.1":
        errors.append("compute campaign schema version is not 1.1")
    if qualification.get("campaign_root_mirror_synchronized") is not True:
        errors.append("root compute-campaign schema mirror is not synchronized")
    if qualification.get("campaign_unknown_or_mixed_input") != "FAIL_CLOSED":
        errors.append("unknown or mixed compute-campaign input is not fail-closed")
    if qualification.get("campaign_migration_qualification_impact") not in {
        "none",
        "NO_EVIDENCE_PROMOTION",
    }:
        errors.append("compute campaign migration impact is not explicitly non-promoting")
    if qualification.get("campaign_defaults_applied") != []:
        errors.append("compute campaign migration applied defaults")
    if qualification.get("campaign_evidence_fields_added") != []:
        errors.append("compute campaign migration fabricated evidence fields")
    if qualification.get("campaign_document_immutable") is not True:
        errors.append("compute campaign document is not immutable")
    if qualification.get("contract_boundary") != ("campaign-policy-independent-from-benchmark-result-evidence"):
        errors.append("campaign and benchmark-result contract boundary is not explicit")
    if qualification.get("input_model") != "canonical-nested-v1.1-typed-accessor":
        errors.append("compute qualification input model is not native canonical typed access")
    if qualification.get("normalization_mandatory") is not True:
        errors.append("compute qualification does not require central normalization")
    if qualification.get("native_semantic_validation") is not True:
        errors.append("compute qualification does not require native semantic validation")
    if qualification.get("legacy_projection_retained") is not True:
        errors.append("legacy diagnostic projection retention is not explicit")
    if qualification.get("legacy_projection_consumed") is not False:
        errors.append("legacy diagnostic projection is still consumed by qualification")
    if qualification.get("legacy_projection_qualification_impact") != "NOT_ELIGIBLE":
        errors.append("legacy diagnostic projection is not explicitly qualification-ineligible")
    if len(qualification.get("identity_invariants") or []) < 7:
        errors.append("compute qualification identity invariants are incomplete")

    return {
        "ok": not errors,
        "schema_version": SCHEMA_VERSION,
        "state": EXTERNAL_HOLD if not errors else UNQUALIFIED,
        "scope": (
            "repository templates, canonical semantics, closed campaign policy, "
            "schema migrations and permanent validators only"
        ),
        "external_engine_invoked": False,
        "acceleration_registry": {
            "ok": registry.get("ok"),
            "registry_version": registry.get("registry_version"),
            "libraries": registry.get("libraries"),
            "runtime_single_source": "runtime_single_source" in validated_surfaces,
        },
        "benchmark_contract": {
            "ok": benchmark.get("ok"),
            "canonical_contract": benchmark.get("canonical_contract"),
            "canonical_schema_sha256": benchmark.get("canonical_schema_sha256"),
            "root_mirror_synchronized": benchmark.get("root_mirror_synchronized"),
            "native_semantic_schema_version": benchmark.get("native_semantic_schema_version"),
            "compatibility_view_present": benchmark.get("compatibility_view_present"),
            "legacy_semantic_bypass": benchmark.get("legacy_semantic_bypass"),
            "legacy_contracts": benchmark.get("legacy_contracts"),
            "legacy_flat_qualification_impact": benchmark.get("legacy_flat_qualification_impact"),
            "unknown_or_mixed_input": benchmark.get("unknown_or_mixed_input"),
        },
        "campaign_contract": {
            "ok": qualification.get("ok"),
            "canonical_contract": qualification.get("campaign_contract"),
            "canonical_schema_version": qualification.get("campaign_schema_version"),
            "canonical_schema_sha256": qualification.get("campaign_schema_sha256"),
            "root_mirror_synchronized": qualification.get("campaign_root_mirror_synchronized"),
            "template_source_contract": qualification.get("campaign_source_contract"),
            "template_migration": qualification.get("campaign_migration"),
            "migration_qualification_impact": qualification.get("campaign_migration_qualification_impact"),
            "defaults_applied": qualification.get("campaign_defaults_applied"),
            "evidence_fields_added": qualification.get("campaign_evidence_fields_added"),
            "unknown_or_mixed_input": qualification.get("campaign_unknown_or_mixed_input"),
            "immutable_mapping": qualification.get("campaign_document_immutable"),
            "benchmark_result_boundary": qualification.get("contract_boundary"),
        },
        "engine_capabilities": {
            "ok": engine.get("ok"),
            "engines": engine.get("engines"),
            "repository_template_state": engine.get("repository_template_state"),
            "performance_qualification": engine.get("performance_qualification"),
        },
        "compute_qualification": {
            "ok": qualification.get("ok"),
            "repository_state": qualification.get("repository_state"),
            "performance_evaluated": qualification.get("performance_evaluated"),
            "workers_bounded_by": qualification.get("workers_bounded_by"),
            "benchmark_result_contract": qualification.get("benchmark_result_contract"),
            "input_model": qualification.get("input_model"),
            "normalization_mandatory": qualification.get("normalization_mandatory"),
            "native_semantic_validation": qualification.get("native_semantic_validation"),
            "legacy_projection_retained": qualification.get("legacy_projection_retained"),
            "legacy_projection_consumed": qualification.get("legacy_projection_consumed"),
            "legacy_projection_qualification_impact": qualification.get("legacy_projection_qualification_impact"),
            "identity_invariants": qualification.get("identity_invariants"),
        },
        "performance_ratio_published": False,
        "errors": errors,
        "non_claims": [
            "This evidence captures repository contracts, not external engine execution.",
            "EXTERNAL_HOLD does not establish numerical or performance qualification.",
            "Campaign v1.0 migration expands role declarations but creates no execution evidence.",
            "Campaign migration cannot remove benchmark-result provenance gaps or lift EXTERNAL_HOLD.",
            "Legacy flat benchmark-result v1.0 migration does not recover missing provenance.",
            "Legacy nested benchmark-result v1.0 is centrally migrated before v1.1 semantics.",
            "No nested v1.0 semantic downgrade view is used.",
            "compute_qualification_view remains diagnostic and is not qualification input.",
            "No CPU/GPU performance ratio is published without accepted real-engine results.",
        ],
    }


def write_report(path: Path | None, report: dict[str, Any]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("compute-contract-evidence.json"))
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args()
    report = build_report()
    write_report(args.out, report)
    if args.json_output:
        print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))
    else:
        print(f"Compute contract evidence: {report['state']}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate the bounded canonical CPU/accelerator qualification workflow and hold template."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "skills" / "tsao-dft-hpc-provenance" / "scripts" / "qualify_compute_campaign.py"
CONTRACT_PATH = ROOT / "skills" / "tsao-dft-hpc-provenance" / "scripts" / "benchmark_contract.py"
CAMPAIGN_PATH = ROOT / "skills" / "tsao-dft-hpc-provenance" / "templates" / "compute-qualification-campaign.yaml"


def load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("tsao_compute_qualification_validation", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def validate() -> dict[str, Any]:
    errors: list[str] = []
    campaign: dict[str, Any] = {}
    hold_report: dict[str, Any] = {}
    try:
        module = load_module()
        campaign = module.load_campaign(CAMPAIGN_PATH)
        errors.extend(module.validate_campaign(campaign))
        hold_report = module.qualify(campaign, [])

        if hold_report.get("state") != module.EXTERNAL_HOLD:
            errors.append("repository qualification template must remain EXTERNAL_HOLD")
        if hold_report.get("performance", {}).get("evaluated") is not False:
            errors.append("repository qualification template must not evaluate performance")
        if hold_report.get("workers_bounded_by") != module.MAX_WORKERS:
            errors.append("qualification worker bound is not stable")
        if hold_report.get("benchmark_result_contract") != "canonical-nested-v1.1":
            errors.append("compute qualification does not declare the canonical nested v1.1 contract")
        if hold_report.get("input_model") != "canonical-nested-v1.1-typed-accessor":
            errors.append("compute qualification does not use the canonical typed-accessor input model")
        if hold_report.get("normalization_mandatory") is not True:
            errors.append("compute qualification does not declare central normalization mandatory")
        if hold_report.get("native_semantic_validation") is not True:
            errors.append("compute qualification does not declare native semantic validation")
        if hold_report.get("legacy_projection_consumed") is not False:
            errors.append("compute qualification still consumes the legacy flat projection")
        if hold_report.get("legacy_projection_status") != module.PROJECTION_STATUS:
            errors.append("legacy projection status is not explicit and stable")
        if module.normalized_workers(10_000, 10_000) != module.MAX_WORKERS:
            errors.append("qualification worker normalization does not enforce the hard bound")

        custom_documents, custom_errors = module.load_results(
            [],
            {"properties": {"schema_version": {"const": "9.9"}}},
        )
        if custom_documents or not any("authoritative nested v1.1" in item for item in custom_errors):
            errors.append("custom schema input was not rejected from compute qualification")

        bypass = module.qualify(campaign, [{"schema_version": "9.9", "candidate_id": "unknown"}])
        if bypass.get("performance", {}).get("evaluated") is not False or not bypass.get("errors"):
            errors.append("raw unknown evidence bypassed central normalization")

        source = MODULE_PATH.read_text(encoding="utf-8")
        contract_source = CONTRACT_PATH.read_text(encoding="utf-8")
        if "ThreadPoolExecutor" not in source or "executor.map" not in source:
            errors.append("qualification workflow lacks deterministic bounded concurrency")
        if "contract.normalize_record" not in source:
            errors.append("qualification workflow does not use the central benchmark adapter")
        if "performance.validate_canonical_result" not in source:
            errors.append("qualification workflow does not run native canonical semantics")
        if "class CampaignDocument" not in source:
            errors.append("qualification workflow lacks the typed canonical document accessor")
        if "compute_qualification_view" in source:
            errors.append("qualification workflow still references compute_qualification_view")
        if "def compute_qualification_view" not in contract_source:
            errors.append("legacy diagnostic projection was removed without a compatibility deprecation cycle")
        if "normalized, _ = normalize_record(canonical)" not in contract_source:
            errors.append("legacy diagnostic projection no longer routes through central normalization")
        if len(hold_report.get("identity_invariants") or []) < 7:
            errors.append("compute qualification identity invariants are incomplete")
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        errors.append(str(exc))

    return {
        "ok": not errors,
        "campaign": campaign.get("campaign_id"),
        "repository_state": hold_report.get("state"),
        "performance_evaluated": hold_report.get("performance", {}).get("evaluated"),
        "benchmark_result_contract": hold_report.get("benchmark_result_contract"),
        "input_model": hold_report.get("input_model"),
        "normalization_mandatory": hold_report.get("normalization_mandatory"),
        "native_semantic_validation": hold_report.get("native_semantic_validation"),
        "legacy_projection_retained": True,
        "legacy_projection_consumed": hold_report.get("legacy_projection_consumed"),
        "legacy_projection_qualification_impact": "NOT_ELIGIBLE",
        "identity_invariants": hold_report.get("identity_invariants"),
        "workers_bounded_by": 8,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args()
    report = validate()
    if args.json_output:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for error in report["errors"]:
            print(f"FAIL: {error}")
        print(f"Compute qualification validation: {'PASS' if report['ok'] else 'FAIL'}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

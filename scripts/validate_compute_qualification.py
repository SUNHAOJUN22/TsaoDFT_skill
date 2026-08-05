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
    try:
        module = load_module()
        campaign = module.load_campaign(CAMPAIGN_PATH)
    except (OSError, RuntimeError, ValueError) as exc:
        return {"ok": False, "errors": [str(exc)]}
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
    if module.normalized_workers(10_000, 10_000) != module.MAX_WORKERS:
        errors.append("qualification worker normalization does not enforce the hard bound")
    source = MODULE_PATH.read_text(encoding="utf-8")
    if "ThreadPoolExecutor" not in source or "executor.map" not in source:
        errors.append("qualification workflow lacks deterministic bounded concurrency")
    if "benchmark_contract" not in source:
        errors.append("qualification workflow does not use the benchmark contract adapter")
    return {
        "ok": not errors,
        "campaign": campaign.get("campaign_id"),
        "repository_state": hold_report.get("state"),
        "performance_evaluated": hold_report.get("performance", {}).get("evaluated"),
        "benchmark_result_contract": hold_report.get("benchmark_result_contract"),
        "workers_bounded_by": module.MAX_WORKERS,
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

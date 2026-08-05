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
    "engine_capabilities": ROOT / "scripts" / "validate_engine_capabilities.py",
    "compute_qualification": ROOT / "scripts" / "validate_compute_qualification.py",
}
SCHEMA_VERSION = "1.0"
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
    engine = reports.get("engine_capabilities", {})
    qualification = reports.get("compute_qualification", {})
    validated_surfaces = registry.get("validated_surfaces") or []
    if "runtime_single_source" not in validated_surfaces:
        errors.append("acceleration registry runtime single source is not validated")
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

    return {
        "ok": not errors,
        "schema_version": SCHEMA_VERSION,
        "state": EXTERNAL_HOLD if not errors else UNQUALIFIED,
        "scope": "repository templates and permanent validators only",
        "external_engine_invoked": False,
        "acceleration_registry": {
            "ok": registry.get("ok"),
            "registry_version": registry.get("registry_version"),
            "libraries": registry.get("libraries"),
            "runtime_single_source": "runtime_single_source" in validated_surfaces,
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
        },
        "performance_ratio_published": False,
        "errors": errors,
        "non_claims": [
            "This evidence captures repository contracts, not external engine execution.",
            "EXTERNAL_HOLD does not establish numerical or performance qualification.",
            "No CPU/GPU performance ratio is published without accepted real-engine results.",
        ],
    }


def write_report(path: Path | None, report: dict[str, Any]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("compute-contract-evidence.json"))
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args()
    report = build_report()
    write_report(args.out, report)
    if args.json_output:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"Compute contract evidence: {report['state']}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

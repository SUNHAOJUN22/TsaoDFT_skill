#!/usr/bin/env python3
"""Validate an engine-aware HPC execution manifest."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import yaml

ENGINES = {"gaussian", "vasp", "quantum-espresso", "cp2k", "generic"}
SCHED = {"local", "slurm", "pbs"}
APPROVAL = {"pending", "approved", "rejected", "not_required"}
LEVELS = {"L0_REFERENCE", "L1_HANDOFF", "L2_VALIDATED_ADAPTER", "L3_EXECUTION_TESTED"}
THREAD_VARIABLES = {
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "BLIS_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "NUMEXPR_MAX_THREADS",
}
ACCELERATOR_BACKENDS = {"none", "cuda", "hip", "sycl", "openacc", "openmp-offload", "metal"}
ACCELERATOR_MODES = {"none", "engine-native", "ml-surrogate", "custom-native", "workflow"}
GPU_VENDORS = {"none", "nvidia", "amd", "intel", "apple"}
CPU_BINDINGS = {"none", "cores", "threads"}
DEVICE_ORDERS = {"scheduler", "pci_bus_id"}
PRECISIONS = {"fp64", "mixed-validated", "mixed-experimental"}
GPU_BIND_RE = re.compile(r"^(?:none|closest|map:\d+(?:,\d+)*)$")


def integer(value: Any, name: str, errors: list[str], minimum: int = 0) -> int:
    try:
        result = int(value)
    except (TypeError, ValueError):
        errors.append(f"{name} must be integer")
        return minimum
    if result < minimum:
        errors.append(f"{name} must be >={minimum}")
    return result


def validate_acceleration(
    manifest: dict[str, Any],
    resources: dict[str, Any],
    errors: list[str],
    warnings: list[str],
) -> None:
    acceleration = manifest.get("acceleration")
    if acceleration is None:
        if (
            integer(
                resources.get("gpus_per_node", resources.get("gpus", 0)),
                "gpus_per_node",
                errors,
                0,
            )
            > 0
        ):
            warnings.append("GPU resources are requested without an acceleration provenance contract")
        return
    if not isinstance(acceleration, dict):
        errors.append("acceleration must be a mapping")
        return

    enabled = bool(acceleration.get("enabled", False))
    backend = str(acceleration.get("backend", "none")).lower()
    mode = str(acceleration.get("mode", "none")).lower()
    vendor = str(acceleration.get("gpu_vendor", "none")).lower()
    cpu_bind = str(acceleration.get("cpu_bind", "none")).lower()
    gpu_bind = str(acceleration.get("gpu_bind", "none")).lower()
    device_order = str(acceleration.get("device_order", "scheduler")).lower()
    precision = str(acceleration.get("precision", "fp64")).lower()
    ranks_per_gpu = integer(
        acceleration.get("ranks_per_gpu", 1),
        "acceleration.ranks_per_gpu",
        errors,
        1,
    )
    gpus_per_node = integer(
        resources.get("gpus_per_node", resources.get("gpus", 0)),
        "gpus_per_node",
        errors,
        0,
    )
    tasks_per_node = integer(resources.get("tasks_per_node", 0), "tasks_per_node", errors, 1)

    if backend not in ACCELERATOR_BACKENDS:
        errors.append(f"acceleration.backend must be one of {sorted(ACCELERATOR_BACKENDS)}")
    if mode not in ACCELERATOR_MODES:
        errors.append(f"acceleration.mode must be one of {sorted(ACCELERATOR_MODES)}")
    if vendor not in GPU_VENDORS:
        errors.append(f"acceleration.gpu_vendor must be one of {sorted(GPU_VENDORS)}")
    if cpu_bind not in CPU_BINDINGS:
        errors.append(f"acceleration.cpu_bind must be one of {sorted(CPU_BINDINGS)}")
    if GPU_BIND_RE.fullmatch(gpu_bind) is None:
        errors.append("acceleration.gpu_bind must be none, closest or map:<comma-separated GPU IDs>")
    if device_order not in DEVICE_ORDERS:
        errors.append(f"acceleration.device_order must be one of {sorted(DEVICE_ORDERS)}")
    if precision not in PRECISIONS:
        errors.append(f"acceleration.precision must be one of {sorted(PRECISIONS)}")

    if not enabled:
        if backend != "none" or mode != "none":
            warnings.append("disabled acceleration contract should normally use backend=none and mode=none")
        return

    if gpus_per_node < 1:
        errors.append("enabled acceleration requires resources.gpus_per_node >=1")
    if backend == "none" or mode == "none" or vendor == "none":
        errors.append("enabled acceleration requires non-none backend, mode and gpu_vendor")
    if backend in {"cuda", "openacc"} and vendor != "nvidia":
        errors.append(f"acceleration.backend={backend} requires gpu_vendor=nvidia")
    if backend == "metal" and vendor != "apple":
        errors.append("acceleration.backend=metal requires gpu_vendor=apple")
    if backend == "hip" and vendor not in {"amd", "nvidia"}:
        errors.append("acceleration.backend=hip requires gpu_vendor=amd or nvidia")

    allow_oversubscription = bool(acceleration.get("allow_gpu_oversubscription", False))
    if ranks_per_gpu > 1 and not allow_oversubscription:
        errors.append("ranks_per_gpu >1 requires acceleration.allow_gpu_oversubscription=true")
    expected_tasks = gpus_per_node * ranks_per_gpu
    if gpus_per_node and tasks_per_node != expected_tasks:
        errors.append("tasks_per_node must equal gpus_per_node * acceleration.ranks_per_gpu")

    if not str(acceleration.get("profile_id", "")).strip():
        errors.append("enabled acceleration requires acceleration.profile_id")
    if mode in {"engine-native", "custom-native"} and not str(
        acceleration.get("build_fingerprint_id", "")
    ).strip():
        errors.append(f"acceleration.mode={mode} requires acceleration.build_fingerprint_id")
    if not str(acceleration.get("benchmark_plan_id", "")).strip():
        errors.append("enabled acceleration requires acceleration.benchmark_plan_id")

    scheduler = str(manifest.get("scheduler", ""))
    launcher = str(manifest.get("launcher", ""))
    if launcher == "auto" and scheduler != "slurm":
        errors.append("launcher=auto is currently supported only for Slurm")
    if scheduler != "slurm" and gpu_bind != "none":
        warnings.append(
            "GPU binding is site-specific outside Slurm and must be verified in the explicit launcher"
        )
    if precision != "fp64":
        warnings.append("mixed precision requires property-specific comparison with an FP64 reference")

    variables = (manifest.get("environment") or {}).get("variables") or {}
    if "CUDA_VISIBLE_DEVICES" in variables and scheduler in {"slurm", "pbs"}:
        warnings.append("avoid hard-coded CUDA_VISIBLE_DEVICES under a scheduler; use scheduler GPU binding")
    if vendor == "nvidia" and device_order == "pci_bus_id":
        configured_order = str(variables.get("CUDA_DEVICE_ORDER", ""))
        if configured_order and configured_order != "PCI_BUS_ID":
            errors.append("device_order=pci_bus_id conflicts with environment.variables.CUDA_DEVICE_ORDER")


def validate(d: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    for key in [
        "schema_version",
        "job_id",
        "engine",
        "engine_version",
        "support_level",
        "method_fingerprint_id",
        "executable",
        "input",
        "workdir",
        "scheduler",
        "resources",
        "environment",
        "expected_outputs",
        "checkpoint_policy",
        "preflight",
        "parser",
        "approval",
    ]:
        if key not in d:
            errors.append(f"missing {key}")
    if d.get("engine") not in ENGINES:
        errors.append("unsupported engine")
    if d.get("scheduler") not in SCHED:
        errors.append("unsupported scheduler")
    if d.get("approval") not in APPROVAL:
        errors.append("invalid approval")
    if d.get("support_level") not in LEVELS:
        errors.append("invalid support_level")

    resources = d.get("resources") or {}
    if not isinstance(resources, dict):
        errors.append("resources must be a mapping")
        resources = {}
    for key in ["nodes", "tasks_per_node", "cpus_per_task", "memory_gb", "walltime"]:
        if key not in resources:
            errors.append(f"resources missing {key}")
    for key in ["nodes", "tasks_per_node", "cpus_per_task"]:
        integer(resources.get(key, 0), key, errors, 1)
    try:
        if float(resources.get("memory_gb", 0)) <= 0:
            errors.append("memory_gb must be positive")
    except (TypeError, ValueError):
        errors.append("memory_gb must be numeric")
    if not re.match(r"^(?:\d+-)?\d{1,3}:\d{2}:\d{2}$", str(resources.get("walltime", ""))):
        errors.append("walltime must be HH:MM:SS or D-HH:MM:SS")

    tasks_per_node = integer(resources.get("tasks_per_node", 0), "tasks_per_node", errors, 1)
    cpus_per_task = integer(resources.get("cpus_per_task", 0), "cpus_per_task", errors, 1)
    if resources.get("cpus_per_node") is not None:
        cpus_per_node = integer(resources["cpus_per_node"], "cpus_per_node", errors, 1)
        if tasks_per_node * cpus_per_task > cpus_per_node:
            errors.append("tasks_per_node * cpus_per_task exceeds cpus_per_node")

    environment = d.get("environment") or {}
    variables = (environment.get("variables") or {}) if isinstance(environment, dict) else {}
    for name in sorted(THREAD_VARIABLES & set(variables)):
        threads = integer(variables[name], name, errors, 1)
        if cpus_per_task and threads > cpus_per_task:
            errors.append(f"{name} exceeds resources.cpus_per_task")

    validate_acceleration(d, resources, errors, warnings)

    if not d.get("expected_outputs"):
        errors.append("expected_outputs must not be empty")
    if not (d.get("preflight") or {}).get("command"):
        errors.append("preflight.command required")
    if not (d.get("parser") or {}).get("command"):
        errors.append("parser.command required")
    if d.get("approval") == "approved" and d.get("support_level") == "L0_REFERENCE":
        errors.append("documentation-only support cannot be approved for execution")
    if d.get("approval") == "approved" and errors:
        errors.append("approved manifest has validation errors")
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    loaded = yaml.safe_load(args.manifest.read_text(encoding="utf-8")) or {}
    if not isinstance(loaded, dict):
        errors, warnings = ["manifest root must be a mapping"], []
    else:
        errors, warnings = validate(loaded)
    print(json.dumps({"ok": not errors, "errors": errors, "warnings": warnings}, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Materialize a reviewed acceleration profile into HPC manifests and a benchmark matrix."""

from __future__ import annotations

import argparse
import copy
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from plan_acceleration import build_plan  # noqa: E402 -- local imports follow SCRIPT_DIR path setup
from validate_hpc_manifest import validate as validate_manifest  # noqa: E402

BACKEND_BY_VENDOR = {
    "none": "none",
    "nvidia": "cuda",
    "amd": "hip",
    "intel": "sycl",
    "apple": "metal",
}
MODE_BY_STAGE = {
    "engine": "engine-native",
    "ml-surrogate": "ml-surrogate",
    "postprocessing": "custom-native",
    "workflow": "workflow",
}
MATRIX_FIELDS = [
    "candidate_id",
    "role",
    "nodes",
    "gpus_per_node",
    "ranks_per_gpu",
    "tasks_per_node",
    "cpus_per_task",
    "backend",
    "precision",
    "cpu_bind",
    "gpu_bind",
    "scientific_equivalence",
]


def identifier(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip()).strip("-")
    return cleaned or "unnamed"


def positive_integer(value: Any, name: str, minimum: int = 1) -> int:
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if result < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    return result


def read_mapping(path: Path, label: str) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(loaded, dict):
        raise ValueError(f"{label} root must be a mapping")
    return loaded


def acceleration_contract(profile: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    hardware = profile.get("hardware") or {}
    software = profile.get("software") or {}
    policy = profile.get("policy") or {}
    binding = profile.get("binding") or {}
    benchmark = profile.get("benchmark") or {}
    engine = str(profile["engine"]).lower()
    stage = str(profile["stage"]).lower()
    vendor = str(hardware.get("gpu_vendor", "none")).lower()
    gpus_per_node = positive_integer(hardware.get("gpus_per_node", 0), "hardware.gpus_per_node", 0)
    ranks_per_gpu = positive_integer(binding.get("ranks_per_gpu", 1), "binding.ranks_per_gpu")
    allow_oversubscription = bool(binding.get("allow_gpu_oversubscription", False))
    if ranks_per_gpu > 1 and not allow_oversubscription:
        raise ValueError("binding.ranks_per_gpu >1 requires binding.allow_gpu_oversubscription=true")

    profile_id = str(profile.get("profile_id", f"ACCEL-{engine}-{hardware.get('gpu_model', vendor)}"))
    build_fingerprint_id = str(software.get("build_fingerprint_id", "")).strip()
    benchmark_plan_id = str(benchmark.get("plan_id", "")).strip()
    mode = MODE_BY_STAGE[stage]
    if mode in {"engine-native", "custom-native"} and not build_fingerprint_id:
        raise ValueError("software.build_fingerprint_id is required for native acceleration")
    if not benchmark_plan_id:
        raise ValueError("benchmark.plan_id is required")

    backend = str(software.get("backend", BACKEND_BY_VENDOR[vendor])).lower()
    gpu_bind = str(binding.get("gpu_bind", "closest" if gpus_per_node else "none")).lower()
    cpu_bind = str(binding.get("cpu_bind", "cores" if gpus_per_node else "none")).lower()
    device_order = str(binding.get("device_order", "pci_bus_id" if vendor == "nvidia" else "scheduler")).lower()
    return {
        "enabled": gpus_per_node > 0,
        "profile_id": profile_id,
        "backend": backend,
        "mode": mode,
        "gpu_vendor": vendor,
        "ranks_per_gpu": ranks_per_gpu,
        "allow_gpu_oversubscription": allow_oversubscription,
        "cpu_bind": cpu_bind,
        "gpu_bind": gpu_bind,
        "device_order": device_order,
        "precision": str(policy.get("precision", "fp64")).lower(),
        "build_fingerprint_id": build_fingerprint_id,
        "benchmark_plan_id": benchmark_plan_id,
        "record_runtime": bool(binding.get("record_runtime", True)),
        "runtime_record": str(binding.get("runtime_record", "tsao-acceleration-runtime.txt")),
        "device_inventory": str(binding.get("device_inventory", "tsao-nvidia-gpu-inventory.csv")),
        "recommended_path": plan["recommended_path"],
    }


def materialize_manifest(
    base_manifest: dict[str, Any],
    profile: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    plan = build_plan(profile)
    if not plan.get("ok", False):
        raise ValueError("; ".join(plan.get("errors", ["acceleration plan is invalid"])))

    hardware = profile.get("hardware") or {}
    contract = acceleration_contract(profile, plan)
    gpus_per_node = positive_integer(hardware.get("gpus_per_node", 0), "hardware.gpus_per_node", 0)
    ranks_per_gpu = int(contract["ranks_per_gpu"])
    cpus_per_gpu = positive_integer(hardware.get("cpus_per_gpu", 1), "hardware.cpus_per_gpu")
    if gpus_per_node and cpus_per_gpu % ranks_per_gpu:
        raise ValueError("hardware.cpus_per_gpu must be divisible by binding.ranks_per_gpu")

    manifest = copy.deepcopy(base_manifest)
    resources = manifest.setdefault("resources", {})
    resources["nodes"] = positive_integer(hardware.get("nodes", resources.get("nodes", 1)), "hardware.nodes")
    resources["gpus_per_node"] = gpus_per_node
    if gpus_per_node:
        resources["tasks_per_node"] = gpus_per_node * ranks_per_gpu
        resources["cpus_per_task"] = cpus_per_gpu // ranks_per_gpu
    else:
        resources["tasks_per_node"] = positive_integer(
            hardware.get("tasks_per_node", resources.get("tasks_per_node", 1)),
            "hardware.tasks_per_node",
        )
        resources["cpus_per_task"] = positive_integer(
            hardware.get("cpus_per_task", resources.get("cpus_per_task", 1)),
            "hardware.cpus_per_task",
        )

    manifest["launcher"] = "auto" if manifest.get("scheduler") == "slurm" else manifest.get("launcher", "")
    manifest["acceleration"] = contract
    environment = manifest.setdefault("environment", {})
    variables = environment.setdefault("variables", {})
    if contract["gpu_vendor"] == "nvidia" and contract["device_order"] == "pci_bus_id":
        variables.setdefault("CUDA_DEVICE_ORDER", "PCI_BUS_ID")
    variables.setdefault("OMP_NUM_THREADS", str(resources["cpus_per_task"]))

    errors, warnings = validate_manifest(manifest)
    if errors:
        raise ValueError("materialized manifest is invalid: " + "; ".join(errors))
    return manifest, plan, warnings


def benchmark_rows(profile: dict[str, Any], manifest: dict[str, Any]) -> list[dict[str, Any]]:
    hardware = profile.get("hardware") or {}
    benchmark = profile.get("benchmark") or {}
    contract = manifest["acceleration"]
    max_gpus = int(manifest["resources"].get("gpus_per_node", 0))
    cpu_reference_tasks = positive_integer(
        benchmark.get("cpu_reference_tasks_per_node", hardware.get("tasks_per_node", 1)),
        "benchmark.cpu_reference_tasks_per_node",
    )
    cpu_reference_threads = positive_integer(
        benchmark.get("cpu_reference_cpus_per_task", hardware.get("cpus_per_task", 1)),
        "benchmark.cpu_reference_cpus_per_task",
    )
    rows: list[dict[str, Any]] = [
        {
            "candidate_id": "cpu-reference",
            "role": "scientific-reference",
            "nodes": 1,
            "gpus_per_node": 0,
            "ranks_per_gpu": 0,
            "tasks_per_node": cpu_reference_tasks,
            "cpus_per_task": cpu_reference_threads,
            "backend": "none",
            "precision": "fp64",
            "cpu_bind": "cores",
            "gpu_bind": "none",
            "scientific_equivalence": "identical input, method fingerprint and convergence thresholds",
        }
    ]
    if max_gpus == 0:
        return rows

    gpu_counts = benchmark.get("gpu_counts") or [1, max_gpus]
    rank_counts = benchmark.get("ranks_per_gpu") or [1]
    node_counts = benchmark.get("node_counts") or [1]
    seen: set[tuple[int, int, int]] = set()
    for nodes_value in node_counts:
        nodes = positive_integer(nodes_value, "benchmark.node_counts[]")
        for gpu_value in gpu_counts:
            gpus = positive_integer(gpu_value, "benchmark.gpu_counts[]")
            if gpus > max_gpus:
                raise ValueError("benchmark.gpu_counts cannot exceed hardware.gpus_per_node")
            for rank_value in rank_counts:
                ranks = positive_integer(rank_value, "benchmark.ranks_per_gpu[]")
                key = (nodes, gpus, ranks)
                if key in seen:
                    continue
                seen.add(key)
                if ranks > 1 and not contract["allow_gpu_oversubscription"]:
                    raise ValueError("benchmark ranks_per_gpu >1 requires GPU oversubscription approval")
                cpus_per_gpu = positive_integer(hardware.get("cpus_per_gpu", 1), "hardware.cpus_per_gpu")
                if cpus_per_gpu % ranks:
                    raise ValueError("hardware.cpus_per_gpu must be divisible by every benchmark ranks_per_gpu")
                rows.append(
                    {
                        "candidate_id": f"gpu-n{nodes}-g{gpus}-r{ranks}",
                        "role": "acceleration-candidate",
                        "nodes": nodes,
                        "gpus_per_node": gpus,
                        "ranks_per_gpu": ranks,
                        "tasks_per_node": gpus * ranks,
                        "cpus_per_task": cpus_per_gpu // ranks,
                        "backend": contract["backend"],
                        "precision": contract["precision"],
                        "cpu_bind": contract["cpu_bind"],
                        "gpu_bind": contract["gpu_bind"],
                        "scientific_equivalence": "identical input, method fingerprint and convergence thresholds",
                    }
                )
    return rows


def candidate_manifest(
    base: dict[str, Any],
    accelerated: dict[str, Any],
    row: dict[str, Any],
) -> dict[str, Any]:
    source = base if row["role"] == "scientific-reference" else accelerated
    candidate = copy.deepcopy(source)
    candidate["job_id"] = identifier(f"{source.get('job_id', 'JOB')}-{row['candidate_id']}")
    candidate["approval"] = "pending"
    candidate["launcher"] = "auto" if candidate.get("scheduler") == "slurm" else candidate.get("launcher", "")
    resources = candidate.setdefault("resources", {})
    for key in ("nodes", "gpus_per_node", "tasks_per_node", "cpus_per_task"):
        resources[key] = int(row[key])

    if row["role"] == "scientific-reference":
        candidate["acceleration"] = {
            "enabled": False,
            "profile_id": "CPU-REFERENCE",
            "backend": "none",
            "mode": "none",
            "gpu_vendor": "none",
            "ranks_per_gpu": 1,
            "allow_gpu_oversubscription": False,
            "cpu_bind": "none",
            "gpu_bind": "none",
            "device_order": "scheduler",
            "precision": "fp64",
            "record_runtime": False,
        }
    else:
        acceleration = candidate["acceleration"]
        acceleration["ranks_per_gpu"] = int(row["ranks_per_gpu"])
        acceleration["precision"] = row["precision"]
        acceleration["cpu_bind"] = row["cpu_bind"]
        acceleration["gpu_bind"] = row["gpu_bind"]

    variables = candidate.setdefault("environment", {}).setdefault("variables", {})
    variables["OMP_NUM_THREADS"] = str(row["cpus_per_task"])
    errors, _ = validate_manifest(candidate)
    if errors:
        raise ValueError(f"candidate {row['candidate_id']} is invalid: {'; '.join(errors)}")
    return candidate


def write_outputs(
    base: dict[str, Any],
    accelerated: dict[str, Any],
    plan: dict[str, Any],
    rows: list[dict[str, Any]],
    manifest_out: Path,
    matrix_out: Path,
    candidate_dir: Path,
    plan_out: Path | None,
) -> list[str]:
    manifest_out.parent.mkdir(parents=True, exist_ok=True)
    matrix_out.parent.mkdir(parents=True, exist_ok=True)
    candidate_dir.mkdir(parents=True, exist_ok=True)
    manifest_out.write_text(yaml.safe_dump(accelerated, sort_keys=False), encoding="utf-8")
    with matrix_out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MATRIX_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    if plan_out is not None:
        plan_out.parent.mkdir(parents=True, exist_ok=True)
        plan_out.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    written: list[str] = []
    for row in rows:
        path = candidate_dir / f"{identifier(str(row['candidate_id']))}.yaml"
        candidate = candidate_manifest(base, accelerated, row)
        path.write_text(yaml.safe_dump(candidate, sort_keys=False), encoding="utf-8")
        written.append(str(path))
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base_manifest", type=Path)
    parser.add_argument("acceleration_profile", type=Path)
    parser.add_argument("--manifest-out", type=Path, required=True)
    parser.add_argument("--matrix-out", type=Path, required=True)
    parser.add_argument("--candidate-dir", type=Path, required=True)
    parser.add_argument("--plan-out", type=Path)
    args = parser.parse_args()
    try:
        base = read_mapping(args.base_manifest, "base manifest")
        profile = read_mapping(args.acceleration_profile, "acceleration profile")
        accelerated, plan, warnings = materialize_manifest(base, profile)
        rows = benchmark_rows(profile, accelerated)
        candidates = write_outputs(
            base,
            accelerated,
            plan,
            rows,
            args.manifest_out,
            args.matrix_out,
            args.candidate_dir,
            args.plan_out,
        )
    except (OSError, ValueError, KeyError) as exc:
        print(json.dumps({"ok": False, "errors": [str(exc)]}, indent=2))
        return 1
    print(
        json.dumps(
            {
                "ok": True,
                "manifest": str(args.manifest_out),
                "matrix": str(args.matrix_out),
                "candidates": candidates,
                "warnings": warnings,
                "submission": "not_performed",
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

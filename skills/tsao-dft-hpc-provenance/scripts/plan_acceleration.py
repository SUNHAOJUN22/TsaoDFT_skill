#!/usr/bin/env python3
"""Create an evidence-bounded DFT/GPU acceleration plan from a YAML profile."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import yaml

ENGINES = {"gaussian", "vasp", "quantum-espresso", "cp2k", "generic"}
STAGES = {"engine", "ml-surrogate", "postprocessing", "workflow"}
TARGETS = {"edge", "workstation", "hpc"}
GPU_VENDORS = {"none", "nvidia", "amd", "intel", "apple"}
PRECISIONS = {"fp64", "mixed-validated", "mixed-experimental"}

LIBRARIES: dict[str, dict[str, str]] = {
    "cublas": {
        "category": "dense-linear-algebra",
        "purpose": "GPU BLAS for dense matrix operations used by compatible engine builds or custom kernels.",
    },
    "cusolver": {
        "category": "dense-solvers",
        "purpose": "GPU factorizations and eigensolvers for compatible engine builds or custom kernels.",
    },
    "cusolvermp": {
        "category": "distributed-dense-solvers",
        "purpose": "ScaLAPACK-like multi-process, multi-GPU dense linear algebra for explicit integrations.",
    },
    "cufft": {
        "category": "fft",
        "purpose": "Single-process GPU FFT primitives used by compatible plane-wave engine builds.",
    },
    "cufftmp": {
        "category": "distributed-fft",
        "purpose": "Multi-process, multi-GPU FFTs for an engine or custom code that explicitly integrates them.",
    },
    "cusparse": {
        "category": "sparse-linear-algebra",
        "purpose": "Sparse matrix primitives for localized-basis or custom sparse solvers.",
    },
    "nccl": {
        "category": "collectives",
        "purpose": "GPU collectives for compatible multi-GPU engine builds and custom distributed kernels.",
    },
    "nvshmem": {
        "category": "gpu-one-sided-communication",
        "purpose": "GPU-initiated communication for explicitly integrated multi-GPU and multi-node kernels.",
    },
    "cutensor": {
        "category": "tensor-contractions",
        "purpose": "Optimized tensor contractions, reductions and permutations for custom tensor workloads.",
    },
    "cuequivariance": {
        "category": "equivariant-ml",
        "purpose": "Optimized equivariant neural-network operations for atomistic ML training and inference.",
    },
    "cutlass": {
        "category": "custom-kernels",
        "purpose": "C++ templates for bespoke GEMM and tensor-core kernels after profiling proves a need.",
    },
}

ALIASES = {
    re.sub(r"[^a-z0-9]", "", name.lower()): name
    for name in LIBRARIES
}


def normalize_library(value: str) -> str:
    key = re.sub(r"[^a-z0-9]", "", value.lower())
    return ALIASES.get(key, key)


def integer(value: Any, name: str, errors: list[str], minimum: int = 0) -> int:
    try:
        result = int(value)
    except (TypeError, ValueError):
        errors.append(f"{name} must be an integer")
        return minimum
    if result < minimum:
        errors.append(f"{name} must be >= {minimum}")
    return result


def validate(profile: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    engine = str(profile.get("engine", "")).lower()
    stage = str(profile.get("stage", "")).lower()
    hardware = profile.get("hardware") or {}
    software = profile.get("software") or {}
    policy = profile.get("policy") or {}

    if engine not in ENGINES:
        errors.append(f"engine must be one of {sorted(ENGINES)}")
    if stage not in STAGES:
        errors.append(f"stage must be one of {sorted(STAGES)}")

    target = str(hardware.get("target", "")).lower()
    vendor = str(hardware.get("gpu_vendor", "none")).lower()
    if target not in TARGETS:
        errors.append(f"hardware.target must be one of {sorted(TARGETS)}")
    if vendor not in GPU_VENDORS:
        errors.append(f"hardware.gpu_vendor must be one of {sorted(GPU_VENDORS)}")

    nodes = integer(hardware.get("nodes", 1), "hardware.nodes", errors, 1)
    gpus = integer(hardware.get("gpus_per_node", 0), "hardware.gpus_per_node", errors, 0)
    integer(hardware.get("cpus_per_gpu", 8), "hardware.cpus_per_gpu", errors, 1)
    if vendor == "none" and gpus:
        errors.append("hardware.gpus_per_node requires a non-none gpu_vendor")
    if vendor != "none" and gpus == 0:
        warnings.append("GPU vendor is declared but gpus_per_node is zero")
    if nodes > 1 and str(hardware.get("interconnect", "none")).lower() == "none":
        warnings.append("multi-node profile should record the interconnect")

    precision = str(policy.get("precision", "fp64")).lower()
    if precision not in PRECISIONS:
        errors.append(f"policy.precision must be one of {sorted(PRECISIONS)}")
    if precision != "fp64":
        warnings.append("mixed precision requires property-specific numerical validation against an FP64 baseline")

    libraries = software.get("libraries") or []
    if not isinstance(libraries, list):
        errors.append("software.libraries must be a list")
    else:
        unknown = sorted({normalize_library(str(item)) for item in libraries} - set(LIBRARIES))
        if unknown:
            errors.append(f"unknown acceleration libraries: {unknown}")
        if vendor != "nvidia" and libraries:
            warnings.append("NVIDIA CUDA-X libraries are not portable to the declared GPU vendor")

    if target == "edge" and stage == "engine":
        warnings.append("edge devices should normally orchestrate or infer, not host production DFT kernels")
    if bool(software.get("engine_gpu_build")) and (vendor != "nvidia" or gpus == 0):
        errors.append("engine_gpu_build requires at least one NVIDIA GPU")
    return errors, warnings


def recommended_path(profile: dict[str, Any]) -> str:
    stage = str(profile["stage"]).lower()
    target = str((profile.get("hardware") or {})["target"]).lower()
    vendor = str((profile.get("hardware") or {}).get("gpu_vendor", "none")).lower()
    gpu_build = bool((profile.get("software") or {}).get("engine_gpu_build"))
    if target == "edge":
        return "edge-gpu-surrogate" if stage == "ml-surrogate" and vendor != "none" else "edge-orchestrated-remote-dft"
    if stage == "ml-surrogate" and vendor == "nvidia":
        return "cuda-accelerated-atomistic-ml"
    if stage == "engine" and vendor == "nvidia" and gpu_build:
        return "engine-native-gpu"
    if vendor == "none":
        return "cpu-mpi-openmp"
    return "portable-accelerator-benchmark"


def library_decision(name: str, profile: dict[str, Any]) -> tuple[str, str]:
    engine = str(profile["engine"]).lower()
    stage = str(profile["stage"]).lower()
    hardware = profile.get("hardware") or {}
    software = profile.get("software") or {}
    vendor = str(hardware.get("gpu_vendor", "none")).lower()
    gpus = int(hardware.get("gpus_per_node", 0))
    nodes = int(hardware.get("nodes", 1))
    custom = bool(software.get("custom_engine_integration"))
    model_family = str(software.get("model_family", "")).lower()

    if vendor != "nvidia":
        return "not-applicable", "CUDA-X requires an NVIDIA CUDA target; keep a vendor-neutral fallback."
    if name == "cuequivariance":
        if stage == "ml-surrogate" and model_family in {"equivariant", "mace", "nequip", "e3nn"}:
            return "recommended", "Use for equivariant atomistic ML; it does not accelerate a Kohn-Sham engine directly."
        return "not-applicable", "Reserve for equivariant ML potentials, not ordinary DFT parsing or SCF execution."
    if name == "cutensor":
        if stage == "ml-surrogate" or custom:
            return "benchmark", "Benchmark measured tensor contractions; preserve an FP64 reference path."
        return "not-drop-in", "Packaged VASP, QE and CP2K binaries cannot gain cuTENSOR by manifest injection."
    if name in {"cusolvermp", "cufftmp", "nvshmem", "cutlass", "cusparse"}:
        if custom:
            return "benchmark", "Requires explicit source-level integration and end-to-end profiling."
        return "not-drop-in", "This library needs engine or native-extension integration, not a Python workflow flag."
    if name == "nccl":
        if engine == "vasp" and gpus > 1:
            return "recommended-build", "Use a supported NCCL-enabled VASP GPU build and one MPI rank per GPU."
        if gpus > 1 or nodes > 1:
            return "benchmark", "Use only when the engine build and MPI stack support GPU collectives."
        return "optional", "Single-GPU work does not need distributed collectives."
    if name in {"cublas", "cusolver", "cufft"}:
        if stage == "engine" and bool(software.get("engine_gpu_build")):
            return "engine-build", "Consume through the supported GPU build; do not preload into an arbitrary binary."
        if custom:
            return "recommended", "Use from compiled kernels or an audited GPU array backend."
        return "external-engine-owned", "The external engine or ML backend owns this dependency."
    return "benchmark", "Measure the exact workload before adoption."


def engine_actions(profile: dict[str, Any]) -> list[str]:
    engine = str(profile["engine"]).lower()
    hardware = profile.get("hardware") or {}
    software = profile.get("software") or {}
    gpus = int(hardware.get("gpus_per_node", 0))
    actions: list[str] = []
    if engine == "vasp" and gpus:
        actions.extend(
            [
                "Use the supported OpenACC GPU port; do not select the deprecated CUDA-C port.",
                "Start with one MPI rank per GPU and NCORE=1; benchmark KPAR, NSIM and OpenMP threads.",
                "Prefer a supported NCCL-enabled build and CUDA-aware MPI when available.",
            ]
        )
    elif engine == "quantum-espresso" and gpus:
        actions.extend(
            [
                "Use a versioned GPU-enabled Quantum ESPRESSO build and run its upstream tests.",
                "Benchmark pools, task groups, diagonalization, MPI ranks and OpenMP threads on the real input.",
                "Treat one MPI rank per GPU as a starting candidate, not a universal rule.",
            ]
        )
    elif engine == "cp2k" and gpus:
        actions.extend(
            [
                "Build with CP2K_USE_ACCEL=CUDA and the exact target GPU architecture.",
                "Benchmark DBCSR, GRID, DBM and PW GPU backends plus ELPA, SPLA and COSMA choices.",
                "Measure MPI/OpenMP balance, GPU memory high-water mark and restart compatibility.",
            ]
        )
    elif engine == "gaussian" and gpus:
        actions.append("Use only vendor-supported Gaussian GPU features; never inject CUDA-X into a licensed binary.")
    elif engine == "generic" and gpus:
        actions.append("Integrate CUDA libraries in compiled code behind a stable, tested interface and CPU fallback.")
    else:
        actions.append("Profile CPU MPI/OpenMP/BLAS layout before adding accelerators.")
    if bool(software.get("engine_gpu_build")):
        actions.append("Record compiler, CUDA toolkit, MPI, math libraries, driver and engine build fingerprint.")
    return actions


def build_plan(profile: dict[str, Any]) -> dict[str, Any]:
    errors, warnings = validate(profile)
    if errors:
        return {"ok": False, "errors": errors, "warnings": warnings}

    hardware = profile.get("hardware") or {}
    software = profile.get("software") or {}
    gpus = int(hardware.get("gpus_per_node", 0))
    nodes = int(hardware.get("nodes", 1))
    cpus_per_gpu = int(hardware.get("cpus_per_gpu", 8))
    selected = {normalize_library(str(item)) for item in software.get("libraries", [])}
    if str(profile["stage"]).lower() == "engine" and gpus:
        selected.update({"cublas", "cusolver", "cufft", "nccl"})
    if str(profile["stage"]).lower() == "ml-surrogate":
        selected.update({"cuequivariance", "cutensor"})

    library_report = []
    for name in sorted(selected):
        decision, reason = library_decision(name, profile)
        library_report.append(
            {
                "name": name,
                "category": LIBRARIES[name]["category"],
                "decision": decision,
                "purpose": LIBRARIES[name]["purpose"],
                "reason": reason,
            }
        )

    ranks_per_node = gpus if gpus and str(profile["stage"]).lower() == "engine" else int(
        hardware.get("tasks_per_node", 1)
    )
    benchmarks = [
        "CPU reference with identical scientific inputs and convergence thresholds",
        "single-GPU strong-scaling point" if gpus else "single-node CPU MPI/OpenMP sweep",
    ]
    if gpus > 1:
        benchmarks.append("multi-GPU rank binding and communication sweep")
    if nodes > 1:
        benchmarks.append("multi-node scaling with filesystem and interconnect counters")
    if str(hardware.get("target", "")).lower() == "edge":
        benchmarks.append("edge inference/preprocessing latency, power and memory measurement")

    return {
        "ok": True,
        "recommended_path": recommended_path(profile),
        "resource_baseline": {
            "nodes": nodes,
            "gpus_per_node": gpus,
            "mpi_ranks_per_node": ranks_per_node,
            "cpus_per_rank": cpus_per_gpu if gpus else int(hardware.get("cpus_per_task", 1)),
            "mapping": "one-rank-per-gpu baseline" if gpus else "benchmark MPI/OpenMP decomposition",
        },
        "engine_actions": engine_actions(profile),
        "library_assessment": library_report,
        "python_strategy": [
            "Keep Python for manifests, validation, provenance, scheduling and orchestration.",
            "Use vectorized NumPy first; use CuPy, JAX or a framework backend only for measured array hotspots.",
            "Avoid Python process pools around MPI, OpenMP, BLAS or GPU-parallel engines unless nesting is proven safe.",
        ],
        "native_strategy": [
            "Use C++, Fortran, CUDA, OpenACC, OpenMP offload, Kokkos or SYCL only for measured kernels.",
            "Expose native code through a narrow C ABI, pybind11/nanobind binding, or file/JSON subprocess contract.",
            "Ship x86_64 and aarch64 builds with a deterministic CPU fallback; never make GPU availability mandatory.",
        ],
        "benchmark_matrix": benchmarks,
        "metrics": [
            "wall time",
            "time to solution",
            "energy and force agreement",
            "SCF iterations",
            "GPU and CPU utilization",
            "peak host and device memory",
            "I/O volume",
            "energy consumption when available",
        ],
        "warnings": warnings,
        "non_claims": [
            "A generated plan is L1 planning evidence, not measured speedup.",
            "GPU execution does not relax convergence, precision, provenance or scientific acceptance rules.",
            "Only immutable real-engine benchmarks can promote a scoped acceleration result to L3 evidence.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    loaded = yaml.safe_load(args.profile.read_text(encoding="utf-8")) or {}
    if not isinstance(loaded, dict):
        report = {"ok": False, "errors": ["profile root must be a mapping"], "warnings": []}
    else:
        report = build_plan(loaded)
    rendered = json.dumps(report, indent=2, ensure_ascii=False)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

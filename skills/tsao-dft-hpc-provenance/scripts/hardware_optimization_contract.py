#!/usr/bin/env python3
"""Validation and catalog contracts for hardware-aware optimization planning."""

from __future__ import annotations

import math
import re
from typing import Any

SCHEMA_VERSION = "1.0"
NOT_AVAILABLE = "NOT_AVAILABLE"
SIMULATION_LABELS = {
    "SIMULATION_ONLY",
    "NOT_REAL_HARDWARE",
    "NOT_PERFORMANCE_EVIDENCE",
}
ENGINES = {"gaussian", "vasp", "quantum-espresso", "cp2k", "generic"}
STAGES = {"engine", "ml-surrogate", "postprocessing", "workflow"}
TARGETS = {"edge", "workstation", "hpc"}
GPU_VENDORS = {"none", "nvidia", "amd", "intel", "apple"}
BACKENDS = {"cpu", "cuda", "openacc", "hip", "sycl", "openmp-offload", "metal"}
PROVIDERS = {"auto", "cpu", "engine-native", "array-api", "custom-native", "edge-runtime", "remote-dft"}
BOTTLENECKS = {"auto", "fft", "dense-solve", "sparse", "tensor", "communication", "io", "transfer", "unknown"}
PRECISIONS = {"fp64", "mixed-validated", "mixed-experimental"}
EDGE_RUNTIMES = {"auto", "onnxruntime", "tensorrt", "openvino", "framework"}
BACKEND_VENDORS = {
    "cpu": GPU_VENDORS,
    "cuda": {"nvidia"},
    "openacc": {"nvidia"},
    "hip": {"amd", "nvidia"},
    "sycl": {"intel", "amd", "nvidia"},
    "openmp-offload": {"amd", "intel", "nvidia"},
    "metal": {"apple"},
}


def _library(vendor: str, category: str, purpose: str) -> dict[str, str]:
    return {"vendor": vendor, "category": category, "purpose": purpose}


LIBRARIES: dict[str, dict[str, str]] = {
    "cublas": _library("nvidia", "dense-solve", "Dense BLAS through an accepted build or explicit CUDA integration."),
    "cusolver": _library(
        "nvidia",
        "dense-solve",
        "Factorization and eigensolver support through an accepted integration.",
    ),
    "cufft": _library("nvidia", "fft", "FFT primitives for supported engine builds or explicit custom kernels."),
    "cusparse": _library("nvidia", "sparse", "Sparse primitives for an explicit profiled sparse path."),
    "cutensor": _library("nvidia", "tensor", "High-order contractions, reductions and permutations."),
    "cuequivariance": _library(
        "nvidia",
        "tensor",
        "Equivariant atomistic-ML operations for accepted model families.",
    ),
    "nccl": _library("nvidia", "communication", "Multi-GPU collectives with topology evidence."),
    "tensorrt": _library("nvidia", "edge-runtime", "Validated NVIDIA edge inference."),
    "rocblas": _library("amd", "dense-solve", "Dense BLAS through an accepted HIP build or explicit integration."),
    "rocsolver": _library(
        "amd",
        "dense-solve",
        "Factorization and eigensolver support through an accepted HIP path.",
    ),
    "rocfft": _library("amd", "fft", "FFT primitives for supported HIP builds or explicit kernels."),
    "rocsparse": _library("amd", "sparse", "Sparse primitives for an explicit profiled sparse path."),
    "hiptensor": _library("amd", "tensor", "Tensor contractions for an explicit HIP workload."),
    "rccl": _library("amd", "communication", "Multi-GPU collectives with topology evidence."),
    "onemkl": _library("intel", "math", "BLAS, LAPACK, FFT or sparse kernels for explicit oneAPI paths."),
    "oneccl": _library("intel", "communication", "Distributed collectives with topology evidence."),
    "openvino": _library("intel", "edge-runtime", "Validated Intel edge inference."),
    "mps": _library("apple", "tensor", "Supported Metal array and ML operations."),
    "accelerate": _library("apple", "math", "Apple host BLAS, LAPACK and FFT services."),
    "arrayapi": _library("portable", "interface", "Backend-neutral Python array interface."),
    "dlpack": _library("portable", "interface", "Audited tensor interchange and copy avoidance."),
    "kokkos": _library("portable", "native", "Performance-portable C++ kernels after profiling."),
    "onnxruntime": _library("portable", "edge-runtime", "Portable validated surrogate inference baseline."),
}
ALIASES = {re.sub(r"[^a-z0-9]", "", name.lower()): name for name in LIBRARIES}
ALIASES.update(
    {
        "pythonarrayapi": "arrayapi",
        "onnxruntimegpu": "onnxruntime",
        "onemathkernellibrary": "onemkl",
        "metalperformanceshaders": "mps",
    }
)


def normalize_library(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]", "", value.lower())
    return ALIASES.get(normalized, normalized)


def _mapping(value: Any, name: str, errors: list[str]) -> dict[str, Any]:
    if type(value) is not dict:
        errors.append(f"{name} must be a mapping")
        return {}
    return value


def _string(value: Any, name: str, errors: list[str], *, allow_not_available: bool = False) -> str:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{name} must be a non-empty string")
        return ""
    rendered = value.strip()
    if rendered == NOT_AVAILABLE and not allow_not_available:
        errors.append(f"{name} cannot be {NOT_AVAILABLE}")
    return rendered


def _strict_int(value: Any, name: str, errors: list[str], minimum: int = 0) -> int:
    if type(value) is not int:
        errors.append(f"{name} must be an integer")
        return minimum
    if value < minimum:
        errors.append(f"{name} must be >= {minimum}")
    return value


def _optional_number(value: Any, name: str, errors: list[str], *, minimum: float = 0.0) -> float | None:
    if value == NOT_AVAILABLE:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        errors.append(f"{name} must be numeric or {NOT_AVAILABLE}")
        return None
    rendered = float(value)
    if not math.isfinite(rendered) or rendered <= minimum:
        errors.append(f"{name} must be finite and > {minimum}, or {NOT_AVAILABLE}")
        return None
    return rendered


def _optional_int(value: Any, name: str, errors: list[str], *, minimum: int = 1) -> int | None:
    if value == NOT_AVAILABLE:
        return None
    if type(value) is not int:
        errors.append(f"{name} must be an integer or {NOT_AVAILABLE}")
        return None
    if value < minimum:
        errors.append(f"{name} must be >= {minimum}, or {NOT_AVAILABLE}")
        return None
    return value


def _string_list(value: Any, name: str, errors: list[str]) -> list[str]:
    if not isinstance(value, list):
        errors.append(f"{name} must be a list")
        return []
    output: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            errors.append(f"{name}[{index}] must be a non-empty string")
        else:
            output.append(item.strip())
    return output


def _bool(value: Any, name: str, errors: list[str]) -> bool:
    if type(value) is not bool:
        errors.append(f"{name} must be boolean")
        return False
    return value


def validate_profile(profile: dict[str, Any]) -> tuple[list[str], list[str], dict[str, Any]]:
    errors: list[str] = []
    warnings: list[str] = []
    evidence = _mapping(profile.get("evidence", {}), "evidence", errors)
    hardware = _mapping(profile.get("hardware", {}), "hardware", errors)
    software = _mapping(profile.get("software", {}), "software", errors)
    engine_build = _mapping(software.get("engine_build", {}), "software.engine_build", errors)
    workload = _mapping(profile.get("workload", {}), "workload", errors)
    policy = _mapping(profile.get("policy", {}), "policy", errors)

    profile_id = _string(profile.get("profile_id"), "profile_id", errors)
    engine = str(profile.get("engine", "")).lower()
    stage = str(profile.get("stage", "")).lower()
    target = str(hardware.get("target", "")).lower()
    vendor = str(hardware.get("gpu_vendor", "none")).lower()
    backend = str(software.get("backend", "cpu")).lower()
    provider = str(software.get("provider", "auto")).lower()
    precision = str(policy.get("precision", "fp64")).lower()
    expected_kernel = str(workload.get("expected_kernel", "auto")).lower()
    edge_runtime = str(software.get("edge_runtime", "auto")).lower()

    if str(profile.get("schema_version", "")) != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    if engine not in ENGINES:
        errors.append(f"engine must be one of {sorted(ENGINES)}")
    if stage not in STAGES:
        errors.append(f"stage must be one of {sorted(STAGES)}")
    if target not in TARGETS:
        errors.append(f"hardware.target must be one of {sorted(TARGETS)}")
    if vendor not in GPU_VENDORS:
        errors.append(f"hardware.gpu_vendor must be one of {sorted(GPU_VENDORS)}")
    if backend not in BACKENDS:
        errors.append(f"software.backend must be one of {sorted(BACKENDS)}")
    elif vendor in GPU_VENDORS and vendor not in BACKEND_VENDORS[backend]:
        errors.append(f"software.backend={backend} is incompatible with hardware.gpu_vendor={vendor}")
    if provider not in PROVIDERS:
        errors.append(f"software.provider must be one of {sorted(PROVIDERS)}")
    if precision not in PRECISIONS:
        errors.append(f"policy.precision must be one of {sorted(PRECISIONS)}")
    if expected_kernel not in BOTTLENECKS:
        errors.append(f"workload.expected_kernel must be one of {sorted(BOTTLENECKS)}")
    if edge_runtime not in EDGE_RUNTIMES:
        errors.append(f"software.edge_runtime must be one of {sorted(EDGE_RUNTIMES)}")

    source_kind = str(evidence.get("source_kind", "simulation")).lower()
    labels = set(_string_list(evidence.get("labels", []), "evidence.labels", errors))
    if source_kind not in {"simulation", "observed"}:
        errors.append("evidence.source_kind must be simulation or observed")
    if source_kind == "simulation" and not SIMULATION_LABELS.issubset(labels):
        missing = sorted(SIMULATION_LABELS - labels)
        errors.append(f"simulation evidence is missing required labels: {missing}")

    nodes = _strict_int(hardware.get("nodes", 1), "hardware.nodes", errors, 1)
    gpus = _strict_int(hardware.get("gpus_per_node", 0), "hardware.gpus_per_node", errors, 0)
    physical_cores = _optional_int(hardware.get("physical_cores", NOT_AVAILABLE), "hardware.physical_cores", errors)
    logical_threads = _optional_int(hardware.get("logical_threads", NOT_AVAILABLE), "hardware.logical_threads", errors)
    numa_nodes = _optional_int(hardware.get("numa_nodes", NOT_AVAILABLE), "hardware.numa_nodes", errors)
    memory_gb = _optional_number(hardware.get("memory_gb", NOT_AVAILABLE), "hardware.memory_gb", errors)
    gpu_memory_gb = _optional_number(hardware.get("gpu_memory_gb", NOT_AVAILABLE), "hardware.gpu_memory_gb", errors)
    bandwidth = _optional_number(
        hardware.get("memory_bandwidth_gb_s", NOT_AVAILABLE),
        "hardware.memory_bandwidth_gb_s",
        errors,
    )
    tasks_per_node = _optional_int(hardware.get("tasks_per_node", NOT_AVAILABLE), "hardware.tasks_per_node", errors)
    cpus_per_gpu = _optional_int(hardware.get("cpus_per_gpu", NOT_AVAILABLE), "hardware.cpus_per_gpu", errors)

    if vendor == "none" and gpus:
        errors.append("hardware.gpus_per_node requires a non-none gpu_vendor")
    if backend != "cpu" and gpus == 0:
        errors.append("an accelerator backend requires at least one GPU")
    if logical_threads is not None and physical_cores is not None and logical_threads < physical_cores:
        errors.append("hardware.logical_threads must be >= hardware.physical_cores")
    if numa_nodes is not None and physical_cores is not None and numa_nodes > physical_cores:
        errors.append("hardware.numa_nodes cannot exceed hardware.physical_cores")
    if tasks_per_node is not None and physical_cores is not None and tasks_per_node > physical_cores:
        warnings.append("hardware.tasks_per_node exceeds physical cores; oversubscription requires site evidence")
    if gpus and gpu_memory_gb is None:
        warnings.append("GPU memory is NOT_AVAILABLE; device-memory risk cannot be closed")
    if bandwidth is None:
        warnings.append("memory bandwidth is NOT_AVAILABLE; transfer and roofline assumptions remain open")
    if memory_gb is None:
        warnings.append("host memory is NOT_AVAILABLE; host-memory risk cannot be closed")

    accelerator_supported = _bool(
        engine_build.get("accelerator_supported", False),
        "software.engine_build.accelerator_supported",
        errors,
    )
    build_fingerprint = _string(
        engine_build.get("build_fingerprint_id", NOT_AVAILABLE),
        "software.engine_build.build_fingerprint_id",
        errors,
        allow_not_available=True,
    )
    custom_integration = _bool(software.get("custom_integration", False), "software.custom_integration", errors)
    libraries = _string_list(software.get("libraries", []), "software.libraries", errors)
    available_libraries = _string_list(
        software.get("available_libraries", []),
        "software.available_libraries",
        errors,
    )
    normalized_libraries = [normalize_library(item) for item in libraries]
    normalized_available = [normalize_library(item) for item in available_libraries]
    unknown = sorted((set(normalized_libraries) | set(normalized_available)) - set(LIBRARIES))
    if unknown:
        errors.append(f"unknown acceleration libraries: {unknown}")

    model_family = str(software.get("model_family", "none")).lower()
    if "cuequivariance" in normalized_libraries and model_family not in {"equivariant", "mace", "nequip", "e3nn"}:
        errors.append("cuEquivariance requires an accepted equivariant, MACE, NequIP or e3nn model family")
    if "tensorrt" in normalized_libraries and not (target == "edge" and stage == "ml-surrogate" and vendor == "nvidia"):
        errors.append("TensorRT is limited to NVIDIA edge ml-surrogate plans")
    if "openvino" in normalized_libraries and not (target == "edge" and stage == "ml-surrogate" and vendor == "intel"):
        errors.append("OpenVINO is limited to Intel edge ml-surrogate plans")

    if stage == "engine" and target != "edge" and backend != "cpu":
        if not accelerator_supported:
            errors.append("accelerated engine plans require software.engine_build.accelerator_supported=true")
        if build_fingerprint == NOT_AVAILABLE:
            errors.append("accelerated engine plans require an immutable build_fingerprint_id")
    if provider == "engine-native" and (not accelerator_supported or build_fingerprint == NOT_AVAILABLE):
        errors.append("engine-native provider requires accepted accelerator support and build fingerprint")
    if provider == "custom-native" and not custom_integration:
        errors.append("custom-native provider requires software.custom_integration=true")

    require_cpu_reference = _bool(
        policy.get("require_cpu_fp64_reference", True),
        "policy.require_cpu_fp64_reference",
        errors,
    )
    require_cpu_fallback = _bool(policy.get("require_cpu_fallback", True), "policy.require_cpu_fallback", errors)
    uncertainty_gate = _bool(policy.get("edge_uncertainty_gate", True), "policy.edge_uncertainty_gate", errors)
    remote_fallback = _bool(policy.get("remote_dft_fallback", True), "policy.remote_dft_fallback", errors)
    if not require_cpu_reference:
        errors.append("policy.require_cpu_fp64_reference must remain true")
    if backend != "cpu" and not require_cpu_fallback:
        errors.append("accelerator plans require policy.require_cpu_fallback=true")
    if target == "edge" and stage == "ml-surrogate" and (not uncertainty_gate or not remote_fallback):
        errors.append("edge ml-surrogate plans require uncertainty gating and remote DFT fallback")
    if target == "edge" and stage == "engine" and provider not in {"auto", "remote-dft"}:
        errors.append("edge engine plans must use the remote-dft provider")

    claims = profile.get("claims", [])
    if claims not in (None, [], {}):
        errors.append("optimization input must not contain speedup or capability claims")
    if policy.get("requested_speedup_claim") not in (None, False, ""):
        errors.append("requested_speedup_claim is forbidden before real qualification")

    for name in normalized_libraries:
        if name not in LIBRARIES:
            continue
        library_vendor = LIBRARIES[name]["vendor"]
        if library_vendor not in {"portable", vendor}:
            errors.append(f"{name} targets {library_vendor}, not hardware.gpu_vendor={vendor}")

    normalized = {
        "profile_id": profile_id,
        "engine": engine,
        "stage": stage,
        "target": target,
        "vendor": vendor,
        "backend": backend,
        "provider": provider,
        "precision": precision,
        "expected_kernel": expected_kernel,
        "edge_runtime": edge_runtime,
        "source_kind": source_kind,
        "labels": sorted(labels),
        "nodes": nodes,
        "gpus": gpus,
        "physical_cores": physical_cores,
        "logical_threads": logical_threads,
        "numa_nodes": numa_nodes,
        "memory_gb": memory_gb,
        "gpu_memory_gb": gpu_memory_gb,
        "bandwidth": bandwidth,
        "tasks_per_node": tasks_per_node,
        "cpus_per_gpu": cpus_per_gpu,
        "accelerator_supported": accelerator_supported,
        "build_fingerprint": build_fingerprint,
        "custom_integration": custom_integration,
        "libraries": normalized_libraries,
        "available_libraries": normalized_available,
        "model_family": model_family,
        "workload": workload,
        "policy": policy,
    }
    return errors, warnings, normalized

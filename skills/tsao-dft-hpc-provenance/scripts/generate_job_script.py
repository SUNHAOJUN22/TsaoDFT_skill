#!/usr/bin/env python3
"""Generate reviewed local/Slurm/PBS job scripts for DFT engines."""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path
from typing import Any

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from validate_hpc_manifest import (  # noqa: E402 -- local validator import follows SCRIPT_DIR path setup
    validate as validate_manifest,
)


def q(value: Any) -> str:
    return shlex.quote(str(value))


def approval_guard(manifest: dict[str, Any]) -> list[str]:
    approval = str(manifest.get("approval", "pending"))
    if approval in {"approved", "not_required"}:
        return []
    return [
        f'echo "TsaoDFT execution blocked: manifest approval is {approval}" >&2',
        "exit 64",
    ]


def launcher_prefix(manifest: dict[str, Any]) -> str:
    launcher = str(manifest.get("launcher", "")).strip()
    if launcher and launcher != "auto":
        return f"{launcher} "
    if launcher != "auto":
        return ""

    resources = manifest["resources"]
    scheduler = manifest["scheduler"]
    if scheduler != "slurm":
        raise ValueError("launcher=auto is currently supported only for Slurm")

    nodes = int(resources["nodes"])
    tasks_per_node = int(resources["tasks_per_node"])
    options = [
        "srun",
        f"--ntasks={nodes * tasks_per_node}",
        f"--ntasks-per-node={tasks_per_node}",
        f"--cpus-per-task={int(resources['cpus_per_task'])}",
        "--kill-on-bad-exit=1",
    ]
    acceleration = manifest.get("acceleration") or {}
    if acceleration.get("enabled", False):
        ranks_per_gpu = int(acceleration.get("ranks_per_gpu", 1))
        if ranks_per_gpu == 1:
            options.append("--gpus-per-task=1")
        cpu_bind = str(acceleration.get("cpu_bind", "none"))
        gpu_bind = str(acceleration.get("gpu_bind", "none"))
        if cpu_bind != "none":
            options.append(f"--cpu-bind={cpu_bind}")
        if gpu_bind != "none":
            options.append(f"--gpu-bind={gpu_bind}")
    return " ".join(options) + " "


def engine_command(manifest: dict[str, Any]) -> str:
    engine = manifest["engine"]
    executable = q(manifest["executable"])
    input_path = q(manifest["input"])
    stdout = q(manifest.get("stdout") or (Path(str(manifest["input"])).stem + ".stdout"))
    stderr = q(manifest.get("stderr") or (Path(str(manifest["input"])).stem + ".stderr"))
    prefix = launcher_prefix(manifest)
    if engine == "gaussian":
        return f"{prefix}{executable} < {input_path} > {stdout} 2> {stderr}"
    if engine == "vasp":
        return f"{prefix}{executable} > {stdout} 2> {stderr}"
    if engine == "quantum-espresso":
        return f"{prefix}{executable} -in {input_path} > {stdout} 2> {stderr}"
    if engine == "cp2k":
        return f"{prefix}{executable} -i {input_path} -o {stdout} 2> {stderr}"
    return f"{prefix}{executable} {input_path} > {stdout} 2> {stderr}"


def acceleration_environment(manifest: dict[str, Any], existing: dict[str, Any]) -> list[str]:
    acceleration = manifest.get("acceleration") or {}
    if not acceleration.get("enabled", False):
        return []
    lines: list[str] = []
    if (
        acceleration.get("gpu_vendor") == "nvidia"
        and acceleration.get("device_order") == "pci_bus_id"
        and "CUDA_DEVICE_ORDER" not in existing
    ):
        lines.append("export CUDA_DEVICE_ORDER=PCI_BUS_ID")
    return lines


def runtime_provenance(manifest: dict[str, Any]) -> list[str]:
    acceleration = manifest.get("acceleration") or {}
    if not acceleration.get("enabled", False) or not acceleration.get("record_runtime", True):
        return []

    record = q(acceleration.get("runtime_record", "tsao-acceleration-runtime.txt"))
    lines = [
        f'printf "profile_id=%s\\n" {q(acceleration.get("profile_id", "unknown"))} > {record}',
        f'printf "build_fingerprint_id=%s\\n" {q(acceleration.get("build_fingerprint_id", "unknown"))} >> {record}',
        f'printf "benchmark_plan_id=%s\\n" {q(acceleration.get("benchmark_plan_id", "unknown"))} >> {record}',
        f'printf "backend=%s\\n" {q(acceleration.get("backend", "none"))} >> {record}',
        f'printf "precision=%s\\n" {q(acceleration.get("precision", "fp64"))} >> {record}',
        f'printf "SLURM_JOB_ID=%s\\n" "${{SLURM_JOB_ID:-}}" >> {record}',
        f'printf "SLURM_NODEID=%s\\n" "${{SLURM_NODEID:-}}" >> {record}',
        f'printf "SLURM_LOCALID=%s\\n" "${{SLURM_LOCALID:-}}" >> {record}',
        f'printf "CUDA_VISIBLE_DEVICES=%s\\n" "${{CUDA_VISIBLE_DEVICES:-}}" >> {record}',
        f'printf "ROCR_VISIBLE_DEVICES=%s\\n" "${{ROCR_VISIBLE_DEVICES:-}}" >> {record}',
        f'printf "ZE_AFFINITY_MASK=%s\\n" "${{ZE_AFFINITY_MASK:-}}" >> {record}',
    ]
    vendor = str(acceleration.get("gpu_vendor", "none"))
    if vendor == "nvidia":
        inventory = q(acceleration.get("device_inventory", "tsao-nvidia-gpu-inventory.csv"))
        lines.extend(
            [
                "if command -v nvidia-smi >/dev/null 2>&1; then",
                "  nvidia-smi --query-gpu=name,uuid,pci.bus_id,driver_version,memory.total "
                f"--format=csv,noheader > {inventory}",
                "else",
                f'  echo "nvidia-smi unavailable" > {inventory}',
                "fi",
            ]
        )
    return lines


def build(manifest: dict[str, Any]) -> str:
    resources = manifest["resources"]
    scheduler = manifest["scheduler"]
    lines = ["#!/usr/bin/env bash", "set -euo pipefail"]
    headers: list[str] = []
    if scheduler == "slurm":
        headers = [
            f"#SBATCH --job-name={manifest['job_id']}",
            f"#SBATCH --nodes={resources['nodes']}",
            f"#SBATCH --ntasks-per-node={resources['tasks_per_node']}",
            f"#SBATCH --cpus-per-task={resources['cpus_per_task']}",
            f"#SBATCH --mem={resources['memory_gb']}G",
            f"#SBATCH --time={resources['walltime']}",
        ]
        if resources.get("partition"):
            headers.append(f"#SBATCH --partition={resources['partition']}")
        gpus_per_node = int(resources.get("gpus_per_node", resources.get("gpus", 0)))
        if gpus_per_node > 0:
            headers.append(f"#SBATCH --gpus-per-node={gpus_per_node}")
    elif scheduler == "pbs":
        select = (
            f"select={resources['nodes']}:"
            f"ncpus={int(resources['tasks_per_node']) * int(resources['cpus_per_task'])}:"
            f"mem={resources['memory_gb']}gb"
        )
        gpus_per_node = int(resources.get("gpus_per_node", resources.get("gpus", 0)))
        if gpus_per_node > 0:
            select += f":ngpus={gpus_per_node}"
        headers = [
            f"#PBS -N {manifest['job_id']}",
            f"#PBS -l {select}",
            f"#PBS -l walltime={resources['walltime']}",
        ]
        if resources.get("queue"):
            headers.append(f"#PBS -q {resources['queue']}")
    lines[1:1] = headers

    acceleration = manifest.get("acceleration") or {}
    lines += [
        "",
        f"# engine: {manifest['engine']} {manifest.get('engine_version', 'unknown')}",
        f"# method_fingerprint_id: {manifest.get('method_fingerprint_id', 'unknown')}",
        f"# support_level: {manifest.get('support_level', 'unknown')}",
        f"# approval: {manifest.get('approval', 'pending')}",
    ]
    if acceleration.get("enabled", False):
        lines.extend(
            [
                f"# acceleration_profile_id: {acceleration.get('profile_id', 'unknown')}",
                f"# acceleration_backend: {acceleration.get('backend', 'none')}",
                f"# acceleration_mode: {acceleration.get('mode', 'none')}",
                f"# acceleration_precision: {acceleration.get('precision', 'fp64')}",
                f"# build_fingerprint_id: {acceleration.get('build_fingerprint_id', 'unknown')}",
                f"# benchmark_plan_id: {acceleration.get('benchmark_plan_id', 'unknown')}",
            ]
        )

    environment = manifest.get("environment") or {}
    for module in environment.get("modules", []):
        lines.append(f"module load {q(module)}")
    for source in environment.get("source", []):
        lines.append(f"source {q(source)}")
    variables = environment.get("variables") or {}
    for key, value in variables.items():
        lines.append(f"export {key}={q(value)}")
    lines.extend(acceleration_environment(manifest, variables))

    scratch = manifest.get("scratch") or {}
    if scratch.get("path"):
        lines.append(f"mkdir -p {q(scratch['path'])}")
        if manifest["engine"] == "gaussian":
            lines.append(f"export GAUSS_SCRDIR={q(scratch['path'])}")

    lines += ["", f"cd {q(manifest['workdir'])}"]
    lines.extend(approval_guard(manifest))
    lines += ['echo "TsaoDFT job start: $(date -Is)"', 'echo "Host: $(hostname)"']
    lines.extend(runtime_provenance(manifest))
    lines.append(f"# preflight: {(manifest.get('preflight') or {}).get('command', 'not recorded')}")
    if (manifest.get("preflight") or {}).get("run_in_job", False):
        lines.append(str(manifest["preflight"]["command"]))
    lines.append(engine_command(manifest))
    lines += ["rc=$?", 'echo "TsaoDFT job end: $(date -Is) rc=${rc}"']
    if (manifest.get("parser") or {}).get("run_in_job", False):
        lines.append(str(manifest["parser"]["command"]))
    lines.append("exit ${rc}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    loaded = yaml.safe_load(args.manifest.read_text(encoding="utf-8")) or {}
    if not isinstance(loaded, dict):
        print(json.dumps({"ok": False, "errors": ["manifest root must be a mapping"], "warnings": []}, indent=2))
        return 1
    errors, warnings = validate_manifest(loaded)
    if errors:
        print(json.dumps({"ok": False, "errors": errors, "warnings": warnings}, indent=2))
        return 1
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(build(loaded), encoding="utf-8")
    args.out.chmod(0o755)
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

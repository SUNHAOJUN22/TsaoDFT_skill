#!/usr/bin/env python3
"""Generate injection-resistant local/Slurm/PBS job scripts from structured argv."""

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

from shell_contract import render_argv  # noqa: E402 -- standalone Skill import contract
from validate_hpc_manifest import validate as validate_manifest  # noqa: E402 -- standalone Skill import contract


def q(value: Any) -> str:
    return shlex.quote(str(value))


def approval_guard(manifest: dict[str, Any]) -> list[str]:
    approval = str(manifest.get("approval", "pending"))
    if approval in {"approved", "not_required"}:
        return []
    return [f'echo "TsaoDFT execution blocked: manifest approval is {approval}" >&2', "exit 64"]


def launcher_prefix(manifest: dict[str, Any]) -> str:
    launcher = manifest.get("launcher")
    if isinstance(launcher, dict):
        return render_argv(launcher["argv"]) + " "
    if launcher != "auto":
        return ""
    resources = manifest["resources"]
    if manifest["scheduler"] != "slurm":
        raise ValueError("launcher=auto is supported only for Slurm")
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
    if acceleration.get("enabled") is True:
        if int(acceleration.get("ranks_per_gpu", 1)) == 1:
            options.append("--gpus-per-task=1")
        for flag, key in (("--cpu-bind", "cpu_bind"), ("--gpu-bind", "gpu_bind")):
            value = str(acceleration.get(key, "none"))
            if value != "none":
                options.append(f"{flag}={value}")
    return " ".join(q(item) for item in options) + " "


def engine_argv(manifest: dict[str, Any]) -> list[str]:
    engine = manifest["engine"]
    executable = str(manifest["executable"])
    input_path = str(manifest["input"])
    if engine == "gaussian":
        return [executable]
    if engine == "vasp":
        return [executable]
    if engine == "quantum-espresso":
        return [executable, "-in", input_path]
    if engine == "cp2k":
        return [executable, "-i", input_path, "-o", str(manifest.get("stdout") or "cp2k.out")]
    return [executable, input_path]


def engine_command(manifest: dict[str, Any]) -> str:
    engine = manifest["engine"]
    input_path = q(manifest["input"])
    stdout = q(manifest.get("stdout") or (Path(str(manifest["input"])).stem + ".stdout"))
    stderr = q(manifest.get("stderr") or (Path(str(manifest["input"])).stem + ".stderr"))
    prefix = launcher_prefix(manifest)
    command = render_argv(engine_argv(manifest))
    if engine == "gaussian":
        return f"{prefix}{command} < {input_path} > {stdout} 2> {stderr}"
    if engine == "cp2k":
        return f"{prefix}{command} 2> {stderr}"
    return f"{prefix}{command} > {stdout} 2> {stderr}"


def runtime_provenance(manifest: dict[str, Any]) -> list[str]:
    acceleration = manifest.get("acceleration") or {}
    if acceleration.get("enabled") is not True or acceleration.get("record_runtime", True) is False:
        return []
    record = q(acceleration.get("runtime_record", "tsao-acceleration-runtime.txt"))
    lines = [
        f'printf "profile_id=%s\\n" {q(acceleration.get("profile_id", "unknown"))} > {record}',
        f'printf "build_fingerprint_id=%s\\n" {q(acceleration.get("build_fingerprint_id", "unknown"))} >> {record}',
        f'printf "benchmark_plan_id=%s\\n" {q(acceleration.get("benchmark_plan_id", "unknown"))} >> {record}',
        f'printf "SLURM_JOB_ID=%s\\n" "${{SLURM_JOB_ID:-}}" >> {record}',
        f'printf "SLURM_LOCALID=%s\\n" "${{SLURM_LOCALID:-}}" >> {record}',
        f'printf "CUDA_VISIBLE_DEVICES=%s\\n" "${{CUDA_VISIBLE_DEVICES:-}}" >> {record}',
        f'printf "ROCR_VISIBLE_DEVICES=%s\\n" "${{ROCR_VISIBLE_DEVICES:-}}" >> {record}',
        f'printf "ZE_AFFINITY_MASK=%s\\n" "${{ZE_AFFINITY_MASK:-}}" >> {record}',
    ]
    if acceleration.get("gpu_vendor") == "nvidia":
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
        gpus = int(resources.get("gpus_per_node", resources.get("gpus", 0)))
        if gpus:
            headers.append(f"#SBATCH --gpus-per-node={gpus}")
    elif scheduler == "pbs":
        select = (
            f"select={resources['nodes']}:"
            f"ncpus={int(resources['tasks_per_node']) * int(resources['cpus_per_task'])}:"
            f"mem={resources['memory_gb']}gb"
        )
        gpus = int(resources.get("gpus_per_node", resources.get("gpus", 0)))
        if gpus:
            select += f":ngpus={gpus}"
        headers = [f"#PBS -N {manifest['job_id']}", f"#PBS -l {select}", f"#PBS -l walltime={resources['walltime']}"]
        if resources.get("queue"):
            headers.append(f"#PBS -q {resources['queue']}")
    lines[1:1] = headers
    lines += [
        "",
        f"# engine: {manifest['engine']} {manifest.get('engine_version', 'unknown')}",
        f"# method_fingerprint_id: {manifest.get('method_fingerprint_id', 'unknown')}",
        f"# support_level: {manifest.get('support_level', 'unknown')}",
        f"# approval: {manifest.get('approval', 'pending')}",
    ]
    environment = manifest.get("environment") or {}
    for module in environment.get("modules", []):
        lines.append(f"module load {q(module)}")
    for source in environment.get("source", []):
        lines.append(f"source {q(source)}")
    variables = environment.get("variables") or {}
    for key, value in variables.items():
        lines.append(f"export {key}={q(value)}")
    acceleration = manifest.get("acceleration") or {}
    if (
        acceleration.get("enabled")
        and acceleration.get("gpu_vendor") == "nvidia"
        and acceleration.get("device_order") == "pci_bus_id"
        and "CUDA_DEVICE_ORDER" not in variables
    ):
        lines.append("export CUDA_DEVICE_ORDER=PCI_BUS_ID")
    scratch = manifest.get("scratch") or {}
    if scratch.get("path"):
        lines.append(f"mkdir -p {q(scratch['path'])}")
        if manifest["engine"] == "gaussian":
            lines.append(f"export GAUSS_SCRDIR={q(scratch['path'])}")
    lines += ["", f"cd {q(manifest['workdir'])}"]
    lines.extend(approval_guard(manifest))
    lines.extend(['echo "TsaoDFT job start: $(date -Is)"', 'echo "Host: $(hostname)"'])
    lines.extend(runtime_provenance(manifest))
    preflight = manifest["preflight"]
    lines.append(f"# preflight: {render_argv(preflight['argv'])}")
    if preflight.get("run_in_job") is True:
        lines.append(render_argv(preflight["argv"]))
    lines.append(engine_command(manifest))
    lines += ["rc=$?", 'echo "TsaoDFT job end: $(date -Is) rc=${rc}"']
    parser_contract = manifest["parser"]
    if parser_contract.get("run_in_job") is True:
        lines.append(render_argv(parser_contract["argv"]))
    lines.append("exit ${rc}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--approval-root", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    loaded = yaml.safe_load(args.manifest.read_text(encoding="utf-8")) or {}
    if not isinstance(loaded, dict):
        print(json.dumps({"ok": False, "errors": ["manifest root must be a mapping"]}, indent=2))
        return 1
    errors, warnings = validate_manifest(loaded, approval_root=args.approval_root or args.manifest.parent)
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

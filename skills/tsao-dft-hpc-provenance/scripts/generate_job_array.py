#!/usr/bin/env python3
"""Generate one approval-gated Slurm array script and one JSONL task table."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from generate_job_script import approval_guard, engine_command, q  # noqa: E402
from validate_hpc_manifest import validate as validate_manifest  # noqa: E402


def load_campaign(path: Path) -> tuple[dict, dict, list[dict]]:
    campaign = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    errors: list[str] = []
    for key in ("schema_version", "campaign_id", "base_manifest", "tasks"):
        if key not in campaign:
            errors.append(f"missing {key}")
    base_path = path.parent / str(campaign.get("base_manifest", ""))
    if not base_path.is_file():
        errors.append(f"base_manifest not found: {base_path}")
        base: dict = {}
    else:
        base = yaml.safe_load(base_path.read_text(encoding="utf-8")) or {}
        manifest_errors, _ = validate_manifest(base)
        errors.extend(f"base manifest: {message}" for message in manifest_errors)
    if base.get("scheduler") != "slurm":
        errors.append("job arrays require a Slurm base manifest")
    if (base.get("preflight") or {}).get("run_in_job") or (base.get("parser") or {}).get("run_in_job"):
        errors.append("array base manifest requires preflight/parser run_in_job=false")
    if (base.get("scratch") or {}).get("path") and not campaign.get("scratch_root"):
        errors.append("scratch_root is required when the base manifest declares scratch.path")

    tasks = campaign.get("tasks") or []
    if not isinstance(tasks, list) or not tasks:
        errors.append("tasks must be a non-empty list")
        tasks = []
    seen: set[str] = set()
    for index, task in enumerate(tasks):
        if not isinstance(task, dict):
            errors.append(f"task {index} must be a mapping")
            continue
        for key in ("task_id", "input", "workdir"):
            if not task.get(key):
                errors.append(f"task {index} missing {key}")
        task_id = str(task.get("task_id", ""))
        if task_id in seen:
            errors.append(f"duplicate task_id: {task_id}")
        seen.add(task_id)
    try:
        maximum = int(campaign.get("max_concurrent", len(tasks) or 1))
        if maximum < 1:
            raise ValueError
    except (TypeError, ValueError):
        errors.append("max_concurrent must be a positive integer")
        maximum = 1
    campaign["max_concurrent"] = maximum
    if errors:
        raise ValueError("; ".join(errors))
    return campaign, base, tasks


def task_record(campaign: dict, base: dict, task: dict) -> dict:
    merged = dict(base)
    merged.update({key: value for key, value in task.items() if key != "task_id"})
    record = {
        "task_id": str(task["task_id"]),
        "workdir": str(merged["workdir"]),
        "command": engine_command(merged),
        "environment": {},
    }
    if (base.get("scratch") or {}).get("path"):
        scratch = Path(str(campaign["scratch_root"])) / str(task["task_id"])
        record["scratch_path"] = str(scratch)
        if base.get("engine") == "gaussian":
            record["environment"]["GAUSS_SCRDIR"] = str(scratch)
    return record


def build_array_script(campaign: dict, base: dict, task_table_name: str) -> str:
    resources = base["resources"]
    tasks = campaign["tasks"]
    maximum = min(int(campaign["max_concurrent"]), len(tasks))
    lines = [
        "#!/usr/bin/env bash",
        f"#SBATCH --job-name={campaign['campaign_id']}",
        f"#SBATCH --nodes={resources['nodes']}",
        f"#SBATCH --ntasks-per-node={resources['tasks_per_node']}",
        f"#SBATCH --cpus-per-task={resources['cpus_per_task']}",
        f"#SBATCH --mem={resources['memory_gb']}G",
        f"#SBATCH --time={resources['walltime']}",
        f"#SBATCH --array=0-{len(tasks) - 1}%{maximum}",
    ]
    if resources.get("partition"):
        lines.append(f"#SBATCH --partition={resources['partition']}")
    if int(resources.get("gpus_per_node", resources.get("gpus", 0))) > 0:
        lines.append(f"#SBATCH --gpus-per-node={int(resources.get('gpus_per_node', resources.get('gpus', 0)))}")
    lines += [
        "set -euo pipefail",
        "",
        f"# base method_fingerprint_id: {base.get('method_fingerprint_id', 'unknown')}",
        f"# approval: {base.get('approval', 'pending')}",
    ]
    environment = base.get("environment") or {}
    for module in environment.get("modules", []):
        lines.append(f"module load {q(module)}")
    for source in environment.get("source", []):
        lines.append(f"source {q(source)}")
    for key, value in (environment.get("variables") or {}).items():
        lines.append(f"export {key}={q(value)}")
    lines.extend(approval_guard(base))
    lines += [
        'SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)',
        f'TASK_TABLE="${{SCRIPT_DIR}}/{task_table_name}"',
        'TASK_INDEX="${SLURM_ARRAY_TASK_ID:?SLURM_ARRAY_TASK_ID is required}"',
        "python - \"${TASK_TABLE}\" \"${TASK_INDEX}\" <<'PY'",
        "import json",
        "import os",
        "import subprocess",
        "import sys",
        "from pathlib import Path",
        "",
        "table = Path(sys.argv[1])",
        "index = int(sys.argv[2])",
        "record = None",
        "with table.open(encoding='utf-8') as handle:",
        "    for current, line in enumerate(handle):",
        "        if current == index:",
        "            record = json.loads(line)",
        "            break",
        "if record is None:",
        "    raise SystemExit(f'array index {index} is outside {table}')",
        "print(f\"TsaoDFT array task start: {record['task_id']}\", flush=True)",
        "environment = os.environ.copy()",
        "environment.update(record.get('environment') or {})",
        "if record.get('scratch_path'):",
        "    scratch_path = Path(record['scratch_path']).resolve()",
        "    scratch_path.mkdir(parents=True, exist_ok=True)",
        "    if 'GAUSS_SCRDIR' in environment:",
        "        environment['GAUSS_SCRDIR'] = str(scratch_path)",
        "completed = subprocess.run(",
        "    record['command'],",
        "    cwd=record['workdir'],",
        "    shell=True,",
        "    executable='/bin/bash',",
        "    env=environment,",
        "    check=False,",
        ")",
        "print(f\"TsaoDFT array task end: {record['task_id']} rc={completed.returncode}\", flush=True)",
        "raise SystemExit(completed.returncode)",
        "PY",
    ]
    return "\n".join(lines) + "\n"


def generate(campaign_path: Path, script_path: Path, task_table_path: Path) -> dict:
    campaign, base, tasks = load_campaign(campaign_path)
    script_path.parent.mkdir(parents=True, exist_ok=True)
    task_table_path.parent.mkdir(parents=True, exist_ok=True)
    with task_table_path.open("w", encoding="utf-8") as handle:
        for task in tasks:
            json.dump(task_record(campaign, base, task), handle, sort_keys=True)
            handle.write("\n")
    script_path.write_text(build_array_script(campaign, base, task_table_path.name), encoding="utf-8")
    script_path.chmod(0o755)
    return {"script": str(script_path), "task_table": str(task_table_path), "task_count": len(tasks)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign", type=Path)
    parser.add_argument("--script", type=Path, required=True)
    parser.add_argument("--tasks", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = generate(args.campaign, args.script, args.tasks)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(json.dumps({"ok": False, "errors": [str(exc)]}, indent=2))
        return 1
    print(json.dumps({"ok": True, **result}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

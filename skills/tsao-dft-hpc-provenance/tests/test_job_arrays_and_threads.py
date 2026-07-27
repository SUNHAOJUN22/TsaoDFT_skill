from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str):
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(f"tsao_{name.replace('.', '_')}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class JobArrayAndThreadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validator = load_script("validate_hpc_manifest.py")
        cls.generator = load_script("generate_job_script.py")
        cls.arrays = load_script("generate_job_array.py")
        cls.base = yaml.safe_load((ROOT / "examples/slurm/hpc-manifest.yaml").read_text(encoding="utf-8"))

    def test_thread_oversubscription_is_rejected(self):
        manifest = yaml.safe_load(yaml.safe_dump(self.base))
        manifest["resources"]["cpus_per_task"] = 4
        manifest["environment"]["variables"]["OMP_NUM_THREADS"] = "8"
        errors, _ = self.validator.validate(manifest)
        self.assertIn("OMP_NUM_THREADS exceeds resources.cpus_per_task", errors)

    def test_node_cpu_capacity_is_rejected(self):
        manifest = yaml.safe_load(yaml.safe_dump(self.base))
        manifest["resources"].update({"tasks_per_node": 8, "cpus_per_task": 4, "cpus_per_node": 16})
        errors, _ = self.validator.validate(manifest)
        self.assertIn("tasks_per_node * cpus_per_task exceeds cpus_per_node", errors)

    def test_pending_script_contains_runtime_guard(self):
        script = self.generator.build(self.base)
        self.assertIn("execution blocked: manifest approval is pending", script)
        self.assertIn("exit 64", script)
        self.assertIn("g16 < demo.gjf > demo.log", script)

    def test_array_compacts_one_thousand_tasks_into_two_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            base_path = root / "base.yaml"
            campaign_path = root / "campaign.yaml"
            script_path = root / "campaign.sh"
            task_table = root / "campaign.tasks.jsonl"
            base_path.write_text(yaml.safe_dump(self.base), encoding="utf-8")
            campaign = {
                "schema_version": "1.0",
                "campaign_id": "BATCH-1000",
                "base_manifest": "base.yaml",
                "max_concurrent": 32,
                "scratch_root": "./array-scratch",
                "tasks": [
                    {
                        "task_id": f"task-{index:04d}",
                        "input": f"input-{index:04d}.gjf",
                        "workdir": f"./run-{index:04d}",
                        "stdout": f"task-{index:04d}.log",
                        "stderr": f"task-{index:04d}.stderr",
                    }
                    for index in range(1000)
                ],
            }
            campaign_path.write_text(yaml.safe_dump(campaign, sort_keys=False), encoding="utf-8")
            result = self.arrays.generate(campaign_path, script_path, task_table)
            self.assertEqual(result["task_count"], 1000)
            self.assertEqual(len(list(root.glob("*"))), 4)
            with task_table.open(encoding="utf-8") as handle:
                self.assertEqual(sum(1 for _ in handle), 1000)
            script = script_path.read_text(encoding="utf-8")
            self.assertIn("#SBATCH --array=0-999%32", script)
            self.assertIn("SLURM_ARRAY_TASK_ID", script)
            records = [json.loads(line) for line in task_table.read_text(encoding="utf-8").splitlines()]
            first = records[0]
            self.assertEqual(first["task_id"], "task-0000")
            self.assertNotEqual(records[0]["scratch_path"], records[1]["scratch_path"])
            self.assertEqual(first["environment"]["GAUSS_SCRDIR"], first["scratch_path"])

    def test_array_rejects_non_slurm_and_empty_tasks(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            base = yaml.safe_load(yaml.safe_dump(self.base))
            base["scheduler"] = "pbs"
            (root / "base.yaml").write_text(yaml.safe_dump(base), encoding="utf-8")
            campaign = {"schema_version": "1.0", "campaign_id": "BAD", "base_manifest": "base.yaml", "tasks": []}
            path = root / "campaign.yaml"
            path.write_text(yaml.safe_dump(campaign), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Slurm|non-empty"):
                self.arrays.load_campaign(path)


if __name__ == "__main__":
    unittest.main()

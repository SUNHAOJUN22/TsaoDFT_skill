from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "skills" / "tsao-dft-hpc-provenance" / "scripts" / "qualify_compute_campaign.py"
VALIDATOR_PATH = ROOT / "scripts" / "validate_compute_qualification.py"
SCHEMA_PATH = ROOT / "templates" / "benchmark-result.schema.json"


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


qualification = load_module("tsao_compute_qualification_tests", MODULE_PATH)
validator = load_module("tsao_compute_qualification_validator_tests", VALIDATOR_PATH)


def campaign() -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "campaign_id": "CAMPAIGN-1",
        "benchmark_plan_id": "PLAN-1",
        "engine": "vasp",
        "reference_candidate_id": "CPU-REF",
        "candidate_ids": ["GPU-CANDIDATE"],
        "minimum_repeats": 3,
        "minimum_reference_over_candidate_ratio": 1.1,
        "numerical_tolerances": {
            "energy_ev": {"absolute": 1.0e-6, "relative": 1.0e-8},
            "forces_ev_per_angstrom": {"absolute": 1.0e-4, "relative": 1.0e-6},
        },
    }


def result(candidate_id: str, repeat: int, wall_time: float, *, gpu: bool) -> dict[str, Any]:
    accelerator = (
        {"backend": "cuda", "toolkit_version": "12.8", "driver_version": "600.1"}
        if gpu
        else {"backend": "none", "toolkit_version": "none", "driver_version": "none"}
    )
    accelerators = (
        [
            {
                "vendor": "nvidia",
                "model": "fixture-gpu",
                "stable_id": "GPU-FIXTURE",
                "memory_bytes": 24_000_000_000,
            }
        ]
        if gpu
        else []
    )
    return {
        "schema_version": "1.0",
        "run_id": f"RUN-{candidate_id}-{repeat}",
        "benchmark_plan_id": "PLAN-1",
        "candidate_id": candidate_id,
        "engine": "vasp",
        "engine_version": "6.5.1",
        "build_fingerprint": {
            "id": f"BUILD-{candidate_id}",
            "sha256": ("b" if gpu else "a") * 64,
            "components": {"compiler": "NVHPC 25.1", "backend": accelerator["backend"]},
        },
        "compiler": "NVHPC 25.1",
        "mpi": {
            "implementation": "Open MPI",
            "version": "5.0.7",
            "ranks_per_node": 1,
            "cuda_aware": gpu,
        },
        "openmp_runtime": {
            "implementation": "NVHPC OpenMP",
            "version": "25.1",
            "threads_per_rank": 8,
        },
        "accelerator_runtime": accelerator,
        "hardware_fingerprint": {
            "id": f"HW-{candidate_id}",
            "sha256": ("d" if gpu else "c") * 64,
            "cpu": {
                "architecture": "x86_64",
                "model": "fixture-cpu",
                "physical_cores": 8,
                "logical_threads": 16,
                "memory_bytes": 64_000_000_000,
            },
            "accelerators": accelerators,
            "topology": {
                "nodes": 1,
                "gpus_per_node": 1 if gpu else 0,
                "numa_nodes_per_node": 1,
                "interconnect": "local",
            },
        },
        "binding": {"cpu": "cores-0-7", "accelerator": "gpu-0" if gpu else "none"},
        "scheduler": {"kind": "local", "job_id": f"JOB-{candidate_id}-{repeat}"},
        "filesystem": {"kind": "local"},
        "input_sha256": "e" * 64,
        "method_fingerprint_id": "METHOD-1",
        "convergence": {"policy_id": "CONV-1", "achieved": True},
        "output_artifact_sha256": "f" * 64,
        "wall_time_seconds": wall_time,
        "cpu_time_seconds": wall_time * 4,
        "scf_iterations": 12,
        "peak_host_memory_bytes": 1_000_000,
        "peak_device_memory_bytes": 2_000_000 if gpu else 0,
        "utilization": {"cpu_percent": 80.0, "accelerator_percent": 90.0 if gpu else 0.0},
        "scientific_results": {
            "energy_ev": -10.0,
            "forces_ev_per_angstrom": [0.001, -0.002, 0.003],
        },
        "parser_acceptance": "PASS",
        "exit_status": 0,
        "timestamp": f"2026-08-05T00:00:0{repeat}Z",
        "repeat_index": repeat,
        "evidence_source": "real-engine-observation",
        "missing_fields": [],
    }


def complete_documents(candidate_wall: float = 5.0) -> list[dict[str, Any]]:
    documents = [result("CPU-REF", repeat, 10.0, gpu=False) for repeat in range(1, 4)]
    documents.extend(result("GPU-CANDIDATE", repeat, candidate_wall, gpu=True) for repeat in range(1, 4))
    return documents


def role_hints() -> dict[str, str]:
    return {
        "CPU-REF": "scientific-reference",
        "GPU-CANDIDATE": "acceleration-candidate",
    }


class ComputeQualificationTests(unittest.TestCase):
    def test_repository_workflow_is_bounded_and_external_hold(self) -> None:
        report = validator.validate()
        self.assertTrue(report["ok"], report["errors"])
        self.assertEqual(report["repository_state"], qualification.EXTERNAL_HOLD)
        self.assertFalse(report["performance_evaluated"])
        self.assertEqual(report["benchmark_result_contract"], "canonical-nested-v1.1")
        self.assertEqual(report["workers_bounded_by"], 8)

    def test_real_repeated_equivalent_campaign_qualifies_for_review_only(self) -> None:
        report = qualification.qualify(campaign(), complete_documents())
        self.assertTrue(report["ok"], report["errors"])
        self.assertEqual(report["state"], qualification.QUALIFIED_FOR_REVIEW)
        self.assertTrue(report["performance"]["evaluated"])
        candidate = report["performance"]["candidates"]["GPU-CANDIDATE"]
        self.assertEqual(candidate["reference_over_candidate_ratio"], 2.0)
        self.assertTrue(candidate["passes"])
        self.assertIn("not signed L3", report["non_claims"][0])

    def test_non_real_evidence_forces_hold_without_ratio(self) -> None:
        documents = complete_documents()
        documents[-1]["evidence_source"] = "simulation"
        report = qualification.qualify(campaign(), documents)
        self.assertTrue(report["ok"], report["errors"])
        self.assertEqual(report["state"], qualification.EXTERNAL_HOLD)
        self.assertFalse(report["performance"]["evaluated"])
        self.assertTrue(any("not real-engine-observation" in hold for hold in report["holds"]))

    def test_numerical_and_performance_failures_are_unqualified(self) -> None:
        numerical = complete_documents()
        numerical[-1]["scientific_results"]["energy_ev"] = -9.0
        report = qualification.qualify(campaign(), numerical)
        self.assertFalse(report["ok"])
        self.assertEqual(report["state"], qualification.UNQUALIFIED)
        self.assertTrue(any("numerical mismatch" in error for error in report["errors"]))

        slow = qualification.qualify(campaign(), complete_documents(candidate_wall=10.0))
        self.assertFalse(slow["ok"])
        self.assertEqual(slow["state"], qualification.UNQUALIFIED)
        self.assertTrue(slow["performance"]["evaluated"])
        self.assertTrue(any("threshold was not met" in error for error in slow["errors"]))

    def test_worker_and_campaign_contracts_fail_closed(self) -> None:
        self.assertEqual(qualification.normalized_workers(1000, 1000), 8)
        with self.assertRaisesRegex(ValueError, "workers must be non-negative"):
            qualification.normalized_workers(-1, 2)
        mutated = copy.deepcopy(campaign())
        mutated["minimum_repeats"] = 2
        self.assertIn("minimum_repeats must be an integer >= 3", qualification.validate_campaign(mutated))

    def test_parallel_loader_is_deterministic_and_schema_migrated(self) -> None:
        schema = qualification.load_json(SCHEMA_PATH)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = [root / "z.json", root / "a.json"]
            paths[0].write_text(json.dumps(result("GPU-CANDIDATE", 1, 5.0, gpu=True)), encoding="utf-8")
            paths[1].write_text(json.dumps(result("CPU-REF", 1, 10.0, gpu=False)), encoding="utf-8")
            documents, errors = qualification.load_results(
                paths,
                schema,
                workers=100,
                role_hints=role_hints(),
            )
        self.assertEqual(errors, [])
        self.assertEqual([document["candidate_id"] for document in documents], ["CPU-REF", "GPU-CANDIDATE"])
        self.assertTrue(all(document["_canonical_schema_version"] == "1.1" for document in documents))

    def test_legacy_flat_loader_requires_explicit_roles(self) -> None:
        schema = qualification.load_json(SCHEMA_PATH)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "legacy.json"
            path.write_text(json.dumps(result("CPU-REF", 1, 10.0, gpu=False)), encoding="utf-8")
            documents, errors = qualification.load_results([path], schema)
        self.assertEqual(documents, [])
        self.assertTrue(any("explicit" in error for error in errors))

    def test_legacy_flat_campaign_remains_external_hold(self) -> None:
        schema = qualification.load_json(SCHEMA_PATH)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = []
            for document in complete_documents():
                path = root / f"{document['candidate_id']}-{document['repeat_index']}.json"
                path.write_text(json.dumps(document), encoding="utf-8")
                paths.append(path)
            documents, errors = qualification.load_results(
                paths,
                schema,
                workers=8,
                role_hints=role_hints(),
            )
        report = qualification.qualify(campaign(), documents, errors)
        self.assertTrue(report["ok"], report["errors"])
        self.assertEqual(report["state"], qualification.EXTERNAL_HOLD)
        self.assertFalse(report["performance"]["evaluated"])
        self.assertTrue(any("missing_fields" in hold for hold in report["holds"]))

    def test_json_loader_rejects_overflowed_nonfinite_numbers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "overflow.json"
            path.write_text('{"wall_time_seconds": 1e999}', encoding="utf-8")
            with self.assertRaisesRegex(
                qualification.QualificationLoadError,
                "non-finite JSON number is forbidden",
            ):
                qualification.load_json(path)


if __name__ == "__main__":
    unittest.main()

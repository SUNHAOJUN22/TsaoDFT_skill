from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_planner():
    path = ROOT / "scripts/plan_acceleration.py"
    spec = importlib.util.spec_from_file_location("tsao_acceleration_planner", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def clone(value: dict[str, Any]) -> dict[str, Any]:
    return yaml.safe_load(yaml.safe_dump(value))


def library(report: dict[str, Any], name: str) -> dict[str, Any]:
    return next(item for item in report["library_assessment"] if item["name"] == name)


class AccelerationPlannerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.planner = load_planner()
        cls.base = yaml.safe_load((ROOT / "templates/acceleration-profile.yaml").read_text(encoding="utf-8"))

    def test_template_builds_an_engine_native_gpu_plan(self):
        report = self.planner.build_plan(clone(self.base))
        self.assertTrue(report["ok"])
        self.assertEqual(report["recommended_path"], "engine-native-gpu")
        self.assertEqual(report["resource_baseline"]["mpi_ranks_per_node"], 4)

    def test_vasp_plan_records_supported_gpu_starting_point(self):
        report = self.planner.build_plan(clone(self.base))
        actions = " ".join(report["engine_actions"])
        self.assertIn("OpenACC", actions)
        self.assertIn("one MPI rank per GPU", actions)
        self.assertIn("NCORE=1", actions)
        self.assertIn("KPAR", actions)

    def test_quantum_espresso_plan_requires_empirical_decomposition(self):
        profile = clone(self.base)
        profile["engine"] = "quantum-espresso"
        report = self.planner.build_plan(profile)
        actions = " ".join(report["engine_actions"])
        self.assertIn("pools", actions)
        self.assertIn("task groups", actions)
        self.assertIn("starting candidate", actions)

    def test_cp2k_plan_covers_gpu_backends_and_solver_choices(self):
        profile = clone(self.base)
        profile["engine"] = "cp2k"
        report = self.planner.build_plan(profile)
        actions = " ".join(report["engine_actions"])
        self.assertIn("CP2K_USE_ACCEL=CUDA", actions)
        self.assertIn("DBCSR", actions)
        self.assertIn("ELPA", actions)

    def test_cuequivariance_is_recommended_only_for_equivariant_ml(self):
        profile = clone(self.base)
        profile["stage"] = "ml-surrogate"
        profile["software"]["engine_gpu_build"] = False
        profile["software"]["model_family"] = "equivariant"
        report = self.planner.build_plan(profile)
        self.assertEqual(report["recommended_path"], "cuda-accelerated-atomistic-ml")
        self.assertEqual(library(report, "cuequivariance")["decision"], "recommended")

    def test_cutensor_is_not_a_drop_in_vasp_flag(self):
        report = self.planner.build_plan(clone(self.base))
        self.assertEqual(library(report, "cutensor")["decision"], "not-drop-in")

    def test_edge_engine_profile_routes_production_dft_remotely(self):
        profile = clone(self.base)
        profile["hardware"]["target"] = "edge"
        report = self.planner.build_plan(profile)
        self.assertEqual(report["recommended_path"], "edge-orchestrated-remote-dft")
        self.assertTrue(any("edge devices" in warning for warning in report["warnings"]))

    def test_cpu_profile_retains_cuda_x_as_not_applicable(self):
        profile = clone(self.base)
        profile["hardware"]["gpu_vendor"] = "none"
        profile["hardware"]["gpus_per_node"] = 0
        profile["software"]["engine_gpu_build"] = False
        profile["software"]["libraries"] = ["cuFFT"]
        report = self.planner.build_plan(profile)
        self.assertTrue(report["ok"])
        self.assertEqual(report["recommended_path"], "cpu-mpi-openmp")
        self.assertEqual(library(report, "cufft")["decision"], "not-applicable")

    def test_gpu_engine_build_without_gpu_is_rejected(self):
        profile = clone(self.base)
        profile["hardware"]["gpu_vendor"] = "none"
        profile["hardware"]["gpus_per_node"] = 0
        report = self.planner.build_plan(profile)
        self.assertFalse(report["ok"])
        self.assertIn("engine_gpu_build requires at least one NVIDIA GPU", report["errors"])

    def test_plans_are_deterministic(self):
        profile = clone(self.base)
        self.assertEqual(self.planner.build_plan(profile), self.planner.build_plan(clone(self.base)))


if __name__ == "__main__":
    unittest.main()

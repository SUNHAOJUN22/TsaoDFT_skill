from __future__ import annotations

import copy
import importlib.util
import math
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/generate_autotuning_candidates.py"


def load_module() -> Any:
    spec = importlib.util.spec_from_file_location("tsao_autotuning_numeric_contract", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


autotune = load_module()


def valid_profile() -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "campaign_id": "NUMERIC-CONTRACT",
        "engine": "vasp",
        "scientific_identity": {
            "input_sha256": "a" * 64,
            "method_fingerprint_id": "METHOD-1",
            "convergence_policy_id": "CONV-1",
        },
        "workload": {
            "atoms": 64,
            "kpoints": 4,
            "estimated_host_memory_gb": 8,
            "estimated_device_memory_gb": 8,
        },
        "hardware": {
            "nodes": 1,
            "cpus_per_node": 32,
            "memory_gb_per_node": 128,
            "gpu_vendor": "nvidia",
            "gpus_per_node": 2,
            "gpu_memory_gb": 80,
        },
        "policy": {
            "precisions": ["fp64", "mixed-validated"],
            "max_candidates": 64,
            "allow_gpu_oversubscription": False,
            "require_fp64_reference": True,
        },
        "tuning": {
            "cpu_tasks_per_node": [1, 2, 4],
            "openmp_threads": [1, 2],
            "ranks_per_gpu": [1],
        },
    }


class AutotuningNumericContractTests(unittest.TestCase):
    def assert_rejected(self, profile: dict[str, Any], expected_error: str) -> None:
        report = autotune.generate(profile)
        self.assertFalse(report["ok"])
        self.assertIn(expected_error, report["errors"])
        self.assertNotIn("candidates", report)
        self.assertNotIn("candidate_count", report)

    def test_hardware_integer_fields_reject_coercion(self) -> None:
        invalid_values: tuple[object, ...] = (True, 1.5, "4", None)
        for field in ("nodes", "cpus_per_node", "gpus_per_node"):
            for invalid in invalid_values:
                profile = valid_profile()
                profile["hardware"][field] = invalid
                with self.subTest(field=field, invalid=invalid):
                    self.assert_rejected(profile, f"hardware.{field} must be an exact integer")

    def test_memory_and_workload_numbers_reject_nonfinite_or_coerced_values(self) -> None:
        fields = (
            ("hardware", "memory_gb_per_node"),
            ("hardware", "gpu_memory_gb"),
            ("workload", "estimated_host_memory_gb"),
            ("workload", "estimated_device_memory_gb"),
        )
        invalid_values: tuple[object, ...] = (True, "8", math.nan, math.inf, -math.inf)
        for section, field in fields:
            for invalid in invalid_values:
                profile = valid_profile()
                profile[section][field] = invalid
                expected = (
                    f"{section}.{field} must be a finite number"
                    if invalid is True or isinstance(invalid, str)
                    else f"{section}.{field} must be finite"
                )
                with self.subTest(section=section, field=field, invalid=invalid):
                    self.assert_rejected(profile, expected)

    def test_workload_integer_fields_reject_coercion(self) -> None:
        invalid_values: tuple[object, ...] = (True, 4.0, "4", None)
        for field in ("atoms", "kpoints"):
            for invalid in invalid_values:
                profile = valid_profile()
                profile["workload"][field] = invalid
                with self.subTest(field=field, invalid=invalid):
                    self.assert_rejected(profile, f"workload.{field} must be an exact integer")

    def test_policy_fields_are_exact_and_fail_closed(self) -> None:
        for invalid in (1, 0, "true", None):
            profile = valid_profile()
            profile["policy"]["allow_gpu_oversubscription"] = invalid
            with self.subTest(field="allow_gpu_oversubscription", invalid=invalid):
                self.assert_rejected(profile, "policy.allow_gpu_oversubscription must be a boolean")

            profile = valid_profile()
            profile["policy"]["require_fp64_reference"] = invalid
            with self.subTest(field="require_fp64_reference", invalid=invalid):
                self.assert_rejected(profile, "policy.require_fp64_reference must be a boolean")

        for invalid in (True, 64.0, "64", None):
            profile = valid_profile()
            profile["policy"]["max_candidates"] = invalid
            with self.subTest(field="max_candidates", invalid=invalid):
                self.assert_rejected(profile, "policy.max_candidates must be an exact integer")

        for invalid in (["fp64", 1], ["fp64", ""], "fp64", []):
            profile = valid_profile()
            profile["policy"]["precisions"] = invalid
            report = autotune.generate(profile)
            with self.subTest(field="precisions", invalid=invalid):
                self.assertFalse(report["ok"])
                self.assertNotIn("candidates", report)

    def test_all_integer_tuning_lists_reject_invalid_members(self) -> None:
        for field in autotune.INTEGER_LIST_FIELDS:
            for invalid in (True, 2.0, "2", None):
                profile = valid_profile()
                profile["tuning"][field] = [1, invalid]
                with self.subTest(field=field, invalid=invalid):
                    self.assert_rejected(profile, f"tuning.{field}[1] must be an exact integer")

        for field in autotune.INTEGER_LIST_FIELDS:
            profile = valid_profile()
            profile["tuning"][field] = []
            with self.subTest(field=field, invalid="empty"):
                self.assert_rejected(profile, f"tuning.{field} must be a non-empty list")

    def test_scalar_tuning_and_boolean_fields_reject_standins(self) -> None:
        for field in autotune.INTEGER_FIELDS:
            for invalid in (True, 4.0, "4", None):
                profile = valid_profile()
                profile["tuning"][field] = invalid
                with self.subTest(field=field, invalid=invalid):
                    self.assert_rejected(profile, f"tuning.{field} must be an exact integer")

        for field in autotune.BOOLEAN_FIELDS:
            for invalid in (1, 0, "true", None):
                profile = valid_profile()
                profile["tuning"][field] = invalid
                with self.subTest(field=field, invalid=invalid):
                    self.assert_rejected(profile, f"tuning.{field} must be a boolean")

    def test_string_tuning_lists_reject_wrong_shapes_and_members(self) -> None:
        for field in autotune.STRING_LIST_FIELDS:
            for invalid in ([], "cg", ["cg", 1], ["cg", ""]):
                profile = valid_profile()
                profile["tuning"][field] = invalid
                report = autotune.generate(profile)
                with self.subTest(field=field, invalid=invalid):
                    self.assertFalse(report["ok"])
                    self.assertNotIn("candidates", report)

    def test_valid_profile_is_deterministic_and_preserves_candidate_contract(self) -> None:
        profile = valid_profile()
        first = autotune.generate(copy.deepcopy(profile))
        second = autotune.generate(copy.deepcopy(profile))
        self.assertEqual(first, second)
        self.assertTrue(first["ok"])
        self.assertGreater(first["candidate_count"], 1)
        self.assertEqual(first["candidates"][0]["candidate_id"], "cpu-fp64-reference")
        self.assertTrue(any(item["backend"] == "openacc" for item in first["candidates"]))
        self.assertTrue(all(item["approval"] == "pending" for item in first["candidates"]))


if __name__ == "__main__":
    unittest.main()

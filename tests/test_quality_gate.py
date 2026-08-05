from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_quality_gate():
    path = ROOT / "scripts" / "quality_gate.py"
    spec = importlib.util.spec_from_file_location("tsao_quality_gate", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


quality_gate = load_quality_gate()


class QualityGateTests(unittest.TestCase):
    def test_dependency_contract_precedes_static_analysis(self):
        names = [stage.name for stage in quality_gate.stages()]
        self.assertEqual(names[1], "dependency contract")
        self.assertLess(names.index("dependency contract"), names.index("Ruff lint"))
        self.assertLess(names.index("CI constraints"), names.index("acceleration contracts"))
        self.assertLess(names.index("acceleration contracts"), names.index("capability claims"))
        self.assertEqual(names[-1], "unit tests")

    def test_skip_tests_removes_only_unit_test_stage(self):
        full = [stage.name for stage in quality_gate.stages()]
        static = [stage.name for stage in quality_gate.stages(include_tests=False)]
        self.assertEqual(static, full[:-1])
        self.assertNotIn("unit tests", static)

    def test_stage_timeout_is_reported_deterministically(self):
        stage = quality_gate.Stage(
            "timeout fixture",
            (sys.executable, "-c", "import time; time.sleep(0.2)"),
            timeout_seconds=0.01,
        )
        result = quality_gate.run_stage(stage, os.environ.copy(), capture_output=True)
        self.assertEqual(result["returncode"], 124)
        self.assertTrue(result["timed_out"])
        self.assertEqual(result["timeout_seconds"], 0.01)

    def test_non_positive_timeout_is_rejected_by_cli(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/quality_gate.py"), "--timeout", "0"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("--timeout must be positive", result.stderr)


if __name__ == "__main__":
    unittest.main()

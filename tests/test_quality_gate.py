from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import quality_gate  # noqa: E402


class QualityGateTests(unittest.TestCase):
    def test_dependency_contract_precedes_static_analysis(self):
        names = [stage.name for stage in quality_gate.stages()]
        self.assertEqual(names[1], "dependency contract")
        self.assertLess(names.index("dependency contract"), names.index("Ruff lint"))
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

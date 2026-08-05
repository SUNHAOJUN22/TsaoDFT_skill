from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "capture_compute_contract_evidence.py"


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


capture = load_module("tsao_compute_contract_evidence_tests", SCRIPT)


class ComputeContractEvidenceTests(unittest.TestCase):
    def test_current_repository_is_machine_readable_external_hold(self) -> None:
        report = capture.build_report()
        self.assertTrue(report["ok"], report["errors"])
        self.assertEqual(report["state"], capture.EXTERNAL_HOLD)
        self.assertFalse(report["external_engine_invoked"])
        self.assertTrue(report["acceleration_registry"]["runtime_single_source"])
        self.assertEqual(report["benchmark_contract"]["canonical_contract"], "nested-v1.1")
        self.assertTrue(report["benchmark_contract"]["root_mirror_synchronized"])
        self.assertEqual(report["benchmark_contract"]["legacy_flat_qualification_impact"], capture.EXTERNAL_HOLD)
        self.assertEqual(report["benchmark_contract"]["unknown_or_mixed_input"], "FAIL_CLOSED")
        self.assertEqual(report["engine_capabilities"]["repository_template_state"], capture.EXTERNAL_HOLD)
        self.assertEqual(report["engine_capabilities"]["performance_qualification"], "NOT_ESTABLISHED")
        self.assertEqual(report["compute_qualification"]["repository_state"], capture.EXTERNAL_HOLD)
        self.assertEqual(report["compute_qualification"]["benchmark_result_contract"], "canonical-nested-v1.1")
        self.assertFalse(report["compute_qualification"]["performance_evaluated"])
        self.assertEqual(report["compute_qualification"]["workers_bounded_by"], 8)
        self.assertFalse(report["performance_ratio_published"])

    def test_capture_is_deterministic(self) -> None:
        first = capture.build_report()
        second = capture.build_report()
        self.assertEqual(first, second)

    def test_validator_failure_is_unqualified(self) -> None:
        broken = type("BrokenValidator", (), {"validate": staticmethod(lambda: {"ok": False})})()
        with patch.object(capture, "load_module", return_value=broken):
            report = capture.build_report()
        self.assertFalse(report["ok"])
        self.assertEqual(report["state"], capture.UNQUALIFIED)
        self.assertTrue(any("validator failed" in error for error in report["errors"]))

    def test_write_and_cli_outputs(self) -> None:
        capture.write_report(None, {"ok": True})
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "nested" / "evidence.json"
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), "--out", str(output), "--json"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            stdout = json.loads(completed.stdout)
            written = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(stdout, written)
            self.assertEqual(written["state"], capture.EXTERNAL_HOLD)


if __name__ == "__main__":
    unittest.main()

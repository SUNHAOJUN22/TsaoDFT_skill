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
        self.assertEqual(report["schema_version"], "1.2")
        self.assertEqual(report["state"], capture.EXTERNAL_HOLD)
        self.assertFalse(report["external_engine_invoked"])
        self.assertTrue(report["acceleration_registry"]["runtime_single_source"])
        benchmark = report["benchmark_contract"]
        self.assertEqual(benchmark["canonical_contract"], "nested-v1.1")
        self.assertTrue(benchmark["root_mirror_synchronized"])
        self.assertEqual(benchmark["native_semantic_schema_version"], "1.1")
        self.assertFalse(benchmark["compatibility_view_present"])
        self.assertEqual(benchmark["legacy_semantic_bypass"], "FAIL_CLOSED")
        self.assertEqual(benchmark["legacy_flat_qualification_impact"], capture.EXTERNAL_HOLD)
        self.assertEqual(benchmark["unknown_or_mixed_input"], "FAIL_CLOSED")
        self.assertEqual(report["engine_capabilities"]["repository_template_state"], capture.EXTERNAL_HOLD)
        self.assertEqual(report["engine_capabilities"]["performance_qualification"], "NOT_ESTABLISHED")
        self.assertEqual(report["compute_qualification"]["repository_state"], capture.EXTERNAL_HOLD)
        self.assertEqual(report["compute_qualification"]["benchmark_result_contract"], "canonical-nested-v1.1")
        self.assertFalse(report["compute_qualification"]["performance_evaluated"])
        self.assertEqual(report["compute_qualification"]["workers_bounded_by"], 8)
        self.assertFalse(report["performance_ratio_published"])
        self.assertTrue(any("No nested v1.0 semantic downgrade view" in item for item in report["non_claims"]))

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

    def test_semantic_contract_drift_is_unqualified(self) -> None:
        reports = {
            "acceleration_registry": {
                "ok": True,
                "validated_surfaces": ["runtime_single_source"],
            },
            "benchmark_contract": {
                "ok": True,
                "canonical_contract": "nested-v1.1",
                "root_mirror_synchronized": True,
                "native_semantic_schema_version": "1.0",
                "compatibility_view_present": True,
                "legacy_semantic_bypass": "OPEN",
                "legacy_flat_qualification_impact": capture.EXTERNAL_HOLD,
                "unknown_or_mixed_input": "FAIL_CLOSED",
                "external_engine_invoked": False,
            },
            "engine_capabilities": {
                "ok": True,
                "repository_template_state": capture.EXTERNAL_HOLD,
                "performance_qualification": "NOT_ESTABLISHED",
            },
            "compute_qualification": {
                "ok": True,
                "repository_state": capture.EXTERNAL_HOLD,
                "performance_evaluated": False,
                "workers_bounded_by": 8,
            },
        }

        def fake_load(name: str, _: Path) -> object:
            key = name.removeprefix("tsao_contract_evidence_")
            return type("Validator", (), {"validate": staticmethod(lambda: reports[key])})()

        with patch.object(capture, "load_module", side_effect=fake_load):
            report = capture.build_report()
        self.assertFalse(report["ok"])
        self.assertEqual(report["state"], capture.UNQUALIFIED)
        self.assertTrue(any("not native" in error for error in report["errors"]))
        self.assertTrue(any("compatibility view" in error for error in report["errors"]))
        self.assertTrue(any("bypass" in error for error in report["errors"]))

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
            self.assertEqual(written["schema_version"], "1.2")
            self.assertEqual(written["state"], capture.EXTERNAL_HOLD)


if __name__ == "__main__":
    unittest.main()

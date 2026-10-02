"""Runtime report routing must preserve every qualification stage and timeout."""

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

_PATH = Path(__file__).resolve().parents[1] / "scripts/quality_gate.py"
_SPEC = importlib.util.spec_from_file_location("quality_runtime_reports", _PATH)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _MODULE
_SPEC.loader.exec_module(_MODULE)


class QualityRuntimeReportTests(unittest.TestCase):
    def test_runtime_reports_do_not_change_the_gate_inventory(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            baseline = _MODULE.stages()
            routed = _MODULE.stages_for_reports(True, output)
            self.assertEqual(len(routed), 29)
            for original, current in zip(baseline, routed, strict=True):
                self.assertEqual(current.name, original.name)
                self.assertEqual(current.timeout_seconds, original.timeout_seconds)
                if current.name == "release acceptance":
                    self.assertEqual(current.command[-1], str(output / "release-acceptance.json"))
                    self.assertEqual(current.command[:-1], original.command[:-1])
                elif current.name == "coverage":
                    self.assertEqual(current.command[:-2], original.command)
                    self.assertEqual(current.command[-2:], ("--report", str(output / "coverage-report.json")))
                else:
                    self.assertEqual(current.command, original.command)

    def test_legacy_routing_and_static_inventory_are_preserved(self):
        self.assertEqual(_MODULE.stages_for_reports(True, None), _MODULE.stages())
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(
                [s.name for s in _MODULE.stages_for_reports(False, Path(directory))],
                [s.name for s in _MODULE.stages(False)],
            )

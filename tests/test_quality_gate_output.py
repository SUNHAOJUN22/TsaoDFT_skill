from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("quality_gate_output_tests", ROOT / "scripts" / "quality_gate.py")
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load quality gate")
quality_gate = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = quality_gate
SPEC.loader.exec_module(quality_gate)


class QualityGateOutputTests(unittest.TestCase):
    def test_timeout_preserves_byte_text_and_empty_diagnostics(self):
        stage = quality_gate.Stage("timeout", (sys.executable, "-c", "pass"))
        cases = [
            (b"stdout line\n", b"stderr line\n", "stdout line\nstderr line"),
            ("text out\n", "text err\n", "text out\ntext err"),
            (None, None, ""),
            ("temperature \u6e29\u5ea6\n".encode(), b"\xe4\xb8", "temperature \u6e29\u5ea6\n\\xe4\\xb8"),
            (b"bad byte \xff", None, "bad byte \\xff"),
        ]
        for stdout, stderr, expected in cases:
            with self.subTest(stdout=stdout, stderr=stderr):
                failure = subprocess.TimeoutExpired(stage.command, 0.1, output=stdout, stderr=stderr)
                with patch.object(quality_gate.subprocess, "run", side_effect=failure):
                    result = quality_gate.run_stage(stage, os.environ.copy(), capture_output=True)
                self.assertEqual(result["returncode"], 124)
                self.assertTrue(result["timed_out"])
                self.assertEqual(result["output"], expected)
                json.dumps(result, allow_nan=False)

    def test_real_timeout_keeps_flushed_stdout_and_stderr(self):
        code = "import os,time; os.write(1,b'out-before-timeout\\n'); os.write(2,b'err-before-timeout\\n'); time.sleep(10)"
        stage = quality_gate.Stage("real timeout", (sys.executable, "-c", code), timeout_seconds=1.0)
        result = quality_gate.run_stage(stage, os.environ.copy(), capture_output=True)
        self.assertEqual(result["returncode"], 124)
        self.assertIn("out-before-timeout", result["output"])
        self.assertIn("err-before-timeout", result["output"])

    def test_non_utf8_failure_is_a_stage_result_not_a_decoder_crash(self):
        code = "import os,sys; os.write(1,b'out\\xff\\n'); os.write(2,b'err\\xe4\\xb8'); sys.exit(7)"
        stage = quality_gate.Stage("invalid UTF-8", (sys.executable, "-c", code))
        result = quality_gate.run_stage(stage, os.environ.copy(), capture_output=True)
        self.assertEqual(result["returncode"], 7)
        self.assertFalse(result["timed_out"])
        self.assertEqual(result["output"], "out\\xff\nerr\\xe4\\xb8")

    def test_decode_failure_does_not_prevent_unqualified_receipt(self):
        code = "import os,sys; os.write(2,b'failure\\xff'); sys.exit(3)"
        stage = quality_gate.Stage("invalid bytes", (sys.executable, "-c", code))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(quality_gate, "ROOT", root), patch.object(
                quality_gate, "stages", return_value=[stage]
            ), patch.object(sys, "argv", ["quality_gate.py", "--json"]), redirect_stdout(StringIO()):
                self.assertEqual(quality_gate.main(), 1)
            receipt = json.loads((root / "quality-run-acceptance.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["acceptance_state"], "UNQUALIFIED")
        self.assertFalse(receipt["ok"])
        self.assertEqual(receipt["stages"][0]["returncode"], 3)
        self.assertIn("failure\\xff", receipt["stages"][0]["output"])

    def test_capture_disabled_keeps_output_out_of_receipt(self):
        stage = quality_gate.Stage("timeout", (sys.executable, "-c", "pass"))
        failure = subprocess.TimeoutExpired(stage.command, 0.1, output=b"unused")
        with patch.object(quality_gate.subprocess, "run", side_effect=failure):
            result = quality_gate.run_stage(stage, os.environ.copy(), capture_output=False)
        self.assertEqual(result["returncode"], 124)
        self.assertNotIn("output", result)


if __name__ == "__main__":
    unittest.main()

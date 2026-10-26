from __future__ import annotations

import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
FINDING = {
    "filename": "scripts/allowed.py",
    "test_id": "B404",
    "issue_severity": "LOW",
    "line_number": 1,
}


class BanditScanIntegrityTests(unittest.TestCase):
    runner: Any

    @classmethod
    def setUpClass(cls) -> None:
        spec = importlib.util.spec_from_file_location("bandit_scan_integrity", ROOT / "scripts/run_bandit.py")
        if spec is None or spec.loader is None:
            raise RuntimeError("cannot import Bandit gate")
        cls.runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.runner)

    def run_payload(self, payload: Any, returncode: int) -> tuple[list[dict[str, Any]], str]:
        def run(command: list[str], **_: Any) -> subprocess.CompletedProcess[str]:
            Path(command[-1]).write_text(json.dumps(payload), encoding="utf-8")
            return subprocess.CompletedProcess(command, returncode, stdout="scan output", stderr="diagnostics")

        with patch.object(self.runner.subprocess, "run", side_effect=run):
            result: tuple[list[dict[str, Any]], str] = self.runner.run_bandit()
            return result

    def test_complete_findings_keep_allowlist_semantics(self) -> None:
        findings, output = self.run_payload({"errors": [], "results": [FINDING]}, 1)
        self.assertEqual(findings, [FINDING])
        self.assertEqual(output, "scan outputdiagnostics")
        with (
            patch.object(self.runner, "run_bandit", return_value=(findings, output)),
            patch.object(self.runner, "load_allowlist", return_value={("scripts/allowed.py", "B404"): "reviewed"}),
        ):
            self.assertEqual(self.runner.validate()[0], [])

    def test_clean_scan_without_findings(self) -> None:
        self.assertEqual(self.run_payload({"errors": [], "results": []}, 0)[0], [])

    def test_scan_errors_fail_with_or_without_findings(self) -> None:
        error = {"filename": "scripts/unscanned.py", "reason": "syntax error while parsing AST from file"}
        for returncode, findings in ((0, []), (1, [FINDING])):
            with self.subTest(returncode=returncode), self.assertRaisesRegex(RuntimeError, "unscanned.py"):
                self.run_payload({"errors": [error], "results": findings}, returncode)

    def test_report_structure_is_required(self) -> None:
        invalid: list[Any] = [
            [],
            {"results": []},
            {"errors": {}},
            {"errors": []},
            {"errors": [], "results": {}},
            {"errors": [], "results": ["discarded finding"]},
            {"errors": [], "results": [{"test_id": "B404"}]},
            {"errors": [], "results": [{**FINDING, "filename": ""}]},
            {"errors": [], "results": [{**FINDING, "issue_severity": "unexpected"}]},
            {"errors": [], "results": [{**FINDING, "line_number": 0}]},
        ]
        for index, payload in enumerate(invalid):
            with self.subTest(index=index), self.assertRaises(RuntimeError):
                self.run_payload(payload, 0)

    def test_abnormal_or_inconsistent_exit_status_fails(self) -> None:
        for returncode in (2, 127, -15):
            with self.subTest(returncode=returncode), self.assertRaisesRegex(RuntimeError, "exit"):
                self.run_payload({"errors": [], "results": []}, returncode)
        for returncode, findings in ((1, []), (0, [FINDING])):
            with self.subTest(returncode=returncode, findings=findings), self.assertRaisesRegex(RuntimeError, "exit"):
                self.run_payload({"errors": [], "results": findings}, returncode)

    def test_real_bandit_partial_scan_cannot_receive_cli_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "scripts").mkdir()
            (root / "skills").mkdir()
            (root / "scripts/allowed.py").write_text("import subprocess\n", encoding="utf-8")
            with (
                patch.object(self.runner, "ROOT", root),
                patch.object(
                    self.runner,
                    "load_allowlist",
                    return_value={("scripts/allowed.py", "B404"): "reviewed benign fixture import"},
                ),
            ):
                self.assertEqual(self.runner.validate()[0], [])
                (root / "scripts/unscanned.py").write_text("def unfinished(\n", encoding="utf-8")
                with patch.object(sys, "argv", ["run_bandit.py", "--json"]), redirect_stdout(io.StringIO()) as out:
                    status = self.runner.main()
                report = json.loads(out.getvalue())
                self.assertEqual(status, 1, report)
                self.assertIs(report["ok"], False)
                self.assertIn("unscanned.py", " ".join(report["failures"]))


if __name__ == "__main__":
    unittest.main()

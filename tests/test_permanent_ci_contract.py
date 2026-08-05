from __future__ import annotations

import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


class PermanentCIContractTests(unittest.TestCase):
    def test_only_permanent_ci_workflow_is_present(self) -> None:
        workflows = ROOT / ".github" / "workflows"
        self.assertEqual(sorted(path.name for path in workflows.iterdir() if path.is_file()), ["ci.yml"])

    def test_permanent_ci_is_read_only_and_complete(self) -> None:
        path = ROOT / ".github" / "workflows" / "ci.yml"
        text = path.read_text(encoding="utf-8")
        data = yaml.safe_load(text)
        self.assertEqual(data["name"], "TsaoDFT quality and security gates")
        self.assertEqual(data["permissions"], {"contents": "read"})
        self.assertEqual(data["concurrency"]["cancel-in-progress"], True)
        self.assertEqual(
            set(data["jobs"]),
            {"quality-gate", "windows-control-plane", "supply-chain", "codeql"},
        )
        self.assertEqual(data["jobs"]["quality-gate"]["timeout-minutes"], 25)
        self.assertEqual(data["jobs"]["windows-control-plane"]["timeout-minutes"], 40)
        self.assertEqual(data["jobs"]["supply-chain"]["timeout-minutes"], 25)
        self.assertEqual(data["jobs"]["codeql"]["timeout-minutes"], 30)
        matrix = data["jobs"]["quality-gate"]["strategy"]["matrix"]["include"]
        versions = [item["python-version"] for item in matrix]
        constraints = [item["constraint"] for item in matrix]
        self.assertEqual(versions, ["3.10", "3.12", "3.13"])
        self.assertEqual(
            constraints,
            ["constraints/py310.txt", "constraints/py312.txt", "constraints/py313.txt"],
        )
        self.assertFalse(data["jobs"]["quality-gate"]["strategy"]["fail-fast"])
        self.assertIn("python scripts/quality_gate.py", text)
        self.assertIn("scripts\\quality_gate.ps1", text)
        self.assertIn("inspect_windows_environment.ps1", text)
        self.assertIn("coverage-report.json", text)
        self.assertIn("pip_audit", text)
        self.assertIn("cyclonedx-json", text)
        self.assertIn("security-extended", text)
        self.assertNotIn("contents: write", text)
        self.assertNotIn("git push", text)
        self.assertNotIn("Invoke-Expression", text)
        self.assertNotIn("Start-Process", text)

    def test_windows_control_plane_is_real_private_and_evidence_preserving(self) -> None:
        path = ROOT / ".github" / "workflows" / "ci.yml"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        job = data["jobs"]["windows-control-plane"]
        self.assertEqual(job["runs-on"], "windows-latest")
        self.assertEqual(job["permissions"], {"contents": "read", "statuses": "write"})
        steps = job["steps"]
        by_name = {step["name"]: step for step in steps}

        setup = by_name["Setup Python 3.12"]
        self.assertEqual(setup["with"]["python-version"], "3.12")
        self.assertIn("constraints/py312.txt", setup["with"]["cache-dependency-path"])

        inventory = by_name["Capture privacy-bounded Windows inventory"]
        self.assertEqual(inventory["shell"], "pwsh")
        for fragment in (
            "inspect_windows_environment.ps1",
            "windows-environment.json",
            "external_dft_engine_invoked",
            "NOT_ELIGIBLE",
            "hostname_recorded",
            "username_recorded",
            "home_path_recorded",
            "environment_values_recorded",
            "executable_paths_recorded",
        ):
            self.assertIn(fragment, inventory["run"])

        capture = by_name["Capture complete PowerShell quality gate"]
        self.assertEqual(capture["id"], "windows-gate")
        self.assertEqual(capture["shell"], "pwsh")
        for fragment in (
            "quality_gate.ps1",
            "windows-quality-gate.log",
            "Tee-Object",
            "$LASTEXITCODE",
            "$env:GITHUB_OUTPUT",
            "exit_code=$code",
        ):
            self.assertIn(fragment, capture["run"])

        upload = by_name["Upload Windows control-plane evidence"]
        self.assertEqual(upload["if"], "always()")
        self.assertEqual(upload["with"]["if-no-files-found"], "error")
        for report in (
            "windows-environment.json",
            "windows-quality-gate.log",
            "coverage-report.json",
        ):
            self.assertIn(report, upload["with"]["path"])

        status = by_name["Publish best-effort Windows compatibility summary"]
        self.assertTrue(status["continue-on-error"])
        self.assertIn("tsao-dft/windows-powershell", status["run"])
        self.assertIn("GATE_EXIT_CODE", status["env"])

        failure = by_name["Fail job when PowerShell quality gate fails"]
        self.assertIn("steps.windows-gate.outputs.exit_code", failure["if"])
        self.assertEqual(failure["run"], "exit 1")

    def test_supply_chain_reports_are_always_preserved_before_failure(self) -> None:
        path = ROOT / ".github" / "workflows" / "ci.yml"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        steps = data["jobs"]["supply-chain"]["steps"]
        by_name = {step["name"]: step for step in steps}

        capture = by_name["Capture all dependency audits and SBOM"]
        self.assertEqual(capture["id"], "audit")
        self.assertIn("set +e", capture["run"])
        for output in (
            "runtime_exit_code",
            "development_exit_code",
            "locked_exit_code",
            "sbom_exit_code",
        ):
            self.assertIn(output, capture["run"])
        self.assertIn("audit command did not produce a report", capture["run"])

        upload = by_name["Upload supply-chain evidence"]
        self.assertEqual(upload["if"], "always()")
        self.assertEqual(upload["with"]["if-no-files-found"], "error")
        for report in (
            "pip-audit-runtime.json",
            "pip-audit-development.json",
            "pip-audit-locked.json",
            "sbom.cdx.json",
        ):
            self.assertIn(report, upload["with"]["path"])

        failure = by_name["Fail job when an audit or SBOM command fails"]
        self.assertEqual(failure["run"], "exit 1")
        condition = failure["if"]
        for output in (
            "runtime_exit_code",
            "development_exit_code",
            "locked_exit_code",
            "sbom_exit_code",
        ):
            self.assertIn(f"steps.audit.outputs.{output}", condition)


if __name__ == "__main__":
    unittest.main()

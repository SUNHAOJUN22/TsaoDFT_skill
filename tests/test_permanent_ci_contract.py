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
        self.assertEqual(set(data["jobs"]), {"quality-gate", "supply-chain", "codeql"})
        self.assertEqual(data["jobs"]["quality-gate"]["timeout-minutes"], 25)
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
        self.assertIn("coverage-report.json", text)
        self.assertIn("pip_audit", text)
        self.assertIn("cyclonedx-json", text)
        self.assertIn("security-extended", text)
        self.assertNotIn("contents: write", text)
        self.assertNotIn("git push", text)

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

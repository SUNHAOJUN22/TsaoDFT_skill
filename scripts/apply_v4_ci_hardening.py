#!/usr/bin/env python3
"""Convert permanent DFT CI from delayed failures to direct fail-closed gates."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_pattern(text: str, pattern: str, replacement: str, label: str) -> str:
    updated, count = re.subn(
        pattern,
        lambda _match: replacement,
        text,
        count=1,
        flags=re.DOTALL,
    )
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, found {count}")
    return updated


def main() -> int:
    workflow_path = ROOT / ".github" / "workflows" / "ci.yml"
    workflow = workflow_path.read_text(encoding="utf-8")
    workflow = replace_pattern(
        workflow,
        r"      - name: Capture complete quality gate\n.*?(?=      - name: Upload failure log)",
        """      - name: Run complete quality gate
        shell: bash
        run: |
          set -euo pipefail
          python scripts/quality_gate.py 2>&1 | tee quality-gate.log

""",
        "Linux quality gate",
    )
    workflow = workflow.replace(
        "        if: always() && steps.gate.outputs.exit_code != '0'\n",
        "        if: failure()\n",
        1,
    )
    workflow = replace_pattern(
        workflow,
        r"\n      - name: Publish best-effort compatibility summary\n.*?\n      - name: Fail job when quality gate fails\n.*?(?=\n  windows-control-plane:)",
        "",
        "Linux delayed failure blocks",
    )
    workflow = replace_pattern(
        workflow,
        r"      - name: Capture complete PowerShell quality gate\n.*?(?=      - name: Upload Windows control-plane evidence)",
        """      - name: Run complete PowerShell quality gate
        shell: pwsh
        run: |
          $pwsh = (Get-Command -Name "pwsh" -CommandType Application -ErrorAction Stop).Source
          & $pwsh -NoProfile -File ".\\scripts\\quality_gate.ps1" *>&1 |
            Tee-Object -FilePath "windows-quality-gate.log"
          if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

""",
        "Windows quality gate",
    )
    workflow = replace_pattern(
        workflow,
        r"\n      - name: Publish best-effort Windows compatibility summary\n.*?\n      - name: Fail job when PowerShell quality gate fails\n.*?(?=\n  supply-chain:)",
        "",
        "Windows delayed failure blocks",
    )
    workflow = replace_pattern(
        workflow,
        r"      - name: Capture all dependency audits and SBOM\n.*?(?=      - name: Upload supply-chain evidence)",
        """      - name: Audit runtime dependencies
        shell: bash
        run: |
          set -euo pipefail
          python -m pip_audit -r requirements.txt --format json --output pip-audit-runtime.json
          test -s pip-audit-runtime.json

      - name: Audit development dependencies
        if: always()
        shell: bash
        run: |
          set -euo pipefail
          python -m pip_audit -r requirements-dev.txt --format json --output pip-audit-development.json
          test -s pip-audit-development.json

      - name: Audit locked constraints
        if: always()
        shell: bash
        run: |
          set -euo pipefail
          python -m pip_audit --no-deps -r constraints/py312.txt --format json --output pip-audit-locked.json
          test -s pip-audit-locked.json

      - name: Generate CycloneDX SBOM
        if: always()
        shell: bash
        run: |
          set -euo pipefail
          python -m pip_audit --no-deps -r constraints/py312.txt --format cyclonedx-json --output sbom.cdx.json
          test -s sbom.cdx.json

""",
        "supply-chain capture",
    )
    workflow = replace_pattern(
        workflow,
        r"\n      - name: Fail job when an audit or SBOM command fails\n.*?(?=\n  codeql:)",
        "",
        "supply-chain delayed failure block",
    )
    for forbidden in (
        "continue-on-error:",
        "set +e",
        "steps.gate.outputs",
        "steps.windows-gate.outputs",
        "steps.audit.outputs",
        "best-effort compatibility summary",
        "Fail job when",
    ):
        if forbidden in workflow:
            raise RuntimeError(f"forbidden delayed-failure construct remains: {forbidden}")
    workflow_path.write_text(workflow, encoding="utf-8", newline="\n")

    tests_path = ROOT / "tests" / "test_permanent_ci_contract.py"
    tests = tests_path.read_text(encoding="utf-8")
    windows_method = '''    def test_windows_control_plane_is_real_private_and_evidence_preserving(self) -> None:
        path = ROOT / ".github" / "workflows" / "ci.yml"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        job = data["jobs"]["windows-control-plane"]
        self.assertEqual(job["runs-on"], "windows-latest")
        self.assertEqual(job["permissions"], {"contents": "read", "statuses": "write"})
        steps = job["steps"]
        by_name = {step["name"]: step for step in steps}

        gate = by_name["Run complete PowerShell quality gate"]
        self.assertNotIn("id", gate)
        self.assertEqual(gate["shell"], "pwsh")
        for fragment in (
            "quality_gate.ps1",
            "windows-quality-gate.log",
            "Tee-Object",
            "$LASTEXITCODE",
            "exit $LASTEXITCODE",
        ):
            self.assertIn(fragment, gate["run"])
        self.assertNotIn("GITHUB_OUTPUT", gate["run"])

        upload = by_name["Upload Windows control-plane evidence"]
        self.assertEqual(upload["if"], "always()")
        self.assertEqual(upload["with"]["if-no-files-found"], "error")
        for report in (
            "windows-environment.json",
            "windows-quality-gate.log",
            "coverage-report.json",
        ):
            self.assertIn(report, upload["with"]["path"])

        self.assertNotIn("Publish best-effort Windows compatibility summary", by_name)
        self.assertNotIn("Fail job when PowerShell quality gate fails", by_name)

'''
    tests = replace_pattern(
        tests,
        r"    def test_windows_control_plane_is_real_private_and_evidence_preserving\(self\) -> None:\n.*?(?=    def test_supply_chain_reports_are_always_preserved_before_failure)",
        windows_method,
        "Windows governance test",
    )
    supply_method = '''    def test_supply_chain_reports_are_always_preserved_before_failure(self) -> None:
        path = ROOT / ".github" / "workflows" / "ci.yml"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        steps = data["jobs"]["supply-chain"]["steps"]
        by_name = {step["name"]: step for step in steps}

        direct_steps = (
            ("Audit runtime dependencies", "pip-audit-runtime.json"),
            ("Audit development dependencies", "pip-audit-development.json"),
            ("Audit locked constraints", "pip-audit-locked.json"),
            ("Generate CycloneDX SBOM", "sbom.cdx.json"),
        )
        for index, (name, report) in enumerate(direct_steps):
            step = by_name[name]
            if index:
                self.assertEqual(step["if"], "always()")
            self.assertEqual(step["shell"], "bash")
            self.assertIn("set -euo pipefail", step["run"])
            self.assertIn(report, step["run"])
            self.assertNotIn("set +e", step["run"])
            self.assertNotIn("GITHUB_OUTPUT", step["run"])

        upload = by_name["Upload supply-chain evidence"]
        self.assertEqual(upload["if"], "always()")
        self.assertEqual(upload["with"]["if-no-files-found"], "error")
        for _, report in direct_steps:
            self.assertIn(report, upload["with"]["path"])

        self.assertNotIn("Capture all dependency audits and SBOM", by_name)
        self.assertNotIn("Fail job when an audit or SBOM command fails", by_name)
'''
    tests = replace_pattern(
        tests,
        r"    def test_supply_chain_reports_are_always_preserved_before_failure\(self\) -> None:\n.*?(?=\n\nif __name__)",
        supply_method,
        "supply-chain governance test",
    )
    tests_path.write_text(tests, encoding="utf-8", newline="\n")

    (ROOT / ".github" / "workflows" / "v4-ci-export-once.yml").unlink()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

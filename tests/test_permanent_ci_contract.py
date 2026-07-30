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
        self.assertEqual(set(data["jobs"]), {"quality-gate", "supply-chain", "codeql"})
        self.assertEqual(data["jobs"]["quality-gate"]["timeout-minutes"], 25)
        self.assertIn("python scripts/quality_gate.py", text)
        self.assertIn("pip_audit", text)
        self.assertIn("cyclonedx-json", text)
        self.assertIn("security-extended", text)
        self.assertNotIn("contents: write", text)
        self.assertNotIn("git push", text)


if __name__ == "__main__":
    unittest.main()

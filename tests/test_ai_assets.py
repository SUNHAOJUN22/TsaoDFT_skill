from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
import sys
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "assets/ai/manifest.yaml"


class AIAssetTests(unittest.TestCase):
    def test_manifest_policy_and_hashes(self):
        data = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(data["release"], "0.4.0-alpha.1")
        self.assertGreaterEqual(len(data["assets"]), 8)
        for item in data["assets"]:
            self.assertTrue(item["ai_generated"])
            self.assertTrue(item["illustrative_only"])
            self.assertFalse(item["quantitative"])
            self.assertFalse(item["computed_surface"])
            path = ROOT / item["path"]
            self.assertTrue(path.is_file(), item["path"])
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), item["sha256"])

    def test_readme_uses_multiple_ai_concepts(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertGreaterEqual(text.count("assets/ai/"), 8)
        self.assertIn("AI-GENERATED CONCEPTUAL ILLUSTRATION", text)
        self.assertIn("assets/demo/", text)

    def test_validator_cli(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/validate_ai_assets.py")],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()

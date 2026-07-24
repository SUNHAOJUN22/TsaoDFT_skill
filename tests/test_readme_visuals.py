from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]


class ReadmeVisualTests(unittest.TestCase):
    def test_all_governed_ai_assets_are_embedded(self):
        manifest = yaml.safe_load((ROOT / "assets/ai/manifest.yaml").read_text(encoding="utf-8"))
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for item in manifest["assets"]:
            self.assertIn(item["path"], readme)

    def test_readme_has_ai_and_deterministic_visuals(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertGreaterEqual(readme.count("assets/ai/"), 8)
        self.assertGreaterEqual(readme.count("assets/demo/"), 6)
        self.assertIn("AI图像声明", readme)
        hero = (ROOT / "assets/ai/hero/tsao-dft-hero.svg").read_text(encoding="utf-8")
        self.assertIn("NOT COMPUTATIONAL DATA", hero)

    def test_readme_visual_validator(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/validate_readme_visuals.py"), "--strict"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()

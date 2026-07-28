from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str) -> ModuleType:
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"tsao_{name}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SecurityGateTests(unittest.TestCase):
    def test_every_skill_declares_untrusted_content_boundary(self):
        skills = sorted((ROOT / "skills").glob("*/SKILL.md"))
        self.assertEqual(len(skills), 8)
        for path in skills:
            text = path.read_text(encoding="utf-8")
            self.assertIn("## Untrusted content and instruction hierarchy", text, path)
            self.assertIn("untrusted data", text, path)
            self.assertIn("explicit user approval", text, path)

    def test_xml_validators_use_defusedxml(self):
        for rel in (
            "scripts/generate_readme_demos.py",
            "scripts/validate_ai_assets.py",
            "scripts/validate_readme_visuals.py",
            "scripts/validate_repo.py",
        ):
            text = (ROOT / rel).read_text(encoding="utf-8")
            self.assertIn("from defusedxml import ElementTree as ET", text, rel)
            self.assertNotIn("import xml.etree.ElementTree", text, rel)

    def test_packaging_model_contract(self):
        validator = load_script("validate_packaging_model")
        self.assertEqual(validator.validate(), [])

    def test_ignore_markers_are_explained(self):
        validator = load_script("validate_ignore_markers")
        failures, markers = validator.validate()
        self.assertEqual(failures, [])
        self.assertGreater(len(markers), 0)

    def test_bandit_allowlist_has_no_duplicate_contracts(self):
        runner = load_script("run_bandit")
        allowlist = runner.load_allowlist()
        self.assertEqual(len(allowlist), 10)
        self.assertTrue(all(reason.strip() for reason in allowlist.values()))


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_validator():
    path = ROOT / "scripts" / "validate_capability_claims.py"
    spec = importlib.util.spec_from_file_location("tsao_validate_capability_claims", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = load_validator()


class CapabilityClaimTests(unittest.TestCase):
    def test_current_repository_claim_contract(self):
        self.assertEqual(validator.validate(ROOT), [])

    def make_fixture(self, root: Path, *, level: str = "L2_VALIDATED_ADAPTER", phrase: str = "") -> None:
        (root / "docs").mkdir()
        (root / "skills" / "fixture" / "scripts").mkdir(parents=True)
        (root / "skills" / "fixture" / "scripts" / "run.py").write_text("pass\n", encoding="utf-8")
        (root / "skills" / "fixture" / "SKILL.md").write_text(
            f"fixture {phrase}\n",
            encoding="utf-8",
        )
        (root / "VERSION").write_text("0.4.0-alpha.1\n", encoding="utf-8")
        policy = {
            "schema_version": "1.0",
            "release": "0.4.0-alpha.1",
            "support_levels": [
                "L0_REFERENCE",
                "L1_HANDOFF",
                "L2_VALIDATED_ADAPTER",
                "L3_EXECUTION_TESTED",
            ],
            "l3_required_evidence": ["engine", "version", "site", "run_id", "artifact_sha256"],
            "forbidden_claim_phrases": [
                "DFT proves catalyst performance",
                "parser tests prove real engine execution",
                "AI-generated computational result",
                "scheduler success proves the mechanism",
                "high R2 proves causality",
            ],
        }
        capability = {
            "schema_version": "1.0",
            "release": "0.4.0-alpha.1",
            "capabilities": [
                {
                    "id": "fixture",
                    "skill": "fixture",
                    "status": "implemented",
                    "support_level": level,
                    "scripts": ["run.py"],
                    "external_requirements": [],
                }
            ],
        }
        (root / "docs" / "SCIENTIFIC_CLAIM_POLICY.yaml").write_text(
            yaml.safe_dump(policy, sort_keys=False), encoding="utf-8"
        )
        (root / "docs" / "CAPABILITY_STATUS.yaml").write_text(
            yaml.safe_dump(capability, sort_keys=False), encoding="utf-8"
        )
        for name in ("README.md", "README_EN.md"):
            (root / name).write_text(
                "L2_VALIDATED_ADAPTER and L3_EXECUTION_TESTED are distinct.\n",
                encoding="utf-8",
            )

    def test_l3_requires_immutable_execution_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.make_fixture(root, level="L3_EXECUTION_TESTED")
            failures = validator.validate(root)
            self.assertTrue(any("lacks execution_evidence" in item for item in failures), failures)

    def test_forbidden_public_claim_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.make_fixture(root, phrase="DFT proves catalyst performance")
            failures = validator.validate(root)
            self.assertTrue(any("forbidden unsupported claim" in item for item in failures), failures)


if __name__ == "__main__":
    unittest.main()

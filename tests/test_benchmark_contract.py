from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
HPC = ROOT / "skills" / "tsao-dft-hpc-provenance"
CONTRACT_PATH = HPC / "scripts" / "benchmark_contract.py"
VALIDATOR_PATH = ROOT / "scripts" / "validate_benchmark_contract.py"
IMPORTER_PATH = HPC / "scripts" / "import_benchmark_evidence.py"
TEMPLATE_PATH = HPC / "templates" / "benchmark-result.yaml"


def load_module(name: str, path: Path) -> ModuleType:
    if str(path.parent) not in sys.path:
        sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


contract = load_module("tsao_benchmark_contract_tests", CONTRACT_PATH)
validator = load_module("tsao_benchmark_contract_validator_tests", VALIDATOR_PATH)
importer = load_module("tsao_benchmark_contract_importer_tests", IMPORTER_PATH)


class BenchmarkContractTests(unittest.TestCase):
    def template(self) -> dict[str, Any]:
        loaded = yaml.safe_load(TEMPLATE_PATH.read_text(encoding="utf-8"))
        self.assertIsInstance(loaded, dict)
        return loaded

    def test_repository_has_one_authoritative_contract(self) -> None:
        report = validator.validate()
        self.assertTrue(report["ok"], report["errors"])
        self.assertEqual(report["canonical_contract"], "nested-v1.1")
        self.assertTrue(report["root_mirror_synchronized"])
        self.assertEqual(report["legacy_flat_qualification_impact"], "EXTERNAL_HOLD")
        self.assertEqual(report["unknown_or_mixed_input"], "FAIL_CLOSED")
        self.assertFalse(report["external_engine_invoked"])
        self.assertFalse(report["performance_ratio_published"])

    def test_canonical_and_legacy_nested_versions_are_explicit(self) -> None:
        current = self.template()
        canonical, direct = contract.normalize_record(current)
        self.assertEqual(direct["migration"], "none")
        self.assertEqual(canonical["schema_version"], "1.1")

        legacy = copy.deepcopy(current)
        legacy["schema_version"] = "1.0"
        migrated, report = contract.normalize_record(legacy)
        self.assertEqual(migrated, canonical)
        self.assertEqual(report["migration"], "version-only-shape-preserving")
        self.assertEqual(report["qualification_impact"], "none")
        self.assertEqual(contract.semantic_compatibility_record(canonical)["schema_version"], "1.0")

    def test_legacy_flat_requires_role_and_forces_hold(self) -> None:
        legacy = validator.legacy_flat_fixture()
        with self.assertRaisesRegex(contract.BenchmarkContractError, "explicit"):
            contract.normalize_record(legacy)

        migrated, report = contract.normalize_record(legacy, role_hint="scientific-reference")
        self.assertEqual(migrated["schema_version"], "1.1")
        self.assertEqual(migrated["role"], "scientific-reference")
        self.assertEqual(migrated["evidence_source"]["kind"], "imported-unverified")
        self.assertTrue(migrated["evidence_source"]["missing_fields"])
        self.assertFalse(migrated["scientific"]["parser_accepted"])
        self.assertEqual(report["qualification_impact"], "EXTERNAL_HOLD")

        view = contract.compute_qualification_view(migrated)
        self.assertNotEqual(view["evidence_source"], "real-engine-observation")
        self.assertTrue(view["missing_fields"])

    def test_unknown_mixed_and_nonfinite_inputs_fail_closed(self) -> None:
        current = self.template()
        unknown = copy.deepcopy(current)
        unknown["schema_version"] = "2.0"
        with self.assertRaisesRegex(contract.BenchmarkContractError, "unsupported nested"):
            contract.normalize_record(unknown)

        mixed = copy.deepcopy(current)
        mixed["wall_time_seconds"] = 1.0
        with self.assertRaisesRegex(contract.BenchmarkContractError, "mixed flat and nested"):
            contract.normalize_record(mixed)

        nonfinite = copy.deepcopy(current)
        nonfinite["performance"]["wall_time_s"] = float("inf")
        with self.assertRaisesRegex(contract.BenchmarkContractError, "non-finite"):
            contract.normalize_record(nonfinite)

    def test_formal_import_migrates_flat_only_with_explicit_role(self) -> None:
        legacy = validator.legacy_flat_fixture()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "legacy.json"
            path.write_text(json.dumps(legacy), encoding="utf-8")
            records, report = importer.import_with_schema(
                [path],
                contract.CANONICAL_SCHEMA_PATH,
                None,
                legacy_roles={"legacy-cpu-reference": "scientific-reference"},
                require_authoritative=True,
            )
        self.assertTrue(report["ok"], report["failures"])
        self.assertEqual(report["contract_mode"], "canonical-nested-v1.1")
        self.assertEqual(report["migration_counts"], {"field-mapping-with-explicit-missing-evidence": 1})
        self.assertEqual(records[0]["schema_version"], "1.1")
        self.assertEqual(records[0]["evidence_source"]["kind"], "imported-unverified")
        self.assertTrue(records[0]["evidence_source"]["missing_fields"])

        with self.assertRaisesRegex(ValueError, "authoritative"):
            importer.import_with_schema(
                [],
                contract.LEGACY_FLAT_SCHEMA_PATH,
                None,
                require_authoritative=True,
            )

    def test_authoritative_and_legacy_schema_identities_are_distinct(self) -> None:
        canonical = contract.canonical_schema()
        legacy = contract.legacy_flat_schema()
        self.assertEqual(contract.approved_schema_kind(canonical), "canonical-nested-v1.1")
        self.assertEqual(contract.approved_schema_kind(legacy), "legacy-flat-v1.0")
        self.assertNotEqual(canonical["$id"], legacy["$id"])
        self.assertEqual(
            contract.ROOT_SCHEMA_MIRROR_PATH.read_text(encoding="utf-8"),
            contract.CANONICAL_SCHEMA_PATH.read_text(encoding="utf-8"),
        )


if __name__ == "__main__":
    unittest.main()

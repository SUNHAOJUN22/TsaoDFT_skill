"""Required quantities must be observed before any median or signed qualification."""

from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def load(relative: str, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RequiredObservableEvidenceTests(unittest.TestCase):
    support: Any
    review_support: Any

    @classmethod
    def setUpClass(cls) -> None:
        support = load("tests/test_performance_evidence.py", "required_observable_support")
        support.PerformanceEvidenceTests.setUpClass()
        cls.support = support.PerformanceEvidenceTests
        trust_support = load("tests/test_evidence_trust_boundary.py", "required_observable_trust_support")
        trust_support.EvidenceTrustBoundaryTests.setUpClass()
        cls.review_support = trust_support.EvidenceTrustBoundaryTests

    def setUp(self) -> None:
        self.fixture = self.support(methodName="test_valid_cpu_reference")
        self.fixture.setUp()
        self.core = self.fixture.core
        self.policy = self.fixture.policy
        self.root = self.fixture.artifact_root

    def tearDown(self) -> None:
        self.fixture.tearDown()

    def records(self) -> list[dict[str, Any]]:
        records = [*self.fixture.reference_records(), *self.fixture.gpu_records()]
        for record in records:
            record["schema_version"] = "1.1"
            record["benchmark_plan_id"] = "PLAN-A"
            record["scientific"]["observable_set"] = ["energy", "forces", "stress", "band_gap_ev"]
            record["scientific"]["results"]["stress_gpa"] = [0.0] * 6
        return records

    def test_all_declared_quantities_missing_cannot_qualify(self) -> None:
        records = self.records()
        for record in records:
            record["scientific"]["results"] = {
                "energy_ev": None,
                "forces_ev_per_angstrom": None,
                "stress_gpa": None,
                "properties": {},
            }
        validated = [self.core.validate_result(record, self.root) for record in records]
        self.assertTrue(all(errors for _, errors, _ in validated), validated)
        summary = self.core.compare_evidence([value[0] for value in validated], self.policy)
        self.assertIsNone(summary["candidates"]["gpu-1"]["cpu_to_candidate_speedup"])

    def test_failed_attempt_preserves_missing_data_without_becoming_eligible(self) -> None:
        record = self.records()[0]
        record["scientific"]["parser_accepted"] = False
        record["scientific"]["parser_status"] = "REJECTED"
        record["scientific"]["results"]["energy_ev"] = None
        normalized, errors, _ = self.core.validate_result(record, self.root)
        self.assertEqual(errors, [])
        self.assertFalse(self.core.eligible_success(normalized))

    def test_direct_comparison_rejects_each_missing_reference_before_aggregation(self) -> None:
        records = self.records()
        for field in ("energy_ev", "forces_ev_per_angstrom", "stress_gpa", "band_gap_ev"):
            with self.subTest(field=field):
                damaged = copy.deepcopy(records)
                results = damaged[0]["scientific"]["results"]
                if field == "band_gap_ev":
                    results["properties"].pop(field)
                else:
                    results[field] = None
                gate = self.core.numerical_equivalence(damaged[3:], damaged[:3], self.policy)
                self.assertEqual(gate["status"], "FAIL", gate)

    def test_required_vector_shapes_are_not_empty_or_scalar(self) -> None:
        for field, value in (
            ("forces_ev_per_angstrom", []),
            ("forces_ev_per_angstrom", [0.0, 0.0]),
            ("stress_gpa", []),
            ("stress_gpa", [0.0]),
        ):
            with self.subTest(field=field, value=value):
                record = self.records()[0]
                record["scientific"]["results"][field] = value
                _, errors, _ = self.core.validate_result(record, self.root)
                self.assertTrue(errors)

    def test_optional_absence_is_not_a_zero_deviation(self) -> None:
        records = self.records()
        for record in records:
            record["scientific"]["observable_set"] = ["energy"]
            record["scientific"]["results"]["forces_ev_per_angstrom"] = None
            record["scientific"]["results"]["stress_gpa"] = None
            record["scientific"]["results"]["properties"] = {}
        validated = self.fixture.validated(records)
        gate = self.core.numerical_equivalence(validated[3:], validated[:3], self.policy)
        self.assertEqual(gate["status"], "PASS")
        self.assertEqual(gate["maximum_deviations"]["energy_abs_ev"], 0.0)
        self.assertIsNone(gate["maximum_deviations"]["force_max_abs_ev_per_angstrom"])
        self.assertIsNone(gate["maximum_deviations"]["stress_max_abs_gpa"])

    def test_scf_summary_reports_known_and_unknown_counts_without_zero_imputation(self) -> None:
        records = self.records()
        records[3]["performance"]["scf_iterations"] = None
        validated = self.fixture.validated(records)
        summary = self.core.compare_evidence(validated, self.policy)["candidates"]["gpu-1"]
        self.assertEqual(summary["eligible_successful_runs"], 3)
        self.assertEqual(summary["scf_iterations"]["count"], 2)
        self.assertEqual(summary["scf_iterations"]["unknown_count"], 1)
        self.assertEqual(summary["scf_iterations"]["median"], 12)

    def signed_cli(self, records: list[dict[str, Any]]) -> subprocess.CompletedProcess[str]:
        importer = load("scripts/import_benchmark_evidence.py", "required_observable_import")
        trust_fixture = self.review_support(methodName="test_signed_review_is_bound_and_forgery_rejected")
        input_path = self.root / "records.json"
        input_path.write_text(json.dumps(records), encoding="utf-8")
        schema = ROOT / "templates/benchmark-result.schema.json"
        normalized, _ = importer.import_with_schema([input_path], schema, self.root, require_authoritative=True)
        summary = self.core.compare_evidence(normalized, self.policy)
        summary["benchmark_plan_id"] = "PLAN-A"
        payload = trust_fixture.trust.prequalification_payload(normalized, summary, self.policy)
        digest = trust_fixture.trust.sha256_bytes(trust_fixture.shell.canonical_json(payload).encode())
        review, public = trust_fixture.signed_review(digest, payload["candidate_ids"])
        review_path, key_path = self.root / "review.json", self.root / "review.pem"
        review_path.write_text(json.dumps(review), encoding="utf-8")
        key_path.write_bytes(public)
        return subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/qualify_performance_evidence.py"),
                str(input_path),
                "--result-schema",
                str(schema),
                "--policy",
                str(ROOT / "templates/performance-qualification-policy.yaml"),
                "--policy-schema",
                str(ROOT / "templates/performance-qualification-policy.schema.json"),
                "--artifact-root",
                str(self.root),
                "--review",
                str(review_path),
                "--review-public-key",
                str(key_path),
                "--out-parent",
                str(self.root / "published"),
            ],
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )

    def test_formal_signed_cli_cannot_qualify_absent_required_evidence(self) -> None:
        records = self.records()
        for record in records:
            record["scientific"]["results"] = {
                "energy_ev": None,
                "forces_ev_per_angstrom": None,
                "stress_gpa": None,
                "properties": {},
            }
        process = self.signed_cli(records)
        self.assertNotEqual(process.returncode, 0, process.stdout + process.stderr)

    def test_formal_signed_cli_preserves_positive_control(self) -> None:
        process = self.signed_cli(self.records())
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        result = json.loads(process.stdout)
        self.assertEqual(result["qualification"]["qualified_candidates"], ["gpu-1"])
        self.assertFalse(result["qualification"]["public_capability_level_changed"])

    def test_formal_signed_cli_keeps_energy_mismatch_unqualified(self) -> None:
        records = self.records()
        for record in records[3:]:
            record["scientific"]["results"]["energy_ev"] = -9.0
        process = self.signed_cli(records)
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        qualification = json.loads(process.stdout)["qualification"]
        self.assertEqual(qualification["qualified_candidates"], [])
        self.assertEqual(qualification["candidates"]["gpu-1"]["status"], "NUMERICAL_MISMATCH")


if __name__ == "__main__":
    unittest.main()

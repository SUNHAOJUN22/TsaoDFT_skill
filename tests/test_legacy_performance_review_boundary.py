"""Synthetic software fixtures distinguish prechecks from signed qualification."""

from __future__ import annotations

import base64
import copy
import importlib.util
import json
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path(__file__).resolve().parents[1] / "skills/tsao-dft-hpc-provenance"


def load(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def evidence():
    support = load(ROOT / "tests/test_performance_evidence.py", "legacy_review_fixture")
    support.PerformanceEvidenceTests.setUpClass()
    fixture = support.PerformanceEvidenceTests(methodName="test_valid_cpu_reference")
    fixture.setUp()
    try:
        records = fixture.validated([*fixture.reference_records(), *fixture.gpu_records()])
        yield fixture, records, fixture.core.compare_evidence(records, fixture.policy)
    finally:
        fixture.tearDown()


@pytest.mark.parametrize("review_required", [True, False])
@pytest.mark.parametrize("review", [{}, {"status": "approved"}, {"status": "approved", "signature": "claimed"}])
def test_legacy_precheck_never_promotes_unsigned_review(evidence, review_required: bool, review: dict) -> None:
    fixture, _, summary = evidence
    policy = copy.deepcopy(fixture.policy)
    policy["require_independent_review"] = review_required
    report = fixture.core.qualify_evidence(summary, policy, review, "a" * 64)
    assert report["qualified_candidates"] == []
    assert report["candidates"]["gpu-1"]["status"] == "L2_ONLY"
    assert any("qualify_performance_evidence.py" in reason for reason in report["candidates"]["gpu-1"]["reasons"])


def test_legacy_bundle_retains_statistics_without_signed_qualification(evidence, tmp_path: Path) -> None:
    fixture, records, summary = evidence
    bundle = fixture.core.write_evidence_bundle(tmp_path, records, summary, fixture.policy, {"status": "approved"})
    assert bundle["ok"] is True
    assert bundle["qualification"]["qualified_candidates"] == []
    written = json.loads((tmp_path / "qualification-report.json").read_text(encoding="utf-8"))
    assert written["candidates"]["gpu-1"]["status"] == "L2_ONLY"
    persisted = json.loads((tmp_path / "benchmark-summary.json").read_text(encoding="utf-8"))
    assert persisted["candidates"]["gpu-1"]["cpu_to_candidate_speedup"] == 2.0


@pytest.mark.parametrize("review_case", ["valid", "wrong_candidates", "expired"])
def test_formal_cli_still_requires_and_accepts_bound_signatures(evidence, tmp_path: Path, review_case: str) -> None:
    fixture, records, _ = evidence
    formal = load(ROOT / "scripts/qualify_performance_evidence.py", "legacy_review_formal")
    records_path = tmp_path / "records.json"
    exported = [{key: value for key, value in record.items() if key != "validation"} for record in records]
    records_path.write_text(json.dumps(exported), encoding="utf-8")
    imported, report = formal.import_with_schema(
        [records_path],
        ROOT / "templates/benchmark-result.schema.json",
        fixture.artifact_root,
        require_authoritative=True,
    )
    assert report["ok"], report
    summary = formal.compare_evidence(imported, fixture.policy)
    summary["benchmark_plan_id"] = "PLAN-001"
    payload = formal.prequalification_payload(imported, summary, fixture.policy)
    digest = formal.sha256_bytes(formal.canonical_json(payload).encode("utf-8"))
    key = Ed25519PrivateKey.generate()
    public = key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
    shell = load(ROOT / "scripts/shell_contract.py", "legacy_review_shell")
    now = datetime.now(UTC)
    review = {
        "schema_version": "1.0",
        "attestation_id": "SYNTHETIC-REVIEW",
        "identity": "test-reviewer@example.invalid",
        "decision": "approved",
        "scope": "scoped-performance-evidence",
        "issued_at": (now - timedelta(hours=2)).isoformat(),
        "expires_at": (now + timedelta(hours=1) if review_case != "expired" else now - timedelta(hours=1)).isoformat(),
        "binding": {
            "policy_id": fixture.policy["policy_id"],
            "benchmark_plan_id": "PLAN-001",
            "candidate_ids": ["gpu-2"] if review_case == "wrong_candidates" else ["gpu-1"],
            "evidence_root_sha256": digest,
        },
        "signature_algorithm": "ed25519",
        "key_fingerprint": shell.public_key_fingerprint(public),
    }
    review["signature"] = base64.b64encode(key.sign(formal.canonical_json(review).encode("utf-8"))).decode("ascii")
    review_path = tmp_path / "review.json"
    review_path.write_text(json.dumps(review), encoding="utf-8")
    public_path = tmp_path / "review.pem"
    public_path.write_bytes(public)
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/qualify_performance_evidence.py"),
            str(records_path),
            "--result-schema",
            str(ROOT / "templates/benchmark-result.schema.json"),
            "--policy",
            str(ROOT / "templates/performance-qualification-policy.yaml"),
            "--policy-schema",
            str(ROOT / "templates/performance-qualification-policy.schema.json"),
            "--artifact-root",
            str(fixture.artifact_root),
            "--review",
            str(review_path),
            "--review-public-key",
            str(public_path),
            "--out-parent",
            str(tmp_path / "published"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    qualification = json.loads(result.stdout)["qualification"]
    assert qualification["qualified_candidates"] == (["gpu-1"] if review_case == "valid" else [])
    assert bool(qualification["review_verification_errors"]) is (review_case != "valid")
    assert qualification["public_capability_level_changed"] is False

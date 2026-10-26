"""Synthetic signed-manifest retargeting probes; generated commands are never run."""

from __future__ import annotations

import base64
import copy
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
import yaml
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

SKILL = Path(__file__).parents[1] / "skills/tsao-dft-hpc-provenance"
sys.path.insert(0, str(SKILL / "scripts"))
import shell_contract as shell  # noqa: E402 -- needs the standalone Skill path above
from validate_hpc_manifest import validate  # noqa: E402 -- needs the standalone Skill path above


@pytest.fixture
def signed_manifest(tmp_path: Path):
    manifest = yaml.safe_load((SKILL / "templates/hpc-manifest.yaml").read_text())
    manifest.update(approval="approved", approval_public_key="review-key.pem")
    private = Ed25519PrivateKey.generate()
    public = private.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    (tmp_path / "review-key.pem").write_bytes(public)
    now = datetime.now(UTC)
    attestation = {
        "schema_version": "1.0",
        "attestation_id": "SYNTHETIC-MANIFEST-REVIEW",
        "identity": "test-reviewer",
        "decision": "approved",
        "scope": "execute-reviewed-manifest",
        "issued_at": (now - timedelta(minutes=1)).isoformat(),
        "expires_at": (now + timedelta(hours=1)).isoformat(),
        "binding": {
            "manifest_sha256": shell.manifest_sha256(manifest),
            "benchmark_plan_id": None,
            "candidate_id": manifest["job_id"],
            "method_fingerprint_digest": shell.sha256_object(
                {"method_fingerprint_id": manifest["method_fingerprint_id"]}
            ),
        },
        "signature_algorithm": "ed25519",
        "key_fingerprint": shell.public_key_fingerprint(public),
    }
    attestation["signature"] = base64.b64encode(private.sign(shell.canonical_json(attestation).encode())).decode()
    manifest["approval_attestation"] = attestation
    return manifest, private


def test_full_review_positive_control_and_order_independence(signed_manifest, tmp_path: Path) -> None:
    manifest, _ = signed_manifest
    assert validate(manifest, approval_root=tmp_path)[0] == []
    payload = shell.manifest_binding_payload(manifest)
    assert payload["contract"] == "tsao.execution-manifest-review.v2"
    assert payload["manifest"] == {key: value for key, value in manifest.items() if key != "approval_attestation"}
    assert shell.manifest_sha256(dict(reversed(list(manifest.items())))) == shell.manifest_sha256(manifest)


@pytest.mark.parametrize(
    "field,value",
    [
        ("executable", "alternate_engine"),
        ("launcher", {"argv": ["env", "SYNTHETIC_AUDIT_MARKER=1"]}),
        ("stdout", "changed-output.log"),
        ("stderr", "changed-error.log"),
        ("scratch", {"path": "changed-scratch", "preserve_on_failure": True}),
        ("checkpoint_policy", "discard"),
        ("support_level", "L1_HANDOFF"),
        ("schema_version", "2.0"),
        ("estimated_storage_gb", 8),
        ("future_execution_option", {"nested": [True, 1, 0.5, "reviewed", None]}),
        ("environment", {"modules": ["different-engine"], "source": [], "variables": {}}),
    ],
)
def test_original_signature_cannot_authorize_changed_execution_object(
    signed_manifest, tmp_path: Path, field, value
) -> None:
    original, _ = signed_manifest
    changed = copy.deepcopy(original)
    changed[field] = value
    assert shell.manifest_sha256(changed) != shell.manifest_sha256(original)
    assert "attestation binding mismatch: manifest_sha256" in validate(changed, approval_root=tmp_path)[0]


def test_retargeting_digest_without_new_signature_is_rejected(signed_manifest, tmp_path: Path) -> None:
    manifest, _ = signed_manifest
    manifest["executable"] = "alternate_engine"
    manifest["approval_attestation"]["binding"]["manifest_sha256"] = shell.manifest_sha256(manifest)
    assert any("signature verification failed" in error for error in validate(manifest, approval_root=tmp_path)[0])


def test_old_selected_field_digest_requires_fresh_full_review(signed_manifest, tmp_path: Path) -> None:
    manifest, private = signed_manifest
    old_fields = (
        "job_id",
        "engine",
        "engine_version",
        "method_fingerprint_id",
        "input",
        "workdir",
        "scheduler",
        "resources",
        "environment",
        "acceleration",
        "preflight",
        "parser",
        "expected_outputs",
    )
    attestation = manifest["approval_attestation"]
    attestation["binding"]["manifest_sha256"] = shell.sha256_object({key: manifest.get(key) for key in old_fields})
    unsigned = {key: value for key, value in attestation.items() if key != "signature"}
    attestation["signature"] = base64.b64encode(private.sign(shell.canonical_json(unsigned).encode())).decode()
    assert "attestation binding mismatch: manifest_sha256" in validate(manifest, approval_root=tmp_path)[0]


@pytest.mark.parametrize("value", [float("nan"), float("inf"), {1: "ambiguous-key"}, (1, 2)])
def test_full_manifest_identity_rejects_noncanonical_json(signed_manifest, tmp_path: Path, value) -> None:
    manifest, _ = signed_manifest
    manifest["extension"] = value
    with pytest.raises(ValueError, match="manifest"):
        shell.manifest_sha256(manifest)
    assert any("invalid manifest binding" in error for error in validate(manifest, approval_root=tmp_path)[0])


def test_attestation_itself_is_excluded_to_avoid_a_digest_cycle(signed_manifest) -> None:
    manifest, _ = signed_manifest
    digest = shell.manifest_sha256(manifest)
    del manifest["approval_attestation"]
    assert shell.manifest_sha256(manifest) == digest
    manifest["approval_public_key"] = "different-key.pem"
    assert shell.manifest_sha256(manifest) != digest

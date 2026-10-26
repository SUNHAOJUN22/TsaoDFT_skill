from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest

MODULE = Path(__file__).parents[1] / "skills/tsao-dft-hpc-provenance/scripts/model_acceptance_v5.py"
spec = importlib.util.spec_from_file_location("model_acceptance_v5", MODULE)
assert spec and spec.loader
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)

KEY = b"independent-model-approval-key-32bytes"
DATASET_KEY = b"independent-dataset-validation-key-32bytes"
NOW = datetime(2026, 8, 12, 10, tzinfo=UTC)


def artifact():
    value = m.DatasetValidationArtifact(
        "DVA-1",
        "a" * 64,
        "b" * 64,
        "c" * 64,
        "d" * 64,
        100,
        "energy",
        "eV",
        "DFT-PBE",
        "PASS",
        "independent-dataset-validator",
        "2026-08-12T09:00:00Z",
        "",
    )
    return replace(value, signature=m.sign_approval(value.unsigned(), DATASET_KEY))


def card(**updates):
    value = m.ModelCard(
        "M-1",
        "a" * 64,
        "e" * 64,
        "f" * 64,
        "1" * 64,
        "b" * 64,
        {"descriptor_bounds": [-1, 1]},
        {"type": "calibrated_conformal", "coverage": 0.9},
        {"mae": 0.1, "coverage": 0.9},
        "trainer-person",
    )
    return replace(value, **updates)


def approval(approver="reviewer-person"):
    value = m.ModelApproval(
        "A-1",
        "e" * 64,
        "a" * 64,
        "predictive-dft-model",
        "tsao-dft",
        approver,
        "independent_model_validator",
        "2026-08-12T09:00:00Z",
        "2026-08-12T11:00:00Z",
        "nonce-1",
        "key-1",
        "",
        dataset_validation_sha256=hashlib.sha256(
            json.dumps(artifact().unsigned(), sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        model_card_sha256=card().digest(),
    )
    return replace(value, signature=m.sign_approval(value.unsigned(), KEY))


def assess(c, a):
    return m.assess_model_card(
        c,
        dataset_artifact=artifact(),
        expected_schema_sha256="b" * 64,
        approval=a,
        key_resolver=lambda key_id: KEY if key_id == "key-1" else None,
        dataset_key_resolver=lambda issuer: DATASET_KEY if issuer == "independent-dataset-validator" else None,
        now=NOW,
    )


def test_complete_independent_chain_can_be_accepted() -> None:
    result = assess(card(), approval())
    assert result == {"status": "ACCEPTED", "accepted": True, "blockers": []}


def test_trainer_cannot_self_approve() -> None:
    result = assess(card(), approval("trainer-person"))
    assert result["accepted"] is False
    assert "TRAINER_CANNOT_SELF_APPROVE" in result["blockers"]


@pytest.mark.parametrize(
    ("field", "blocker"),
    [
        ("applicability_domain", "APPLICABILITY_DOMAIN_MISSING"),
        ("uncertainty_model", "CALIBRATED_UNCERTAINTY_MISSING"),
        ("holdout_metrics", "HOLDOUT_VALIDATION_MISSING"),
    ],
)
def test_missing_acceptance_components_remain_nonaccepted(field: str, blocker: str) -> None:
    result = assess(card(**{field: None}), approval())
    assert result["accepted"] is False
    assert blocker in result["blockers"]


def test_no_approval_is_not_accepted() -> None:
    result = assess(card(), None)
    assert result["accepted"] is False
    assert "INDEPENDENT_APPROVAL_MISSING" in result["blockers"]


def test_dataset_checksum_change_blocks_training_chain() -> None:
    with pytest.raises(m.ModelAcceptanceError, match="dataset SHA"):
        m.assess_model_card(
            card(dataset_sha256="9" * 64), dataset_artifact=artifact(), expected_schema_sha256="b" * 64, approval=None
        )


def test_nonfinite_holdout_metric_fails_closed() -> None:
    with pytest.raises(m.ModelAcceptanceError, match="finite"):
        assess(card(holdout_metrics={"mae": float("nan")}), approval())


def test_tampered_approval_signature_fails_closed() -> None:
    with pytest.raises(m.ModelAcceptanceError, match="signature"):
        assess(card(), replace(approval(), signature="0" * 64))

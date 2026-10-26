"""Model approval flags require authenticated, exact artifact bindings."""

from __future__ import annotations

import importlib.util
import sys
from dataclasses import asdict, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

SCRIPTS = Path(__file__).parents[1] / "skills/tsao-dft-hpc-provenance/scripts"
spec = importlib.util.spec_from_file_location(
    "model_validation_trust_core", SCRIPTS / "scientific_contracts_core_v18.py"
)
assert spec and spec.loader
core = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = core
spec.loader.exec_module(core)

APPROVAL_KEY = b"synthetic-model-review-key-32-bytes"
DATASET_KEY = b"synthetic-dataset-review-key-32-bytes"
NOW = datetime(2026, 10, 25, 12, tzinfo=UTC)


def dataset() -> Any:
    return core.DatasetValidationArtifact(
        "validation-1",
        "a" * 64,
        "b" * 64,
        "c" * 64,
        "d" * 64,
        100,
        "energy",
        "eV",
        "DFT-PBE",
        "PASS",
        "dataset-reviewer",
        "2026-10-25T10:00:00Z",
        "",
    )


def card(*, legacy_schema: bool = False) -> Any:
    return core.ModelCard(
        "model-1",
        "a" * 64,
        "e" * 64,
        "f" * 64,
        "1" * 64,
        ("d" if legacy_schema else "b") * 64,
        {"descriptor_bounds": [-1, 1]},
        {"method": "conformal", "coverage": 0.9},
        {"mae": 0.1},
        "trainer",
    )


def approval(*, legacy_model: bool = False, binding: str | None = None) -> Any:
    kwargs = {} if binding is None else {"dataset_validation_sha256": binding, "model_card_sha256": card().digest()}
    value = core.ModelApproval(
        "approval-1",
        ("1" if legacy_model else "e") * 64,
        "a" * 64,
        "predictive-dft-model",
        "tsao-dft",
        "model-reviewer",
        "independent_model_validator",
        "2026-10-25T11:00:00Z",
        "2026-10-26T11:00:00Z",
        "nonce-1",
        "model-key",
        "",
        **kwargs,
    )
    return replace(value, signature=core.sign_approval(value.unsigned(), APPROVAL_KEY))


def assess(model: Any, validation: Any, review: Any, *, dataset_trust: bool = False) -> dict[str, Any]:
    kwargs = (
        {"dataset_key_resolver": lambda issuer: DATASET_KEY if issuer == "dataset-reviewer" else None}
        if dataset_trust
        else {}
    )
    return core.assess_model_card(
        model,
        dataset_artifact=validation,
        approval=review,
        expected_schema_sha256="b" * 64,
        key_resolver=lambda key: APPROVAL_KEY if key == "model-key" else None,
        now=NOW,
        **kwargs,
    )


def mapping() -> dict[str, Any]:
    return {
        "status": "ACCEPTED",
        "dataset_sha256": "a" * 64,
        "model_sha256": "e" * 64,
        "code_sha256": "f" * 64,
        "environment_sha256": "1" * 64,
        "trainer_identity": "trainer",
        "applicability_domain": {"bounds": [-1, 1]},
        "calibrated_uncertainty": {"coverage": 0.9},
        "holdout_validation": {"mae": 0.1},
        "independent_approval": {
            "issuer": "reviewer",
            "model_sha256": "e" * 64,
            "role": "qualified-scientist",
            "scope": "predictive-model-use",
            "signature": "unverified-string",
            "issued_at": "2026-10-25T11:00:00Z",
            "expires_at": "2026-10-26T11:00:00Z",
        },
    }


def test_unverified_mapping_cannot_allow_predictive_use() -> None:
    result = core.validate_predictive_model_card(mapping(), now=NOW.isoformat())
    assert result["predictive_use_allowed"] is False
    assert result["structure_valid"] is True
    assert result["status"] == "HOLD"
    assert "APPROVAL_UNVERIFIED" in result["blockers"]


@pytest.mark.parametrize("defect", ["issuer", "status"])
def test_mapping_requires_meaningful_issuer_and_accepted_status(defect: str) -> None:
    value = mapping()
    if defect == "issuer":
        value["independent_approval"].pop("issuer")
    else:
        value["status"] = "REJECTED"
    with pytest.raises(core.ModelAcceptanceError):
        core.validate_predictive_model_card(value, now=NOW.isoformat())


def test_legacy_unsigned_dataset_is_not_an_authenticated_chain() -> None:
    # The old implementation confused schema with split and model with environment.
    # Even its historically accepted shape must never authorize unsigned validation.
    try:
        result = assess(card(legacy_schema=True), dataset(), approval(legacy_model=True))
    except core.ModelAcceptanceError:
        return
    assert result["accepted"] is False


def test_correct_model_and_schema_hashes_are_bound_to_the_named_fields() -> None:
    result = assess(card(), dataset(), approval())
    assert result["status"] == "HOLD"
    assert "APPROVAL_BINDING_MISMATCH" not in result["blockers"]


def signed_dataset() -> Any:
    value = dataset()
    return replace(value, signature=core.sign_approval(value.unsigned(), DATASET_KEY))


def test_authenticated_dataset_and_exact_approval_can_be_accepted() -> None:
    validation = signed_dataset()
    review = approval(binding=core.digest_mapping(validation.unsigned()))
    assert assess(card(), validation, review, dataset_trust=True)["accepted"] is True


@pytest.mark.parametrize("field,value", [("sample_count", 101), ("unit", "hartree"), ("validator_sha256", "9" * 64)])
def test_any_tampered_dataset_contract_field_rejects_signature(field: str, value: object) -> None:
    validation = signed_dataset()
    review = approval(binding=core.digest_mapping(validation.unsigned()))
    with pytest.raises(core.ModelAcceptanceError, match=r"dataset.*signature"):
        assess(card(), replace(validation, **{field: value}), review, dataset_trust=True)


def test_resigned_validation_still_requires_new_approval_binding() -> None:
    validation = signed_dataset()
    review = approval(binding=core.digest_mapping(validation.unsigned()))
    replacement = replace(validation, sample_count=101, signature="")
    replacement = replace(replacement, signature=core.sign_approval(replacement.unsigned(), DATASET_KEY))
    result = assess(card(), replacement, review, dataset_trust=True)
    assert result["accepted"] is False
    assert "DATASET_VALIDATION_BINDING_MISMATCH" in result["blockers"]


def test_missing_dataset_trust_and_missing_binding_remain_hold() -> None:
    validation = signed_dataset()
    bound = approval(binding=core.digest_mapping(validation.unsigned()))
    assert assess(card(), validation, bound)["accepted"] is False
    result = assess(card(), validation, approval(), dataset_trust=True)
    assert result["accepted"] is False
    assert "DATASET_VALIDATION_BINDING_MISSING" in result["blockers"]


def test_unsigned_payload_covers_every_validation_field_and_legacy_approval_stays_serializable() -> None:
    validation = dataset()
    expected = asdict(validation)
    expected.pop("signature")
    assert validation.unsigned() == expected
    assert "dataset_validation_sha256" not in approval().unsigned()


def test_future_issued_dataset_is_not_current_evidence() -> None:
    validation = replace(dataset(), issued_at="2026-10-26T10:00:00Z")
    validation = replace(validation, signature=core.sign_approval(validation.unsigned(), DATASET_KEY))
    review = approval(binding=core.digest_mapping(validation.unsigned()))
    assert assess(card(), validation, review, dataset_trust=True)["accepted"] is False

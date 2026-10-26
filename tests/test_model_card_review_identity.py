"""Signed model reviews bind the entire predictive-use contract, not just weights."""

from __future__ import annotations

import hashlib
import hmac
import importlib.util
import json
import sys
from dataclasses import asdict, replace
from datetime import UTC, datetime
from pathlib import Path
from types import MappingProxyType
from typing import Any

import pytest

SCRIPTS = Path(__file__).parents[1] / "skills/tsao-dft-hpc-provenance/scripts"
spec = importlib.util.spec_from_file_location("model_card_review_public", SCRIPTS / "model_acceptance_v5.py")
assert spec and spec.loader
api = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = api
spec.loader.exec_module(api)

MODEL_KEY = b"synthetic-independent-model-review-key"
DATASET_KEY = b"synthetic-independent-dataset-review-key"
NOW = datetime(2026, 10, 25, 12, tzinfo=UTC)


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode()


def independent_signature(payload: dict[str, object], key: bytes) -> str:
    return hmac.new(key, canonical(payload), hashlib.sha256).hexdigest()


def validation() -> Any:
    value = api.DatasetValidationArtifact(
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
    unsigned = asdict(value)
    unsigned.pop("signature")
    return replace(value, signature=independent_signature(unsigned, DATASET_KEY))


def model() -> Any:
    return api.ModelCard(
        "model-1",
        "a" * 64,
        "e" * 64,
        "f" * 64,
        "1" * 64,
        "b" * 64,
        {"descriptor_bounds": [-1, 1], "purpose": "screening", "label": "聚合物"},
        {"method": "conformal", "coverage": 0.9},
        {"mae": 0.1},
        "trainer",
    )


def independent_card_digest(card: Any) -> str:
    return hashlib.sha256(canonical({"contract": "tsao.dft.model-card-review.v1", "card": asdict(card)})).hexdigest()


def review(card: Any, *, legacy: bool = False) -> Any:
    validated = validation()
    unsigned_validation = asdict(validated)
    unsigned_validation.pop("signature")
    bindings: dict[str, object] = {
        "dataset_validation_sha256": hashlib.sha256(canonical(unsigned_validation)).hexdigest()
    }
    if not legacy:
        bindings["model_card_sha256"] = independent_card_digest(card)
    value = api.ModelApproval(
        "review-1",
        card.model_sha256,
        card.dataset_sha256,
        "predictive-dft-model",
        "tsao-dft",
        "independent-reviewer",
        "independent_model_validator",
        "2026-10-25T11:00:00Z",
        "2026-10-26T11:00:00Z",
        "nonce-1",
        "model-key",
        "",
        **bindings,
    )
    return replace(value, signature=independent_signature(value.unsigned(), MODEL_KEY))


def assess(card: Any, approval: Any, **kwargs: Any) -> dict[str, Any]:
    return api.assess_model_card(
        card,
        dataset_artifact=validation(),
        expected_schema_sha256="b" * 64,
        approval=approval,
        key_resolver=lambda key: MODEL_KEY if key == "model-key" else None,
        dataset_key_resolver=lambda issuer: DATASET_KEY if issuer == "dataset-reviewer" else None,
        now=NOW,
        **kwargs,
    )


def test_legacy_approval_cannot_authorize_an_unbound_model_card() -> None:
    card = model()
    approval = review(card, legacy=True)
    result = assess(card, approval)
    assert result["accepted"] is False
    assert "MODEL_CARD_BINDING_MISSING" in result["blockers"]


def test_independently_signed_full_card_chain_and_digest() -> None:
    card = model()
    assert card.digest() == independent_card_digest(card)
    approval = review(card)
    assert approval.unsigned()["model_card_sha256"] == independent_card_digest(card)
    assert assess(card, approval) == {"status": "ACCEPTED", "accepted": True, "blockers": []}


@pytest.mark.parametrize(
    "field,value",
    [
        ("model_id", "another-model"),
        ("code_sha256", "9" * 64),
        ("environment_sha256", "8" * 64),
        ("applicability_domain", {"descriptor_bounds": [-1e100, 1e100], "purpose": "industrial-release"}),
        ("uncertainty_model", {"method": "unreviewed", "coverage": 1.0}),
        ("holdout_metrics", {"mae": 0.0}),
        ("trainer_identity", "another-trainer"),
    ],
)
def test_same_valid_signature_cannot_retarget_reviewed_content(field: str, value: object) -> None:
    original = model()
    changed = replace(original, **{field: value})
    result = assess(changed, review(original))
    assert result["accepted"] is False
    assert "MODEL_CARD_BINDING_MISMATCH" in result["blockers"]
    # An independent reviewer can issue a new, appropriately bound review. Its
    # acceptance remains an authorization-contract result, not model validation.
    assert assess(changed, review(changed))["accepted"] is True


@pytest.mark.parametrize("field", ["dataset_sha256", "schema_sha256", "model_sha256"])
def test_all_hash_identities_are_part_of_the_card_digest(field: str) -> None:
    original = model()
    changed = replace(original, **{field: "7" * 64})
    assert original.digest() != changed.digest()
    if field == "model_sha256":
        result = assess(changed, review(original))
        assert {"MODEL_CARD_BINDING_MISMATCH", "APPROVAL_BINDING_MISMATCH"} <= set(result["blockers"])
    else:
        with pytest.raises(api.ModelAcceptanceError, match=r"dataset SHA|schema SHA"):
            assess(changed, review(original))


def test_retargeting_only_the_digest_does_not_reauthenticate_a_signature() -> None:
    original = model()
    changed = replace(original, code_sha256="9" * 64)
    retargeted = replace(review(original), model_card_sha256=independent_card_digest(changed))
    with pytest.raises(api.ModelAcceptanceError, match="approval signature"):
        assess(changed, retargeted)


@pytest.mark.parametrize("field,value", [("scope", "industrial-release"), ("audience", "another-service")])
def test_freshly_signed_review_cannot_change_the_authorized_use(field: str, value: str) -> None:
    card = model()
    changed = replace(review(card), **{field: value}, signature="")
    changed = replace(changed, signature=independent_signature(changed.unsigned(), MODEL_KEY))
    result = assess(card, changed)
    assert result["accepted"] is False
    assert "APPROVAL_SCOPE_MISMATCH" in result["blockers"]


def test_nested_mutation_after_review_requires_new_approval() -> None:
    card = model()
    approval = review(card)
    card.applicability_domain["descriptor_bounds"][1] = 50
    assert assess(card, approval)["blockers"] == ["MODEL_CARD_BINDING_MISMATCH"]


def test_mapping_order_and_supported_mapping_views_preserve_identity() -> None:
    card = model()
    reordered = replace(card, applicability_domain=dict(reversed(list(card.applicability_domain.items()))))
    assert reordered.digest() == card.digest()
    assert assess(reordered, review(card))["accepted"] is True
    viewed = replace(card, applicability_domain=MappingProxyType(dict(card.applicability_domain)))
    assert viewed.digest() == card.digest()
    assert assess(viewed, review(card))["accepted"] is True


@pytest.mark.parametrize("bad", [{1: "not-a-JSON-key"}, {"bound": float("inf")}, {"unsupported": object()}])
def test_unserializable_or_ambiguous_review_content_is_rejected(bad: object) -> None:
    card = replace(model(), applicability_domain=bad)
    with pytest.raises(api.ModelAcceptanceError, match=r"model card|finite|JSON"):
        card.digest()


def test_legacy_approval_unsigned_bytes_remain_compatible() -> None:
    approval = review(model(), legacy=True)
    expected = asdict(approval)
    expected.pop("signature")
    expected.pop("model_card_sha256")
    assert approval.unsigned() == expected
    assert approval.signature == independent_signature(expected, MODEL_KEY)


def test_missing_trusted_model_key_keeps_a_bound_review_unaccepted() -> None:
    card = model()
    result = api.assess_model_card(
        card,
        dataset_artifact=validation(),
        expected_schema_sha256="b" * 64,
        approval=review(card),
        dataset_key_resolver=lambda _: DATASET_KEY,
        now=NOW,
    )
    assert result["accepted"] is False
    assert "APPROVAL_KEY_UNAVAILABLE" in result["blockers"]

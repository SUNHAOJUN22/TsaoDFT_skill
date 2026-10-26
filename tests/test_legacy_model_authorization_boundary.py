"""Old public model interfaces cannot authenticate their own approval claims."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).parents[1] / "skills/tsao-dft-hpc-provenance/scripts"


def load(name):
    spec = importlib.util.spec_from_file_location("legacy_boundary_" + name, SCRIPTS / (name + ".py"))
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


V4 = load("ml_provenance_contract")
V16 = load("scientific_contracts_v16")


def card():
    return {
        "status": "UNREVIEWED",
        "dataset_sha256": "a" * 64,
        "model_sha256": "b" * 64,
        "code_sha256": "c" * 64,
        "environment_sha256": "d" * 64,
        "metrics": {"mae": 0.1},
        "applicability_domain": {"declared": "synthetic"},
        "calibrated_uncertainty": {"declared": "synthetic"},
        "holdout_validation": {"declared": "synthetic"},
        "independent_approval": {"signature": "not-a-signature", "issuer": "self"},
    }


@pytest.mark.parametrize("status", ["UNREVIEWED", "ACCEPTED", "PASS"])
def test_v4_public_mapping_is_structural_only_even_if_it_declares_acceptance(status: str) -> None:
    value = card()
    value["status"] = status
    result = V4.validate_model_card(value)
    assert result["structure_valid"] is True
    assert result["status"] == "HOLD"
    assert result["predictive_use_allowed"] is False
    assert result["reason_codes"] == ["APPROVAL_UNVERIFIED"]
    assert "model_acceptance_v5.assess_model_card" in result["migration"]


@pytest.mark.parametrize("approval", [True, False, {"signature": "not-a-signature"}])
def test_v16_no_self_asserted_approval_can_return_accepted(approval) -> None:
    value = card()
    value["independent_approval"] = approval
    assert V16.model_acceptance(value).startswith("HOLD_")


def test_legacy_checks_still_reject_missing_or_invalid_structure() -> None:
    with pytest.raises(V4.MLProvenanceError):
        V4.validate_model_card({})
    value = card()
    value["model_sha256"] = "not-a-digest"
    with pytest.raises(ValueError, match="model_sha256"):
        V4.validate_model_card(value)
    assert V16.model_acceptance(value) == "INVALID_DIGEST"
    assert V16.model_acceptance({}) == "HOLD_INCOMPLETE_EVIDENCE"

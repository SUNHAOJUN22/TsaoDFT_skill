"""Malformed suite documents must fail structurally without escaping the CLI contract."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
HANDOFF = yaml.safe_load((ROOT / "examples/handoff.yaml").read_text(encoding="utf-8"))
FINGERPRINT = yaml.safe_load((ROOT / "templates/method-fingerprint.yaml").read_text(encoding="utf-8"))
FINGERPRINT["model_chemistry"].update(method="B3LYP", basis_or_pseudopotential="def2-SVP")
FINGERPRINT["spin_charge"].update(charge=0, multiplicity_or_magnetism=1)
FINGERPRINT["status"] = "accepted"


def run_document(tmp_path: Path, kind: str, document: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    source = tmp_path / "document.yaml"
    original = yaml.safe_dump(document)
    source.write_text(original, encoding="utf-8")
    script = "validate_handoff.py" if kind == "handoff" else "validate_method_fingerprint.py"
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script), str(source), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert "Traceback" not in result.stderr, result.stderr
    assert source.read_text(encoding="utf-8") == original
    return result.returncode, json.loads(result.stdout)


@pytest.mark.parametrize(
    ("kind", "field"),
    [
        *[("handoff", field) for field in ("source_skill", "target_skill", "support_level", "approval_status")],
        *[("fingerprint", field) for field in ("domain", "engine", "status")],
    ],
)
@pytest.mark.parametrize("value", [[], {}], ids=["list", "mapping"])
def test_enum_containers_are_structured_failures(tmp_path: Path, kind: str, field: str, value: Any) -> None:
    document = copy.deepcopy(HANDOFF if kind == "handoff" else FINGERPRINT)
    document[field] = value
    code, report = run_document(tmp_path, kind, document)
    assert code == 1
    assert report["ok"] is False
    assert report["errors"]


@pytest.mark.parametrize("field", ["model_chemistry", "numerics", "spin_charge", "standard_state", "provenance"])
@pytest.mark.parametrize("value", [None, [], ["unexpected"], "unexpected"], ids=["null", "empty-list", "list", "text"])
def test_accepted_fingerprint_requires_mapping_sections(tmp_path: Path, field: str, value: Any) -> None:
    document = copy.deepcopy(FINGERPRINT)
    document[field] = value
    code, report = run_document(tmp_path, "fingerprint", document)
    assert code == 1
    assert report["ok"] is False
    assert report["errors"]


@pytest.mark.parametrize("field", ["jobs", "cpu_hours", "gpu_hours", "storage_gb"])
def test_resource_integer_overflow_is_a_structured_failure(tmp_path: Path, field: str) -> None:
    document = copy.deepcopy(HANDOFF)
    document["resource_estimate"][field] = 10**400
    code, report = run_document(tmp_path, "handoff", document)
    assert code == 1
    assert report["ok"] is False
    assert report["errors"]


@pytest.mark.parametrize("kind", ["handoff", "fingerprint"])
def test_existing_valid_documents_still_pass(tmp_path: Path, kind: str) -> None:
    code, report = run_document(tmp_path, kind, copy.deepcopy(HANDOFF if kind == "handoff" else FINGERPRINT))
    assert code == 0
    assert report == {"ok": True, "errors": [], "warnings": []}

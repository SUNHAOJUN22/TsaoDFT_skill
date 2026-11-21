"""A restart record must identify two runs and an actual checkpoint locator."""

from __future__ import annotations

import copy
import json
import runpy
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/validate_restart_lineage.py"
VALIDATE = runpy.run_path(str(SCRIPT))["validate"]
TEMPLATE = yaml.safe_load((ROOT / "templates/restart-lineage.yaml").read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "field",
    [
        "lineage_id",
        "engine",
        "parent_run_id",
        "child_run_id",
        "parent_method_fingerprint",
        "child_method_fingerprint",
        "status",
    ],
)
def test_blank_restart_identity_cannot_pass(field: str) -> None:
    record = copy.deepcopy(TEMPLATE)
    record[field] = " \t"
    errors, _ = VALIDATE(record)
    assert any(field in error for error in errors)


@pytest.mark.parametrize("field,value", [("lineage_id", True), ("engine", [])])
def test_restart_identity_requires_text(field: str, value: object) -> None:
    record = copy.deepcopy(TEMPLATE)
    record[field] = value
    errors, _ = VALIDATE(record)
    assert any(field in error for error in errors)


@pytest.mark.parametrize("checkpoint_path", ["missing", " \t", None, False])
def test_restart_requires_a_checkpoint_locator(checkpoint_path: object) -> None:
    record = copy.deepcopy(TEMPLATE)
    if checkpoint_path == "missing":
        record["parent_checkpoint"].pop("path")
    else:
        record["parent_checkpoint"]["path"] = checkpoint_path
    errors, _ = VALIDATE(record)
    assert any("checkpoint path" in error for error in errors)


def test_a_run_cannot_be_its_own_restart_parent() -> None:
    record = copy.deepcopy(TEMPLATE)
    record["child_run_id"] = record["parent_run_id"]
    errors, _ = VALIDATE(record)
    assert any("distinct" in error for error in errors)


def test_blank_change_does_not_describe_a_restart_change() -> None:
    record = copy.deepcopy(TEMPLATE)
    record["restart_mode"] = "new_lineage"
    record["changes"] = [" \t"]
    errors, _ = VALIDATE(record)
    assert any("changes" in error for error in errors)


@pytest.mark.parametrize("mode", [[], {}])
def test_nonscalar_restart_mode_returns_structured_cli_failure(tmp_path: Path, mode: object) -> None:
    record = copy.deepcopy(TEMPLATE)
    record["restart_mode"] = mode
    source = tmp_path / "restart.yaml"
    source.write_text(yaml.safe_dump(record), encoding="utf-8")
    before = source.read_bytes()
    result = subprocess.run([sys.executable, str(SCRIPT), str(source)], capture_output=True, text=True, check=False)
    assert result.returncode == 1
    assert json.loads(result.stdout)["ok"] is False
    assert "invalid restart_mode" in result.stdout
    assert "Traceback" not in result.stderr
    assert source.read_bytes() == before


@pytest.mark.parametrize("mode", ["exact_restart", "geometry_reuse", "wavefunction_guess_reuse", "new_lineage"])
def test_complete_distinct_restart_records_keep_existing_modes(mode: str) -> None:
    record = copy.deepcopy(TEMPLATE)
    record["restart_mode"] = mode
    errors, warnings = VALIDATE(record)
    assert errors == []
    assert bool(warnings) is (mode in {"geometry_reuse", "wavefunction_guess_reuse"})

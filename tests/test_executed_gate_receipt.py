from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest


def load_gate():
    path = Path(__file__).resolve().parents[1] / "scripts/quality_gate.py"
    spec = importlib.util.spec_from_file_location("executed_gate_regression", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "skip_tests, code, expected",
    [(False, 1, "UNQUALIFIED"), (True, 0, "STATIC_GATES_ONLY"), (False, 0, "SOFTWARE_GATES_PASSED")],
)
def test_receipt_uses_only_current_stage_outcomes(tmp_path: Path, skip_tests: bool, code: int, expected: str) -> None:
    gate = load_gate()
    receipt = tmp_path / "quality-run-acceptance.json"
    receipt.write_text('{"acceptance_state":"STALE_SUCCESS"}', encoding="utf-8")
    arguments = ["quality_gate.py", "--json"] + (["--skip-tests"] if skip_tests else [])
    stage = gate.Stage("synthetic gate", (sys.executable, "-c", "pass"))

    def run_stage(*args, **kwargs):
        assert not receipt.exists()
        return {"stage": stage.name, "returncode": code, "seconds": 0.0, "timed_out": False}

    with (
        patch.object(gate, "ROOT", tmp_path),
        patch.object(gate, "stages", return_value=[stage]),
        patch.object(gate, "run_stage", side_effect=run_stage),
        patch.object(sys, "argv", arguments),
    ):
        assert gate.main() == (1 if code else 0)
    result = json.loads(receipt.read_text(encoding="utf-8"))
    assert result["acceptance_state"] == expected
    assert result["external_execution"] == "NOT_EVALUATED"
    assert result["scientific_approval"] == "NOT_EVALUATED"
    assert result["stages"][0]["returncode"] == code

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts import quality_gate as gate


@pytest.mark.parametrize("timeout", [float("nan"), float("inf"), float("-inf"), 0.0, -1.0])
def test_invalid_timeouts_rejected_before_process_start(timeout: float) -> None:
    stage = gate.Stage("unused", (sys.executable, "-c", "pass"))
    with patch.object(gate.subprocess, "run") as run:
        with pytest.raises(ValueError, match="finite and positive"):
            gate.run_stage(stage, dict(os.environ), timeout_override=timeout)
        run.assert_not_called()


def test_start_failure_produces_unqualified_receipt(tmp_path: Path) -> None:
    receipt = tmp_path / "quality-run-acceptance.json"
    receipt.write_text('{"acceptance_state":"SOFTWARE_GATES_PASSED"}', encoding="utf-8")
    missing = gate.Stage("missing executable", (str(tmp_path / "not-installed"),))
    with (
        patch.object(gate, "ROOT", tmp_path),
        patch.object(gate, "stages", return_value=[missing]),
        patch.object(sys, "argv", ["quality_gate.py", "--json"]),
    ):
        assert gate.main() == 1
    data = json.loads(receipt.read_text(encoding="utf-8"))
    assert data["acceptance_state"] == "UNQUALIFIED"
    assert data["ok"] is False
    assert data["stages"][0]["returncode"] == 127
    assert data["stages"][0]["timed_out"] is False
    assert "FileNotFoundError" in data["stages"][0]["error"]

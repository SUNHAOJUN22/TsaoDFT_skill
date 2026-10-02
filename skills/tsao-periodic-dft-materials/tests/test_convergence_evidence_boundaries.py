from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/analyze_convergence.py"


def module() -> Any:
    spec = importlib.util.spec_from_file_location("convergence_evidence_boundaries", SCRIPT)
    assert spec is not None and spec.loader is not None
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


@pytest.mark.parametrize("values", [[1.0, 1.0, 1.0], [1.0, 2.0, 2.0], [3.0, 2.0, 1.0]])
def test_repeated_or_reversed_refinements_do_not_prove_convergence(values: list[float]) -> None:
    report = module().analyze([(value, -1.0) for value in values], 0.01, 2)
    assert not report["ok"]
    assert not report["converged_candidate"]
    assert report["recommended_value"] is None
    assert "distinct" in " ".join(report["errors"])


@pytest.mark.parametrize("threshold", [float("nan"), float("inf"), -1.0, True, 10**400])
def test_invalid_thresholds_return_strict_json_errors(threshold: object) -> None:
    report = module().analyze([(1.0, -1.0), (2.0, -1.0)], threshold, 1)
    assert not report["ok"]
    assert report["threshold"] is None
    json.dumps(report, allow_nan=False)


def test_observable_overflow_is_explicit_not_infinity_in_evidence() -> None:
    report = module().analyze([(1.0, -1e308), (2.0, 1e308)], 1.0, 1)
    assert not report["ok"]
    assert report["deltas"][0]["absolute_change"] is None
    json.dumps(report, allow_nan=False)


@pytest.mark.parametrize("point", [(True, 0.0), (0.0, float("nan")), (10**400, 0.0), (1.0,)])
def test_public_api_revalidates_pairs(point: object) -> None:
    report = module().analyze([point], 0.1, 1)
    assert not report["ok"]
    json.dumps(report, allow_nan=False)


def test_duplicate_headers_fail_closed(tmp_path: Path) -> None:
    path = tmp_path / "duplicate.csv"
    path.write_text("value,observable_value,observable_value\n1,2,3\n", encoding="utf-8")
    points, errors = module().load_points(path, "value", "observable_value")
    assert points == []
    assert "duplicate CSV headers" in " ".join(errors)


def test_nan_cli_diagnostic_is_machine_readable(tmp_path: Path) -> None:
    path = tmp_path / "series.csv"
    path.write_text("value,observable_value\n1,-1\n2,-1\n3,-1\n", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(path), "--absolute-threshold", "nan"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    report = json.loads(result.stdout)
    assert report["threshold"] is None
    assert not report["converged_candidate"]
    json.dumps(report, allow_nan=False)

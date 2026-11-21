from __future__ import annotations

import importlib.util
import json
import math
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


@pytest.mark.parametrize("column", ["value", "observable_value"])
@pytest.mark.parametrize("literal", ["1e-400", "-1e-400"])
def test_csv_nonzero_underflow_cannot_prove_convergence(tmp_path: Path, column: str, literal: str) -> None:
    path = tmp_path / "series.csv"
    rows = [["300", "0"], ["400", "0"], ["500", "0"]]
    rows[0][0 if column == "value" else 1] = literal
    path.write_text("value,observable_value\n" + "\n".join(",".join(row) for row in rows) + "\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(path), "--absolute-threshold=0"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    report = json.loads(result.stdout)
    assert not report["ok"]
    assert not report["converged_candidate"]
    assert report["recommended_value"] is None
    assert "underflow" in " ".join(report["errors"])


@pytest.mark.parametrize("literal", ["1e-400", "-1e-400"])
def test_cli_threshold_nonzero_underflow_is_rejected(tmp_path: Path, literal: str) -> None:
    path = tmp_path / "series.csv"
    path.write_text("value,observable_value\n300,0\n400,0\n500,0\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(path), "--absolute-threshold=" + literal],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    report = json.loads(result.stdout)
    assert report["threshold"] is None
    assert not report["ok"]
    assert not report["converged_candidate"]
    assert "underflow" in " ".join(report["errors"])


@pytest.mark.parametrize("literal", ["0e-9999", "-0e-9999", "5e-324", "-5e-324"])
def test_csv_preserves_zeros_and_representable_subnormal_observables(tmp_path: Path, literal: str) -> None:
    path = tmp_path / "series.csv"
    path.write_text(f"value,observable_value\n300,{literal}\n400,{literal}\n500,{literal}\n", encoding="utf-8")

    points, errors = module().load_points(path, "value", "observable_value")

    assert not errors
    assert len(points) == 3
    assert all(observable == float(literal) for _, observable in points)
    assert all(math.copysign(1, observable) == math.copysign(1, float(literal)) for _, observable in points)
    assert module().analyze(points, 0.0, 2)["converged_candidate"]


@pytest.mark.parametrize("threshold", ["0e-9999", "-0e-9999", "5e-324"])
def test_cli_preserves_zero_and_representable_subnormal_thresholds(tmp_path: Path, threshold: str) -> None:
    path = tmp_path / "series.csv"
    path.write_text("value,observable_value\n300,0\n400,0\n500,0\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(path), "--absolute-threshold=" + threshold],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    report = json.loads(result.stdout)
    assert report["ok"]
    assert report["converged_candidate"]
    assert report["threshold"] == float(threshold)
    assert math.copysign(1, report["threshold"]) == math.copysign(1, float(threshold))

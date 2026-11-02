"""Synthetic numerical/input counterexamples; no external engine is executed."""

from __future__ import annotations

import importlib.util
import json
import math
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
UNCERTAINTY = ROOT / "skills/tsao-dft-researcher/scripts/validate_uncertainty_budget.py"
EYRING = ROOT / "skills/tsao-dft-kinetics-multiscale/scripts/eyring_rates.py"
RIDGE = ROOT / "skills/tsao-dft-ml-active-learning/scripts/train_ridge_baseline.py"


def uncertainty_module():
    spec = importlib.util.spec_from_file_location("uncertainty_input_boundaries", UNCERTAINTY)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def budget(values, rule="root_sum_square"):
    return {
        "schema_version": "1.0",
        "project_id": "synthetic",
        "observable": "barrier",
        "unit": "kcal/mol",
        "components": [{"type": "numerical", "magnitude": value, "basis": "synthetic bound"} for value in values],
        "combination_rule": rule,
        "status": "accepted",
    }


def run(script, *arguments):
    return subprocess.run(
        [sys.executable, str(script), *map(str, arguments)],
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.parametrize(
    "values,rule",
    [
        ([1.4e308, 1.4e308], "root_sum_square"),
        ([1e308, 1e308], "sum_bounds"),
        ([10**400, 1.0], "root_sum_square"),
    ],
)
def test_unrepresentable_uncertainty_cannot_be_accepted(values, rule):
    errors, _, summary = uncertainty_module().validate(budget(values, rule))
    assert errors
    assert summary["combined_magnitude"] is None
    json.dumps(summary, allow_nan=False)


@pytest.mark.parametrize("field,value", [("combination_rule", []), ("component_type", {})])
def test_malformed_uncertainty_labels_are_structured_errors(field, value):
    data = budget([1.0])
    if field == "component_type":
        data["components"][0]["type"] = value
    else:
        data[field] = value
    errors, _, summary = uncertainty_module().validate(data)
    assert errors
    assert summary["combined_magnitude"] is None


def test_valid_component_cannot_conceal_invalid_component():
    errors, _, summary = uncertainty_module().validate(budget([3.0, float("nan")]))
    assert errors
    assert summary["combined_magnitude"] is None


@pytest.mark.parametrize("rule", ["root_sum_square", "sum_bounds"])
def test_uncertainty_cli_overflow_is_finite_json_failure(tmp_path, rule):
    source = tmp_path / "budget.yaml"
    source.write_text(yaml.safe_dump(budget([1.4e308, 1.4e308], rule)), encoding="utf-8")
    result = run(UNCERTAINTY, source)
    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    report = json.loads(result.stdout, parse_constant=lambda value: pytest.fail(f"nonfinite JSON {value}"))
    assert report["ok"] is False
    assert report["summary"]["combined_magnitude"] is None


@pytest.mark.parametrize(
    "values,rule,expected",
    [
        ([3.0, 4.0], "root_sum_square", 5.0),
        ([0.0, 0.0], "root_sum_square", 0.0),
        ([1e308, 1e308], "root_sum_square", 1.4142135623730951e308),
        ([1e16, 1.0, 1.0], "sum_bounds", 10000000000000002.0),
    ],
)
def test_representable_uncertainty_is_preserved(values, rule, expected):
    errors, warnings, summary = uncertainty_module().validate(budget(values, rule))
    assert errors == warnings == []
    assert summary["combined_magnitude"] == pytest.approx(expected, rel=1e-15, abs=0)


@pytest.mark.parametrize(
    "header,row",
    [
        ("delta_g_dagger_kcal_mol,delta_g_dagger_kcal_mol", "100,0"),
        ("delta_g_dagger_kcal_mol,", "15,unused"),
    ],
)
def test_eyring_ambiguous_headers_preserve_existing_output(tmp_path, header, row):
    source = tmp_path / "barriers.csv"
    source.write_text(f"{header}\n{row}\n", encoding="utf-8")
    target = tmp_path / "rates.csv"
    target.write_bytes(b"previous independently retained result\n")
    original = target.read_bytes()
    result = run(EYRING, source, "--temperature", 298.15, "--out", target)
    assert result.returncode == 1
    assert json.loads(result.stdout)["ok"] is False
    assert target.read_bytes() == original
    assert not list(tmp_path.glob("*.tmp"))


def test_eyring_cannot_replace_its_input(tmp_path):
    source = tmp_path / "barriers.csv"
    source.write_text("delta_g_dagger_kcal_mol\n15\n", encoding="utf-8")
    original = source.read_bytes()
    result = run(EYRING, source, "--temperature", 298.15, "--out", source)
    assert result.returncode == 1
    assert "input" in " ".join(json.loads(result.stdout)["errors"])
    assert source.read_bytes() == original


def train(source, destination):
    return run(RIDGE, source, "--features", "x", "--target", "target", "--group", "parent_id", "--out-dir", destination)


def test_ridge_duplicate_target_header_cannot_silently_select_a_label(tmp_path):
    source = tmp_path / "data.csv"
    source.write_text(
        "parent_id,x,target,target\n" + "".join(f"p{i},{i},100,{2 * i + 1}\n" for i in range(12)), encoding="utf-8"
    )
    destination = tmp_path / "fit"
    result = train(source, destination)
    assert result.returncode == 1
    assert "duplicate" in " ".join(json.loads(result.stdout)["errors"])
    assert not destination.exists()


def test_ridge_cannot_replace_raw_dataset_with_predictions(tmp_path):
    source = tmp_path / "predictions.csv"
    source.write_text("parent_id,x,target\n" + "".join(f"p{i},{i},{2 * i + 1}\n" for i in range(12)), encoding="utf-8")
    original = source.read_bytes()
    result = train(source, tmp_path)
    assert result.returncode == 1
    assert "input" in " ".join(json.loads(result.stdout)["errors"])
    assert source.read_bytes() == original
    assert not (tmp_path / "model-card.json").exists()


@pytest.mark.parametrize("output_name", ["predictions.csv", "model-card.json"])
def test_ridge_hardlinked_outputs_cannot_replace_raw_dataset(tmp_path, output_name):
    source = tmp_path / "data.csv"
    source.write_text("parent_id,x,target\n" + "".join(f"p{i},{i},{2 * i + 1}\n" for i in range(12)), encoding="utf-8")
    original = source.read_bytes()
    destination = tmp_path / "fit"
    destination.mkdir()
    (destination / output_name).hardlink_to(source)
    result = train(source, destination)
    assert result.returncode == 1
    assert "input" in " ".join(json.loads(result.stdout)["errors"])
    assert source.read_bytes() == original
    assert (destination / output_name).read_bytes() == original
    assert {path.name for path in destination.iterdir()} == {output_name}


def test_ridge_unreadable_dataset_returns_a_structured_failure(tmp_path):
    result = train(tmp_path / "missing.csv", tmp_path / "fit")
    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    assert json.loads(result.stdout)["ok"] is False


def test_interval_applies_standard_state_before_exponentiating():
    """Extreme synthetic units check numeric ordering, not physical TST validity."""
    script = EYRING.with_name("propagate_barrier_uncertainty.py")
    result = run(
        script,
        "--barrier",
        -500,
        "--uncertainty",
        1,
        "--temperature",
        300,
        "--molecularity",
        2,
        "--standard-state",
        "1e100 M",
        "--barrier-standard-state",
        "1e100 M",
        "--activity-convention",
        "a=c/c0",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    # Independent closed-form oracle with fixed SI constants and kcal/mol conversion.
    prefactor = 1.380649e-23 * 300 / 6.62607015e-34
    rt = (8.31446261815324 / 4184) * 300
    expected_log = math.log(prefactor / 1e100) + 500 / rt
    for label, shift in (("central", 0), ("lower", -1 / rt), ("upper", 1 / rt)):
        assert report[f"{label}_ln_rate"] == pytest.approx(expected_log + shift, rel=1e-14)
        assert report[f"{label}_rate"] == pytest.approx(math.exp(expected_log + shift), rel=5e-13)

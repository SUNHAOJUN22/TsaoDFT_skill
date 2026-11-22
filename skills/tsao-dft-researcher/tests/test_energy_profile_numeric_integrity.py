"""Ambiguous or unrepresentable energies must not replace published profiles."""

from __future__ import annotations

import csv
import importlib.util
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "build_energy_profile.py"


def load_profile() -> Any:
    spec = importlib.util.spec_from_file_location("energy_profile_numeric_integrity", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    ("contents", "message"),
    [
        ("label,g_hartree,g_hartree\nR,0,0\nTS,0.01,1.0\n", "duplicate"),
        ("label,label,g_hartree\nR,S,0\nTS,Product,0.01\n", "duplicate"),
        ("label,g_hartree\nR,0\nTS,1e-400\n", "underflow"),
        ("label,g_hartree\nR,0\nTS,-1e-400\n", "underflow"),
        ("label,g_hartree\nR,0\nTS,1e308\n", "range"),
        ("label,g_hartree\nR,0\nTS,-1e308\n", "range"),
        ("label,g_hartree\nR,-1e308\nTS,1e308\n", "range"),
        ("label,g_hartree\nR,1e308\nTS,-1e308\n", "range"),
    ],
    ids=[
        "duplicate-energy-header",
        "duplicate-label-header",
        "positive-input-underflow",
        "negative-input-underflow",
        "positive-conversion-overflow",
        "negative-conversion-overflow",
        "positive-difference-overflow",
        "negative-difference-overflow",
    ],
)
def test_cli_rejects_invalid_energies_without_replacing_outputs(tmp_path: Path, contents: str, message: str) -> None:
    source = tmp_path / "energies.csv"
    original = contents.encode("utf-8")
    source.write_bytes(original)
    prefix = tmp_path / "published"
    published = {
        prefix.with_suffix(suffix): f"existing {suffix}".encode() for suffix in (".csv", ".svg", ".pdf", ".png")
    }
    for target, payload in published.items():
        target.write_bytes(payload)
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(source), "--out", str(prefix)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 1, result.stdout
    error = json.loads(result.stderr)
    assert error["ok"] is False
    assert message in " ".join(error["errors"])
    assert source.read_bytes() == original
    assert {path: path.read_bytes() for path in published} == published
    assert not list(tmp_path.glob(".published-energy-profile-*"))


@pytest.mark.parametrize("literal", ["0", "-0", "0e-400", "-0e-400", "1e-300", "-1e-300", "5e-324"])
def test_exact_zero_and_representable_small_energies_are_preserved(tmp_path: Path, literal: str) -> None:
    module = load_profile()
    source = tmp_path / "energies.csv"
    source.write_text(f"label,g_hartree,method\nR,0,method-a\nTS,{literal},method-a\n", encoding="utf-8")
    rows = module.read_energy_rows(source, "g_hartree")
    assert rows == [("R", 0.0), ("TS", float(literal))]
    relative = module.build_relative_rows(rows, module.select_reference(rows, "first"))
    assert relative[1]["energy"] == float(literal)
    assert relative[1]["relative_kcal_mol"] == float(literal) * module.HARTREE_TO_KCAL_MOL


@pytest.mark.parametrize("energy", [1e305, -1e305])
def test_finite_relative_energy_near_range_limit_remains_supported(energy: float) -> None:
    module = load_profile()
    relative = module.build_relative_rows([("R", 0.0), ("TS", energy)], 0.0)
    assert math.isfinite(relative[1]["relative_kcal_mol"])
    assert relative[1]["relative_kcal_mol"] == energy * module.HARTREE_TO_KCAL_MOL


@pytest.mark.parametrize("energy", [float("nan"), float("inf"), -float("inf")])
def test_public_builder_rejects_nonfinite_relative_energy(energy: float) -> None:
    module = load_profile()
    with pytest.raises(module.EnergyProfileError, match="range"):
        module.build_relative_rows([("R", 0.0), ("TS", energy)], 0.0)


@pytest.mark.parametrize("column", ["label", "relative_kcal_mol"])
@pytest.mark.parametrize("aliases_source", [False, True])
def test_reserved_energy_column_cannot_replace_source_or_published_profile(
    tmp_path: Path, column: str, aliases_source: bool
) -> None:
    contents = (
        "label,g_hartree\n1,-100\n2,-99.9\n" if column == "label" else "label,relative_kcal_mol\nR,-100\nTS,-99.9\n"
    )
    source = tmp_path / "source.csv"
    original = contents.encode()
    source.write_bytes(original)
    prefix = source.with_suffix("") if aliases_source else tmp_path / "published"
    published = {}
    for suffix in (".csv", ".svg", ".pdf", ".png"):
        target = prefix.with_suffix(suffix)
        published[target] = original if target == source else f"existing {suffix}".encode()
        target.write_bytes(published[target])
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(source), "--column", column, "--out", str(prefix)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 1, result.stdout
    error = json.loads(result.stderr)
    assert error["ok"] is False
    if not aliases_source:
        assert "reserved" in " ".join(error["errors"])
    assert source.read_bytes() == original
    assert {path: path.read_bytes() for path in published} == published
    assert not list(tmp_path.glob(".*-energy-profile-*"))


@pytest.mark.parametrize("column", ["label", "relative_kcal_mol"])
def test_table_writer_rejects_reserved_column_before_opening_output(tmp_path: Path, column: str) -> None:
    module = load_profile()
    path = tmp_path / "table.csv"
    original = b"existing publication table"
    path.write_bytes(original)
    rows = module.build_relative_rows([("R", -100.0), ("TS", -99.9)], -100.0)
    with pytest.raises(module.EnergyProfileError, match="reserved"):
        module.write_table(path, rows, column)
    assert path.read_bytes() == original


@pytest.mark.parametrize("column", ["g_hartree", "custom_energy_eh"])
def test_custom_energy_header_preserves_absolute_and_relative_columns(tmp_path: Path, column: str) -> None:
    module = load_profile()
    source = tmp_path / "input.csv"
    source.write_text(f"label,{column}\nR,-100\nTS,-99.9\n", encoding="utf-8")
    raw = module.read_energy_rows(source, column)
    rows = module.build_relative_rows(raw, -100.0)
    output = tmp_path / "table.csv"
    module.write_table(output, rows, column)
    with output.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == ["label", column, "relative_kcal_mol"]
        result = list(reader)
    assert result[1]["label"] == "TS"
    assert float(result[1][column]) == -99.9
    assert float(result[1]["relative_kcal_mol"]) == pytest.approx(62.7509)

"""Synthetic OUTCAR force-table regressions; no external VASP run is claimed."""

from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path
from typing import Any

import pytest

SCRIPTS = Path(__file__).parents[1] / "skills/tsao-dft-hpc-provenance/scripts"
SPEC = importlib.util.spec_from_file_location("vasp_force_completeness_parser", SCRIPTS / "engine_parser_contract.py")
assert SPEC and SPEC.loader
parser = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = parser
SPEC.loader.exec_module(parser)
PERIODIC = Path(__file__).parents[1] / "skills/tsao-periodic-dft-materials/scripts"
STREAM_SPEC = importlib.util.spec_from_file_location("vasp_force_completeness_stream", PERIODIC / "parse_vasp.py")
assert STREAM_SPEC and STREAM_SPEC.loader
stream_parser = importlib.util.module_from_spec(STREAM_SPEC)
STREAM_SPEC.loader.exec_module(stream_parser)

HEADER = " POSITION                                       TOTAL-FORCE (eV/Angst)\n"
ROWS = " 0 0 0 0.1 0.2 0.3\n 1 1 1 0.4 0.5 0.6\n"
TABLE = HEADER + " ----------------\n" + ROWS + " ----------------\n total drift: 0 0 0\n"
NORMAL = " General timing and accounting informations for this job\n"
DAMAGED_TABLES = [
    pytest.param(TABLE.replace("0.4 0.5 0.6", "bad 0.5 0.6"), id="malformed-first-component"),
    pytest.param(TABLE.replace("0.4 0.5 0.6", "0.4 bad 0.6"), id="malformed-middle-component"),
    pytest.param(TABLE.replace("0.4 0.5 0.6", "0.4 0.5 bad"), id="malformed-last-component"),
    pytest.param(TABLE.replace(" 1 1 1 0.4 0.5 0.6\n", ""), id="missing-atom"),
    pytest.param(TABLE.replace(ROWS, ROWS + " 2 2 2 0.7 0.8 0.9\n"), id="extra-atom"),
    pytest.param(TABLE.replace("0.4 0.5 0.6", "0.4 0.5"), id="truncated-row"),
    pytest.param(TABLE.replace("0.4 0.5 0.6", "0.4 0.5 0.6 0.7"), id="extra-column"),
    pytest.param(TABLE.replace(" 1 1 1 ", " broken 1 1 "), id="malformed-position"),
    pytest.param(TABLE.replace(" total drift: 0 0 0\n", ""), id="missing-closing-summary"),
    pytest.param(TABLE + HEADER + " 0 0 0 7 8 9\n", id="latest-table-is-truncated"),
    pytest.param(TABLE + TABLE.replace("0.4 0.5 0.6", "bad 0.5 0.6"), id="latest-table-is-malformed"),
    pytest.param(TABLE.replace(ROWS, ""), id="empty-table"),
]
INVALID_COUNTS = ["0", "-2", "2.0", "", pytest.param("9" * 5000, id="integer-limit")]


def job(table: str = TABLE, atom_count: str | None = "2") -> str:
    count = "" if atom_count is None else f" number of ions NIONS = {atom_count}\n"
    return "vasp.6.5.1\n" + count + " free energy TOTEN = -10 eV\n EDIFF is reached\n" + table + NORMAL


def parse(tmp_path: Path, text: str) -> dict[str, Any]:
    path = tmp_path / "OUTCAR.synthetic"
    path.write_text(text, encoding="utf-8")
    return parser.parse_engine_output("vasp", path)


def parse_stream(tmp_path: Path, text: str) -> dict[str, Any]:
    path = tmp_path / "OUTCAR.synthetic"
    path.write_text(text, encoding="utf-8")
    return stream_parser.parse(path)


@pytest.mark.parametrize("table", DAMAGED_TABLES)
def test_incomplete_last_force_table_never_emits_a_partial_vector(tmp_path: Path, table: str) -> None:
    result = parse(tmp_path, job(table))
    assert result["forces"]["values"] is None
    assert any("force" in warning.lower() for warning in result["warnings"])
    # Force availability is separate from termination/electronic and scientific acceptance.
    assert result["parser_accepted"] is True
    assert result["energy"]["value"] == -10.0
    assert result["scientific_acceptance"] == "PENDING"


@pytest.mark.parametrize("atom_count", INVALID_COUNTS)
def test_invalid_declared_atom_count_cannot_certify_force_shape(tmp_path: Path, atom_count: str) -> None:
    result = parse(tmp_path, job(atom_count=atom_count))
    assert result["forces"]["values"] is None
    assert any("atom count" in warning for warning in result["warnings"])


@pytest.mark.parametrize("atom_count", ["2", None])
def test_complete_table_preserves_legacy_optional_count_and_atom_order(tmp_path: Path, atom_count: str | None) -> None:
    result = parse(tmp_path, job(atom_count=atom_count))
    assert result["forces"] == {"values": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6], "unit": "eV/angstrom"}
    assert result["warnings"] == []
    assert result["scientific_acceptance"] == "PENDING"


def test_last_complete_ionic_step_wins(tmp_path: Path) -> None:
    final = TABLE.replace("0.1 0.2 0.3", "1 2 3").replace("0.4 0.5 0.6", "4 5 6")
    result = parse(tmp_path, job(TABLE + "\n" + final))
    assert result["forces"]["values"] == [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]


@pytest.mark.parametrize("atom_count", ["1", None])
def test_final_job_does_not_inherit_prior_atom_count(tmp_path: Path, atom_count: str | None) -> None:
    single_atom = TABLE.replace(" 1 1 1 0.4 0.5 0.6\n", "")
    result = parse(tmp_path, job() + job(single_atom, atom_count))
    assert result["forces"]["values"] == [0.1, 0.2, 0.3]
    assert result["job_index"] == 2


def test_final_job_without_force_table_does_not_inherit_old_forces(tmp_path: Path) -> None:
    result = parse(tmp_path, job() + job(""))
    assert result["forces"]["values"] is None
    assert result["job_index"] == 2


def test_final_job_does_not_close_a_force_table_from_a_prior_job(tmp_path: Path) -> None:
    earlier = job(TABLE.replace(" total drift: 0 0 0\n", ""))
    result = parse(tmp_path, earlier + job())
    assert result["forces"]["values"] == [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
    assert result["job_index"] == 2


@pytest.mark.parametrize("table", DAMAGED_TABLES)
def test_stream_incomplete_last_table_never_emits_a_partial_maximum(tmp_path: Path, table: str) -> None:
    result = parse_stream(tmp_path, job(table))
    assert result["max_force_eV_per_angstrom"] is None
    assert any("force" in warning.lower() for warning in result["warnings"])
    assert result["last_toten_eV"] == -10.0
    assert result["scientific_acceptance"] == "PENDING"


@pytest.mark.parametrize("atom_count", INVALID_COUNTS)
def test_stream_invalid_declared_atom_count_cannot_certify_force_shape(tmp_path: Path, atom_count: str) -> None:
    result = parse_stream(tmp_path, job(atom_count=atom_count))
    assert result["max_force_eV_per_angstrom"] is None
    assert any("atom count" in warning for warning in result["warnings"])


@pytest.mark.parametrize("atom_count", ["2", None])
def test_stream_complete_table_preserves_maximum_of_atomic_norms(tmp_path: Path, atom_count: str | None) -> None:
    result = parse_stream(tmp_path, job(atom_count=atom_count))
    assert result["max_force_eV_per_angstrom"] == pytest.approx(math.hypot(0.4, 0.5, 0.6))
    assert result["parser_accepted"] is True
    assert result["warnings"] == []


def test_stream_last_complete_ionic_step_wins(tmp_path: Path) -> None:
    earlier = TABLE.replace("0.4 0.5 0.6", "4 5 6")
    result = parse_stream(tmp_path, job(earlier + TABLE))
    assert result["max_force_eV_per_angstrom"] == pytest.approx(math.hypot(0.4, 0.5, 0.6))


@pytest.mark.parametrize("atom_count", ["1", None])
def test_stream_final_job_does_not_inherit_prior_atom_count(tmp_path: Path, atom_count: str | None) -> None:
    single_atom = TABLE.replace(" 1 1 1 0.4 0.5 0.6\n", "")
    result = parse_stream(tmp_path, job() + job(single_atom, atom_count))
    assert result["max_force_eV_per_angstrom"] == pytest.approx(math.hypot(0.1, 0.2, 0.3))
    assert result["parser_segment_count"] == 2


def test_stream_final_job_without_force_table_does_not_inherit_old_forces(tmp_path: Path) -> None:
    result = parse_stream(tmp_path, job() + job(""))
    assert result["max_force_eV_per_angstrom"] is None
    assert result["parser_segment_count"] == 2


def test_stream_final_job_does_not_close_a_force_table_from_a_prior_job(tmp_path: Path) -> None:
    earlier = job(TABLE.replace(" total drift: 0 0 0\n", ""))
    result = parse_stream(tmp_path, earlier + job())
    assert result["max_force_eV_per_angstrom"] == pytest.approx(math.hypot(0.4, 0.5, 0.6))
    assert result["jobs"][0]["max_force_eV_per_angstrom"] is None
    assert result["parser_accepted"] is True
    assert result["parser_segment_count"] == 2


@pytest.mark.parametrize("components", ["1e-400 0.5 0.6", "1e999 0.5 0.6", "1.5e308 1.5e308 1.5e308"])
def test_stream_numeric_range_failure_never_leaves_a_partial_maximum(tmp_path: Path, components: str) -> None:
    result = parse_stream(tmp_path, job(TABLE.replace("0.4 0.5 0.6", components)))
    assert result["max_force_eV_per_angstrom"] is None
    assert result["parser_accepted"] is False
    assert any(reason.startswith("NUMERIC_RANGE_ERROR:") for reason in result["parser_reason_codes"])

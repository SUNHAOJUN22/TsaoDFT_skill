"""Synthetic parser regressions; no Gaussian executable or real engine claim."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

SOURCE = Path(__file__).parents[1] / "skills/tsao-dft-researcher/scripts/parse_gaussian.py"
SPEC = importlib.util.spec_from_file_location("gaussian_orbital_block_identity", SOURCE)
assert SPEC and SPEC.loader
PARSER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PARSER
SPEC.loader.exec_module(PARSER)

HEADER = "Entering Gaussian System\n#p UHF/STO-3G Opt Pop=Full\n\nCharge = 0 Multiplicity = 2\n"
FIRST = (
    "SCF Done: E(UHF) = -100.0 A.U.\n"
    "Alpha occ. eigenvalues -- -1.0 -0.6\nAlpha virt. eigenvalues -- 0.1 0.2\n"
    "Beta occ. eigenvalues -- -1.1 -0.7\nBeta virt. eigenvalues -- 0.15 0.25\n"
    "Population analysis using the SCF density.\n"
)
FINAL = (
    "SCF Done: E(UHF) = -101.0 A.U.\n"
    "Alpha occ. eigenvalues -- -1.2 -0.3\nAlpha virt. eigenvalues -- 0.7 0.8\n"
    "Beta occ. eigenvalues -- -1.3 -0.4\nBeta virt. eigenvalues -- 0.75 0.85\n"
)
END = "Optimization completed.\nNormal termination of Gaussian\n"
ORACLE = {
    "alpha_occ_hartree": [-1.2, -0.3],
    "alpha_virt_hartree": [0.7, 0.8],
    "beta_occ_hartree": [-1.3, -0.4],
    "beta_virt_hartree": [0.75, 0.85],
    "alpha_homo_hartree": -0.3,
    "alpha_lumo_hartree": 0.7,
    "beta_homo_hartree": -0.4,
    "beta_lumo_hartree": 0.75,
}


def test_same_job_scf_cycles_cannot_mix_frontier_orbitals() -> None:
    result = PARSER.parse_log(HEADER + FIRST + FINAL + END)
    assert result["orbital_energies"] == ORACLE
    assert result["last_scf_energy_hartree"] == -101.0
    assert result["parser_segment_count"] == 1
    assert result["orbital_block"]["scf_record_index"] == 2
    assert result["orbital_block"]["status"] == "OBSERVED"
    assert result["scientific_acceptance"] == "PENDING_HUMAN_OR_CRITIC_REVIEW"


@pytest.mark.parametrize("separator", ["", "\n", "Population analysis using the SCF density.\n"])
def test_multiple_population_blocks_in_one_scf_keep_last_block_together(separator: str) -> None:
    initial = FIRST.removesuffix("Population analysis using the SCF density.\n")
    final_orbitals = FINAL.split("\n", 1)[1]
    result = PARSER.parse_log(HEADER + initial + separator + final_orbitals + END)
    assert result["orbital_energies"] == ORACLE
    assert result["orbital_block"]["block_count"] == 2


def test_wrapped_channel_lines_and_d_exponents_remain_in_one_block() -> None:
    wrapped = FINAL.replace("-1.2 -0.3", "-1.2\nAlpha occ. eigenvalues -- -3.0D-1")
    wrapped = wrapped.replace("0.7 0.8", "0.7\n\nAlpha virt. eigenvalues -- 0.8")
    assert PARSER.parse_log(HEADER + FIRST + wrapped + END)["orbital_energies"] == ORACLE


@pytest.mark.parametrize(
    "tail",
    [
        "Alpha occ. eigenvalues -- -0.3\n",
        "Alpha occ. eigenvalues -- -0.3\nAlpha virt. eigenvalues -- 0.7\n",
        "Alpha occ. eigenvalues -- -0.3\nAlpha virt. eigenvalues -- 0.7\nBeta occ. eigenvalues -- -0.4\n",
        "Alpha occ. eigenvalues -- invalid\nAlpha virt. eigenvalues -- 0.7\n",
        "Alpha occ. eigenvalues --\nAlpha virt. eigenvalues -- 0.7\n",
        "Beta occ. eigenvalues -- -0.4\nBeta virt. eigenvalues -- 0.75\n",
    ],
)
def test_incomplete_last_block_withholds_all_orbitals_without_fallback(tail: str) -> None:
    result = PARSER.parse_log(HEADER + FIRST + "SCF Done: E(UHF) = -101 A.U.\n" + tail + END)
    assert result["orbital_energies"] == {}
    assert result["orbital_block"]["status"] == "HOLD_INCOMPLETE_ORBITAL_BLOCK"
    assert any("no orbital values were borrowed" in warning for warning in result["warnings"])


def test_eof_inside_otherwise_complete_block_is_not_a_closed_block() -> None:
    result = PARSER.parse_log(HEADER + FIRST + FINAL)
    assert result["orbital_energies"] == {}
    assert result["orbital_block"]["status"] == "HOLD_INCOMPLETE_ORBITAL_BLOCK"
    assert result["parser_accepted"] is False


def test_later_scf_without_population_does_not_return_earlier_orbitals() -> None:
    result = PARSER.parse_log(HEADER + FIRST + "SCF Done: E(UHF) = -101 A.U.\n" + END)
    assert result["orbital_energies"] == {}
    assert result["orbital_block"]["status"] == "NOT_OBSERVED"
    assert result["last_scf_energy_hartree"] == -101.0


def test_partial_tail_after_complete_same_scf_block_is_not_hidden() -> None:
    result = PARSER.parse_log(HEADER + FIRST + "Alpha occ. eigenvalues -- -0.3\n" + END)
    assert result["orbital_energies"] == {}
    assert result["orbital_block"]["block_count"] == 2


@pytest.mark.parametrize("scf", ["", "SCF Done: E(RHF) = -1.0 A.U.\n"])
def test_restricted_orbital_block_needs_no_invented_beta_channel(scf: str) -> None:
    result = PARSER.parse_log(scf + "Alpha occ. eigenvalues -- -0.3\nAlpha virt. eigenvalues -- 0.7\n" + END)
    assert result["orbital_energies"] == {
        "alpha_occ_hartree": [-0.3],
        "alpha_virt_hartree": [0.7],
        "alpha_homo_hartree": -0.3,
        "alpha_lumo_hartree": 0.7,
    }


@pytest.mark.parametrize("token", ["1e999", "1e-999"])
def test_selected_orbital_numeric_range_failure_remains_fail_closed(token: str) -> None:
    result = PARSER.parse_log(HEADER + FINAL.replace("0.75", token) + END)
    assert result["parser_contract_status"] == "NUMERIC_RANGE_ERROR"
    assert result["parser_accepted"] is False
    assert result["orbital_energies"] == {}

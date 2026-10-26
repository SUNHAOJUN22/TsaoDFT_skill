"""Appended synthetic logs must not lend observations to their final job."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "skills/tsao-dft-researcher/scripts/parse_gaussian.py"
FIXTURES = ROOT / "skills/tsao-dft-researcher/tests/fixtures"
spec = importlib.util.spec_from_file_location("gaussian_final_job_public", SCRIPT)
assert spec and spec.loader
parser = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = parser
spec.loader.exec_module(parser)

FINAL_EMPTY = (
    "Entering Gaussian System\n#p HF/STO-3G SP\n\nCharge = 1 Multiplicity = 2\nNormal termination of Gaussian\n"
)
FINAL_VALUES = (
    "Entering Gaussian System\n#p HF/STO-3G SP\n\nCharge = 1 Multiplicity = 2\n"
    "SCF Done: E(UHF) = -200.0 A.U.\nAlpha occ. eigenvalues -- -2.0 -1.0\n"
    "Alpha virt. eigenvalues -- 0.7 0.8\nBeta occ. eigenvalues -- -2.1 -1.1\n"
    "Beta virt. eigenvalues -- 0.75 0.85\nNormal termination of Gaussian\n"
)


def observations(result: dict[str, Any]) -> dict[str, Any]:
    # Whole-log diagnostics and context warnings may differ. Every scientific
    # field, route, status and per-job numeric count must equal the final log alone.
    return {
        name: value
        for name, value in result.items()
        if name not in {"parser_segment_count", "normal_termination_count", "warnings"}
    }


@pytest.mark.parametrize("final", [FINAL_EMPTY, FINAL_VALUES])
def test_prior_rich_job_cannot_supply_final_scientific_observations(final: str) -> None:
    first = (FIXTURES / "rich.log").read_text()
    actual = parser.parse_log(first + final)
    independent_final = parser.parse_log(final)
    assert observations(actual) == observations(independent_final)
    assert actual["parser_segment_count"] == 2
    assert actual["normal_termination_count"] == 2
    assert actual["scientific_acceptance"] == "PENDING_HUMAN_OR_CRITIC_REVIEW"


def test_final_missing_values_remain_unobserved_not_minimum_candidates() -> None:
    actual = parser.parse_log((FIXTURES / "rich.log").read_text() + FINAL_EMPTY)
    assert actual["status"] == "COMPLETED_UNCLASSIFIED"
    assert actual["last_scf_energy_hartree"] is None
    assert actual["frequency_count"] == actual["scf_energy_count"] == 0
    assert actual["orbital_energies"] == actual["thermal"] == {}
    assert actual["final_coordinates"] == actual["excited_states"] == actual["nmr_shieldings"] == []
    assert actual["spin_s2"] is actual["dipole_moment"] is None
    assert actual["optimization_completed"] is False


def test_final_orbital_values_use_literal_final_job_observations() -> None:
    actual = parser.parse_log((FIXTURES / "rich.log").read_text() + FINAL_VALUES)
    assert actual["orbital_energies"]["alpha_lumo_hartree"] == 0.7
    assert actual["orbital_energies"]["alpha_homo_hartree"] == -1.0
    assert actual["orbital_energies"]["alpha_virt_hartree"] == [0.7, 0.8]
    assert actual["last_scf_energy_hartree"] == -200.0


def test_generic_job_boundaries_match_canonical_status_boundaries() -> None:
    first = (FIXTURES / "rich.log").read_text().replace(" Entering Gaussian System, Link 0=g16\n", "")
    final = FINAL_EMPTY.replace("Entering Gaussian System\n", "")
    actual = parser.parse_log("--- JOB START ---\n" + first + "--- JOB START ---\n" + final)
    assert observations(actual) == observations(parser.parse_log(final))
    assert actual["parser_segment_count"] == 2


@pytest.mark.parametrize("prior_end", ["Error termination via Lnk1e", "SCF Done: E(HF) = 1e999 A.U."])
def test_prior_failed_or_invalid_observation_cannot_poison_independent_final_job(prior_end: str) -> None:
    prior = "Entering Gaussian System\n" + prior_end + "\n"
    actual = parser.parse_log(prior + FINAL_VALUES)
    assert observations(actual) == observations(parser.parse_log(FINAL_VALUES))
    assert actual["parser_accepted"] is True


@pytest.mark.parametrize("ending", ["", "Error termination via Lnk1e\n"])
def test_final_failed_or_truncated_job_cannot_inherit_earlier_success(ending: str) -> None:
    prior = (FIXTURES / "rich.log").read_text()
    actual = parser.parse_log(prior + "Entering Gaussian System\n" + ending)
    assert actual["parser_accepted"] is False
    assert actual["last_scf_energy_hartree"] is None
    assert actual["orbital_energies"] == {}
    assert actual["frequency_count"] == 0


def test_fatal_marker_after_success_in_same_job_remains_fatal() -> None:
    actual = parser.parse_log(FINAL_VALUES + "Error termination via Lnk1e\n")
    assert actual["parser_accepted"] is False
    assert actual["parser_contract_status"] == "FATAL"
    assert actual["parser_segment_count"] == 1
    assert actual["last_scf_energy_hartree"] == -200.0


@pytest.mark.parametrize("final,code", [(FINAL_EMPTY, 0), ("Entering Gaussian System\n", 2)])
def test_public_cli_and_written_json_share_final_job_identity(tmp_path: Path, final: str, code: int) -> None:
    source = tmp_path / "synthetic-appended.log"
    output = tmp_path / "evidence.json"
    source.write_text((FIXTURES / "rich.log").read_text() + final)
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(source), "--json", "--out", str(output)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == code
    written = json.loads(output.read_text())
    assert written == json.loads(result.stdout)
    assert written["last_scf_energy_hartree"] is None
    assert written["frequency_count"] == 0
    assert written["parser_segment_count"] == 2

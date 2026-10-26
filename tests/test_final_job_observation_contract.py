"""Synthetic parser regressions; these are not external engine receipts."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest

SCRIPTS = Path(__file__).parents[1] / "skills/tsao-dft-hpc-provenance/scripts"


def load(filename: str) -> Any:
    spec = importlib.util.spec_from_file_location("final_job_" + filename, SCRIPTS / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


parser = load("engine_parser_contract.py")
contracts = load("scientific_contracts_core_v18.py")
legacy = load("contracts_v17.py")


def cp2k_job(*, version: str = "2026.1", counts: tuple[int, ...] = (4, 7)) -> str:
    return (
        " **** **** PROGRAM STARTED AT 2026-10-25\n"
        f" CP2K| version string: CP2K {version}\n"
        + "".join(f" *** SCF run converged in {count} steps ***\n" for count in counts)
        + " ENERGY| Total FORCE_EVAL ( QS ) energy (a.u.): -1.0\n"
        " PROGRAM ENDED AT 2026-10-25\n"
    )


def parse_file(tmp_path: Path, engine: str, text: str) -> dict[str, Any]:
    path = tmp_path / "synthetic.out"
    path.write_text(text, encoding="utf-8")
    return parser.parse_engine_output(engine, path)


def test_cp2k_scf_counts_are_inner_steps_not_energy_or_outer_cycles(tmp_path: Path) -> None:
    text = cp2k_job().replace(" PROGRAM ENDED", " outer SCF loop converged in 2 iterations or 11 steps\n PROGRAM ENDED")
    result = parse_file(tmp_path, "cp2k", text)
    assert result["parser_accepted"] is True
    assert result["scf_iterations"] == 11


def test_cp2k_unknown_count_does_not_invent_zero_or_reject_explicit_convergence(tmp_path: Path) -> None:
    text = cp2k_job(counts=()).replace(" ENERGY|", " SCF run converged\n ENERGY|")
    result = parse_file(tmp_path, "cp2k", text)
    assert result["scf_iterations"] is None
    assert result["parser_accepted"] is True


def test_cp2k_partial_cycle_counts_do_not_claim_a_total(tmp_path: Path) -> None:
    text = cp2k_job(counts=(4,)).replace(" ENERGY|", " SCF run converged\n ENERGY|")
    result = parse_file(tmp_path, "cp2k", text)
    assert result["scf_iterations"] is None
    assert result["parser_accepted"] is True


def test_cp2k_final_job_excludes_old_failure_and_metrics(tmp_path: Path) -> None:
    text = "CP2K| version string: CP2K OLD\nABORT\n" + cp2k_job(counts=(4,))
    result = parse_file(tmp_path, "cp2k", text)
    assert result["parser_accepted"] is True
    assert result["engine_version"] == "CP2K 2026.1"
    assert result["job_index"] == 2
    assert result["scf_iterations"] == 4


def test_cp2k_final_truncated_job_does_not_inherit_any_old_result(tmp_path: Path) -> None:
    text = cp2k_job() + " **** PROGRAM STARTED AT 2026-10-26\nCP2K| version string: CP2K NEW\n"
    result = parse_file(tmp_path, "cp2k", text)
    assert result["parser_accepted"] is False
    assert result["normal_termination"] is False
    assert result["energy"]["value"] is None
    assert result["scf_iterations"] is None


@pytest.mark.parametrize("engine", ["vasp", "cp2k"])
def test_startup_preamble_fatal_is_not_dropped_at_version_banner(tmp_path: Path, engine: str) -> None:
    if engine == "cp2k":
        text = cp2k_job().replace(" CP2K|", " *** ABORT ***\n CP2K|")
    else:
        text = (
            "running on 4 total cores\nBRMIX: very serious problems\nvasp.6.5.1\n"
            "EDIFF is reached\nGeneral timing and accounting informations for this job\n"
        )
    result = parse_file(tmp_path, engine, text)
    assert result["parser_accepted"] is False
    assert contracts.parse_engine_output(engine, text).parser_accepted is False


def test_cp2k_program_end_alone_is_not_electronic_convergence() -> None:
    text = "CP2K| version string: CP2K 2026.1\nPROGRAM ENDED AT\n"
    assert contracts.parse_engine_output("cp2k", text).parser_accepted is False
    assert legacy.parse_termination(text.splitlines()).status != "CONVERGED"


@pytest.mark.parametrize("failure", ["SCF run NOT converged", "ABORT"])
def test_v17_failure_overrides_program_end(failure: str) -> None:
    result = legacy.parse_termination([failure, "PROGRAM ENDED AT"])
    assert result.status == "FAILED"


def test_v17_latest_job_controls_legacy_status() -> None:
    text = cp2k_job() + " PROGRAM STARTED AT 2026-10-26\nCP2K| version string: CP2K NEW\n"
    assert legacy.parse_termination(text.splitlines()).status == "INCOMPLETE"


@pytest.mark.parametrize(
    "engine,header,success",
    [
        ("vasp", "vasp 6", "EDIFF is reached\nGeneral timing and accounting informations"),
        ("cp2k", "CP2K| version 2026", "SCF run converged\nPROGRAM ENDED AT"),
    ],
)
def test_legacy_text_header_formats_still_split_appended_jobs(engine: str, header: str, success: str) -> None:
    record = contracts.parse_engine_output(engine, f"{header}\n{success}\n{header}\nunfinished")
    assert len(record.jobs) == 2
    assert record.parser_accepted is False

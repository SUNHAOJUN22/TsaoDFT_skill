"""Literal synthetic failures remain attached to their actual periodic engine job."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).parents[1]
PERIODIC = ROOT / "skills/tsao-periodic-dft-materials/scripts"
HPC = ROOT / "skills/tsao-dft-hpc-provenance/scripts"


def load(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


streaming = load(PERIODIC / "periodic_output.py", "periodic_job_failure_streaming")
mapped = load(HPC / "engine_parser_contract.py", "periodic_job_failure_mapped")

STARTS = {
    "vasp": "running on 4 total cores\n",
    "cp2k": " **** **** ****** PROGRAM STARTED AT 2026-10-25 13:00:00.000\n",
}
SUCCESS = {
    "vasp": (
        "vasp.6.4.3\nfree energy TOTEN = -10.0 eV\naborting loop because EDIFF is reached\n"
        "General timing and accounting informations for this job:\n"
    ),
    "cp2k": (
        "CP2K| version string: CP2K 2026.1\nENERGY| Total FORCE_EVAL ( QS ) energy (a.u.): -10.0\n"
        "SCF run converged in 10 steps\nPROGRAM ENDED AT 2026-10-25 12:00:00.000\n"
    ),
}


@pytest.mark.parametrize("engine", ["vasp", "cp2k"])
@pytest.mark.parametrize("newline", ["\n", "\r\n"], ids=["LF", "CRLF"])
def test_realistic_startup_version_pair_is_one_valid_job(tmp_path: Path, engine: str, newline: str) -> None:
    text = STARTS[engine] + SUCCESS[engine]
    payload = text.replace("\n", newline).encode("utf-8")
    path = tmp_path / "synthetic.out"
    path.write_bytes(payload)
    result = streaming.parse_output(engine, path)
    assert result["parser_accepted"] is True
    assert result["parser_segment_count"] == 1
    assert result["source_sha256"] == hashlib.sha256(payload).hexdigest()
    assert result["source_bytes"] == len(payload)
    if newline == "\r\n":
        assert result["source_sha256"] != hashlib.sha256(text.encode("utf-8")).hexdigest()


@pytest.mark.parametrize("engine", ["vasp", "cp2k"])
@pytest.mark.parametrize("newline", ["\n", "\r\n"], ids=["LF", "CRLF"])
def test_final_startup_fatal_cannot_be_erased_by_its_version_header(tmp_path: Path, engine: str, newline: str) -> None:
    prefix = "launcher café\n" + SUCCESS[engine]
    text = prefix + STARTS[engine] + "FATAL ERROR\n" + SUCCESS[engine].replace("-10.0", "-20.0")
    payload = text.replace("\n", newline).encode("utf-8")
    prefix_bytes = prefix.replace("\n", newline).encode("utf-8")
    path = tmp_path / "synthetic.out"
    path.write_bytes(payload)
    result = streaming.parse_output(engine, path)
    assert result["parser_accepted"] is False
    assert result["status"] == "FATAL"
    assert "FATAL_MARKER_PRESENT" in result["parser_reason_codes"]
    assert result["parser_segment_count"] == 2
    assert result["start_byte"] == len(prefix_bytes)
    assert result["start_line"] == prefix.count("\n") + 1
    assert result["energy_count"] == 1
    assert result["last_total_energy_eV"] == pytest.approx(-20.0 * (1 if engine == "vasp" else 27.211386245988))
    assert result["source_bytes"] == len(payload)
    assert result["source_sha256"] == hashlib.sha256(payload).hexdigest()
    assert result["source_complete"] is True
    assert result["scientific_acceptance"] == "PENDING"


@pytest.mark.parametrize("engine", ["vasp", "cp2k"])
def test_startup_without_a_version_is_a_new_incomplete_job(tmp_path: Path, engine: str) -> None:
    path = tmp_path / "synthetic.out"
    path.write_bytes((SUCCESS[engine] + STARTS[engine]).encode("utf-8"))
    result = streaming.parse_output(engine, path)
    assert result["parser_accepted"] is False
    assert result["last_total_energy_eV"] is None
    assert result["parser_segment_count"] == 2
    assert "NORMAL_TERMINATION_MISSING" in result["parser_reason_codes"]


@pytest.mark.parametrize("engine", ["vasp", "cp2k"])
def test_failed_prior_job_does_not_reject_an_independent_later_success(tmp_path: Path, engine: str) -> None:
    path = tmp_path / "synthetic.out"
    path.write_bytes((SUCCESS[engine] + "FATAL ERROR\n" + STARTS[engine] + SUCCESS[engine]).encode("utf-8"))
    result = streaming.parse_output(engine, path)
    assert result["parser_accepted"] is True
    assert result["parser_segment_count"] == 2
    assert result["jobs"][0]["fatal"] is True
    assert result["jobs"][1]["fatal"] is False


@pytest.mark.parametrize("failure", ["ABORT", "*** ABORT", "FATAL ERROR"])
def test_column_zero_failure_is_fatal_even_after_normal_termination(tmp_path: Path, failure: str) -> None:
    path = tmp_path / "synthetic.out"
    path.write_bytes((SUCCESS["cp2k"] + failure + "\n").encode("utf-8"))
    result = streaming.parse_output("cp2k", path)
    assert result["parser_accepted"] is False
    assert result["status"] == "FATAL"


@pytest.mark.parametrize("engine", ["vasp", "cp2k"])
def test_mapped_public_parser_also_rejects_explicit_fatal_in_final_startup(tmp_path: Path, engine: str) -> None:
    path = tmp_path / "synthetic.out"
    path.write_bytes((SUCCESS[engine] + STARTS[engine] + "FATAL ERROR\n" + SUCCESS[engine]).encode("utf-8"))
    result = mapped.parse_engine_output(engine, path)
    assert result["parser_accepted"] is False
    assert result["fatal_marker"] is not None


@pytest.mark.parametrize("engine", ["vasp", "cp2k"])
def test_public_periodic_cli_rejects_fatal_preamble(tmp_path: Path, engine: str) -> None:
    path = tmp_path / "synthetic.out"
    path.write_bytes((SUCCESS[engine] + STARTS[engine] + "FATAL ERROR\n" + SUCCESS[engine]).encode("utf-8"))
    result = subprocess.run(
        [sys.executable, str(PERIODIC / f"parse_{engine}.py"), str(path)], capture_output=True, text=True, check=False
    )
    assert result.returncode == 2
    report = json.loads(result.stdout)
    assert report["parser_accepted"] is False
    assert report["status"] == "FATAL"

"""Synthetic parser fixtures exercise numeric range before evidence is accepted."""

from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/tsao-dft-hpc-provenance/scripts/engine_parser_contract.py"
spec = importlib.util.spec_from_file_location("mmap_numeric_boundaries", SCRIPT)
assert spec is not None and spec.loader is not None
parser = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = parser
spec.loader.exec_module(parser)

LOGS = {
    "gaussian": "Gaussian 16: Revision C.01\nSCF Done: E(RB3LYP) = {value}\nNormal termination of Gaussian\n",
    "vasp": "vasp.6.4.3\nfree energy TOTEN = {value} eV\nEDIFF is reached\n"
    "General timing and accounting informations for this job\n",
    "quantum-espresso": "Program PWSCF v.7.3\n! total energy = {value} Ry\nconvergence has been achieved\nJOB DONE.\n",
    "cp2k": "CP2K| version string: 2026.1\nENERGY| Total FORCE_EVAL energy (a.u.): {value}\n"
    "SCF run converged\nPROGRAM ENDED AT\n",
}


@pytest.mark.parametrize("engine", LOGS)
@pytest.mark.parametrize("token", ["1e-400", "1e308"])
def test_mmap_parser_rejects_input_and_conversion_range(tmp_path: Path, engine: str, token: str) -> None:
    if engine == "vasp" and token == "1e308":
        token = "1e999"
    source = tmp_path / "synthetic.log"
    source.write_text(LOGS[engine].format(value=token), encoding="utf-8")
    with pytest.raises(ValueError, match=r"underflow|non-finite|range"):
        parser.parse_engine_output(engine, source)


@pytest.mark.parametrize("engine", LOGS)
@pytest.mark.parametrize("token", ["0e-999", "-0.0e-999", "5e-324"])
def test_mmap_parser_retains_real_zero_and_representable_subnormal(tmp_path: Path, engine: str, token: str) -> None:
    source = tmp_path / "synthetic.log"
    source.write_text(LOGS[engine].format(value=token), encoding="utf-8")
    result = parser.parse_engine_output(engine, source)
    value = result["energy"]["value"]
    assert math.isfinite(value)
    assert (value == 0) == (float(token) == 0)
    assert math.copysign(1.0, value) == math.copysign(1.0, float(token))
    assert result["scientific_acceptance"] == "PENDING"


def test_mmap_parser_rejects_pressure_conversion_underflow(tmp_path: Path) -> None:
    source = tmp_path / "synthetic.log"
    source.write_text(LOGS["quantum-espresso"].format(value=-10) + "P= 5e-324\n", encoding="utf-8")
    with pytest.raises(ValueError, match="range"):
        parser.parse_engine_output("quantum-espresso", source)


@pytest.mark.parametrize("token", ["1e-400", "1e999"])
def test_mmap_parser_does_not_discard_out_of_range_force_rows(tmp_path: Path, token: str) -> None:
    source = tmp_path / "synthetic.log"
    source.write_text(
        LOGS["vasp"].format(value=-10)
        + "TOTAL-FORCE (eV/Angst)\n 1 2 3 0.1 0.2 0.3\n 2 3 4 "
        + token
        + " 0.2 0.3\n total drift\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match=r"underflow|non-finite"):
        parser.parse_engine_output("vasp", source)

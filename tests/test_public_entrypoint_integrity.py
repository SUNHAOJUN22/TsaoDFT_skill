"""Synthetic entrypoint regressions; these fixtures are not engine executions."""

from __future__ import annotations

import csv
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PERIODIC = ROOT / "skills/tsao-periodic-dft-materials/scripts"
KINETICS = ROOT / "skills/tsao-dft-kinetics-multiscale/scripts"
ML = ROOT / "skills/tsao-dft-ml-active-learning/scripts"


def run(script: Path, *args: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(script), *map(str, args)], capture_output=True, text=True, check=False)


ENGINE_LOGS = {
    "qe": ("Program PWSCF v.7.3", "! total energy = {energy} Ry", "convergence has been achieved\nJOB DONE."),
    "vasp": (
        "vasp.6.4.3",
        "free energy TOTEN = {energy} eV",
        "EDIFF is reached\nGeneral timing and accounting informations for this job",
    ),
    "cp2k": (
        "CP2K| version string: 2026.1",
        "ENERGY| Total FORCE_EVAL ( QS ) energy (a.u.): {energy}",
        "SCF run converged\nPROGRAM ENDED AT",
    ),
}


@pytest.mark.parametrize("engine", ENGINE_LOGS)
def test_final_job_cannot_inherit_previous_energy(tmp_path: Path, engine: str) -> None:
    start, energy, end = ENGINE_LOGS[engine]
    source = tmp_path / "synthetic.out"
    source.write_text(f"{start}\n{energy.format(energy=-10)}\n{end}\n{start}\n{end}\n", encoding="utf-8")
    result = run(PERIODIC / f"parse_{engine}.py", source)
    assert result.returncode != 0
    report = json.loads(result.stdout)
    assert report["parser_accepted"] is False
    assert report["energy_count"] == 0


@pytest.mark.parametrize("engine", ENGINE_LOGS)
@pytest.mark.parametrize("number", ["1e999", "1e-9999"])
def test_nonrepresentable_engine_numbers_fail_without_nonfinite_json(tmp_path: Path, engine: str, number: str) -> None:
    start, energy, end = ENGINE_LOGS[engine]
    source = tmp_path / "synthetic.out"
    source.write_text(f"{start}\n{energy.format(energy=number)}\n{end}\n", encoding="utf-8")
    result = run(PERIODIC / f"parse_{engine}.py", source)
    report = json.loads(result.stdout, parse_constant=lambda value: pytest.fail(f"nonfinite JSON: {value}"))
    assert result.returncode != 0
    assert report["parser_accepted"] is False


def test_bimolecular_cli_requires_standard_and_barrier_reference(tmp_path: Path) -> None:
    source = tmp_path / "barriers.csv"
    source.write_text("delta_g_dagger_kcal_mol,molecularity\n15,2\n", encoding="utf-8")
    result = run(KINETICS / "eyring_rates.py", source, "--temperature", 298.15, "--out", tmp_path / "rate.csv")
    assert result.returncode != 0
    assert not (tmp_path / "rate.csv").exists()


def test_tst_cli_applies_standard_concentration(tmp_path: Path) -> None:
    values = []
    for concentration in (1.0, 0.1):
        source = tmp_path / "barriers.csv"
        source.write_text(
            "delta_g_dagger_kcal_mol,molecularity,standard_state,barrier_standard_state,activity_convention\n"
            f"15,2,{concentration} M,{concentration} M,a=c/c0\n",
            encoding="utf-8",
        )
        target = tmp_path / f"rate-{concentration}.csv"
        result = run(KINETICS / "eyring_rates.py", source, "--temperature", 298.15, "--out", target)
        assert result.returncode == 0, result.stdout + result.stderr
        with target.open(encoding="utf-8") as handle:
            values.append(float(next(csv.DictReader(handle))["k_tst_s-1_or_standard_state"]))
    assert values[1] / values[0] == pytest.approx(10, rel=1e-7)


def load_core():
    path = ROOT / "skills/tsao-dft-hpc-provenance/scripts/scientific_contracts_core_v18.py"
    spec = importlib.util.spec_from_file_location("entrypoint_integrity_core", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_forces_reject_pressure_units() -> None:
    core = load_core()
    with pytest.raises(ValueError):
        core.TypedQuantity("atomic_forces_full", ((1, 2, 3),), "GPa", (1, 3), "full", ("H1",))


@pytest.mark.parametrize("value", [1.0, (1, 2, 3, 4, 5, 6), ((1, 2, 3), (4, 5), (6, 7, 8, 9))])
def test_declared_stress_shape_matches_actual_structure(value: object) -> None:
    core = load_core()
    with pytest.raises(ValueError):
        core.QuantityRecord(
            "stress_tensor_full", value, "GPa", (3, 3), "full", component_convention="xx yy zz xy yz xz"
        )


def test_training_completion_is_not_validation_and_hashes_input(tmp_path: Path) -> None:
    source = tmp_path / "synthetic.csv"
    source.write_text(
        "sample_id,parent_id,x,target\n" + "".join(f"s{i},p{i},{i},{2 * i + 1}\n" for i in range(12)), encoding="utf-8"
    )
    output = tmp_path / "fit"
    result = run(
        ML / "train_ridge_baseline.py",
        source,
        "--features",
        "x",
        "--target",
        "target",
        "--group",
        "parent_id",
        "--out-dir",
        output,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    card = json.loads((output / "model-card.json").read_text(encoding="utf-8"))
    assert card["status"] == "training_completed"
    assert card["scientific_qualification"] == "UNQUALIFIED"
    assert len(card["dataset_sha256"]) == 64


def test_target_cannot_be_a_training_feature(tmp_path: Path) -> None:
    source = tmp_path / "synthetic.csv"
    source.write_text("parent_id,x,target\n" + "".join(f"p{i},{i},{i}\n" for i in range(12)), encoding="utf-8")
    result = run(
        ML / "train_ridge_baseline.py",
        source,
        "--features",
        "target",
        "--target",
        "target",
        "--group",
        "parent_id",
        "--out-dir",
        tmp_path / "fit",
    )
    assert result.returncode != 0


def test_uncertainty_entrypoint_enforces_and_applies_standard_state() -> None:
    base = ["--barrier", 15, "--uncertainty", 1, "--temperature", 298.15, "--molecularity", 2]
    assert run(KINETICS / "propagate_barrier_uncertainty.py", *base).returncode != 0
    rates = []
    for concentration in ("1 M", "0.1 M"):
        result = run(
            KINETICS / "propagate_barrier_uncertainty.py",
            *base,
            "--standard-state",
            concentration,
            "--barrier-standard-state",
            concentration,
            "--activity-convention",
            "a=c/c0",
        )
        assert result.returncode == 0, result.stdout + result.stderr
        rates.append(json.loads(result.stdout))
    for field in ("central_rate", "lower_rate", "upper_rate"):
        assert rates[1][field] / rates[0][field] == pytest.approx(10)


@pytest.mark.parametrize("engine", ENGINE_LOGS)
def test_final_job_version_and_energy_witness_are_coherent(tmp_path: Path, engine: str) -> None:
    import hashlib

    start, energy, end = ENGINE_LOGS[engine]
    source = tmp_path / "synthetic.out"
    source.write_text(
        f"{start}\n{energy.format(energy=-10)}\n{end}\n{start}\n{energy.format(energy=-20)}\n{end}\n", encoding="utf-8"
    )
    result = run(PERIODIC / f"parse_{engine}.py", source)
    assert result.returncode == 0, result.stdout
    parsed = json.loads(result.stdout)
    assert parsed["parser_segment_count"] == 2
    assert parsed["source_sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    witness = parsed["numeric_witnesses"]["last_total_energy_eV"]
    assert witness["literal"] == "-20"
    assert witness["line"] > parsed["jobs"][0]["numeric_witnesses"]["last_total_energy_eV"]["line"]
    assert parsed["source_complete"] is True

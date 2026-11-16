"""Reaction energies and TST rates must describe the declared physical states."""

from __future__ import annotations

import copy
import importlib.util
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
KINETICS = ROOT / "skills/tsao-dft-kinetics-multiscale"


def load_script(path: Path) -> Any:
    name = f"state_binding_{path.stem}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


NETWORK = load_script(KINETICS / "scripts/validate_reaction_network.py")
CLOSURE = load_script(KINETICS / "scripts/check_thermodynamic_closure.py")
TST = load_script(ROOT / "skills/tsao-dft-hpc-provenance/scripts/scientific_contracts_core_v18.py")


def network() -> dict[str, Any]:
    return yaml.safe_load((KINETICS / "examples/catalysis/network.yaml").read_text(encoding="utf-8"))


def test_accepted_network_cannot_reverse_the_species_equilibrium_direction() -> None:
    data = network()
    data["species"][1]["free_energy"] = 20.0
    data["status"] = "accepted"
    before = copy.deepcopy(data)
    errors, _ = NETWORK.validate(data)
    assert any("species free energies" in error for error in errors)
    report = CLOSURE.analyze(data, 0.05)
    assert report["ok"] is False
    assert any("species free energies" in error for error in report["errors"])
    assert data == before


def test_network_validator_checks_forward_reverse_barrier_closure() -> None:
    data = network()
    data["reactions"][0]["reverse_barrier"] = 16.0
    errors, _ = NETWORK.validate(data)
    assert any("closure error" in error for error in errors)


def weighted_network() -> dict[str, Any]:
    data = network()
    data["species"][0].update(composition={"H": 1}, free_energy=2.0)
    data["species"][1].update(composition={"H": 2}, free_energy=7.0)
    data["reactions"][0].update(
        reactants={"A": 2},
        products={"B": 1},
        reaction_free_energy=3.0,
        forward_barrier=10.0,
        reverse_barrier=7.0,
    )
    return data


def test_reaction_energy_uses_written_stoichiometry() -> None:
    data = weighted_network()
    assert NETWORK.validate(data)[0] == []
    data["reactions"][0].update(reaction_free_energy=5.0, reverse_barrier=5.0)
    assert any("species free energies" in error for error in NETWORK.validate(data)[0])


def test_element_reference_shift_preserves_the_balanced_reaction_energy() -> None:
    data = weighted_network()
    for species in data["species"]:
        species["free_energy"] += 1e6 * species["composition"]["H"]
    assert NETWORK.validate(data)[0] == []
    report = CLOSURE.analyze(data, 0.0)
    assert report["ok"] is True
    assert report["reactions"][0]["species_reaction_free_energy"] == 3.0
    assert report["reactions"][0]["expected_reverse_barrier"] == 7.0


def test_closed_cycle_cannot_create_a_nonzero_free_energy_gain() -> None:
    data = network()
    third = copy.deepcopy(data["species"][1])
    third.update(id="C", free_energy=-3.0, artifact_id="ART-C")
    data["species"].append(third)
    for identifier, reactant, product, delta in (("R2", "B", "C", -1.0), ("R3", "C", "A", 4.0)):
        reaction = copy.deepcopy(data["reactions"][0])
        reaction.update(
            id=identifier,
            reactants={reactant: 1},
            products={product: 1},
            reaction_free_energy=delta,
            reverse_barrier=15.0 - delta,
        )
        data["reactions"].append(reaction)
    assert any("R3" in error and "species free energies" in error for error in NETWORK.validate(data)[0])
    data["reactions"][2].update(reaction_free_energy=3.0, reverse_barrier=12.0)
    assert NETWORK.validate(data)[0] == []


@pytest.mark.parametrize("difference, accepted", [(0.04, True), (0.06, False)])
def test_declared_energy_tolerance_is_in_the_network_energy_unit(difference: float, accepted: bool) -> None:
    data = network()
    data["species"][1]["free_energy"] -= difference
    report = CLOSURE.analyze(data, 0.05)
    assert report["ok"] is accepted


def test_barrier_only_analysis_does_not_claim_species_energy_verification() -> None:
    data = network()
    del data["species"]
    report = CLOSURE.analyze(data, 0.05)
    assert report["ok"] is True
    assert report["species_energy_checked"] is False


def test_omitted_optional_reversibility_keeps_legacy_irreversible_network_valid() -> None:
    data = network()
    reaction = data["reactions"][0]
    for field in ("reversible", "reverse_barrier", "reaction_free_energy"):
        del reaction[field]
    assert NETWORK.validate(data)[0] == []
    report = CLOSURE.analyze(data, 0.05)
    assert report["ok"] is True
    assert report["species_energy_checked"] is True
    assert report["reactions"] == []


@pytest.mark.parametrize("invalid_state", ["missing_energy", "duplicate_id", "unknown_species", "zero_coefficient"])
def test_species_binding_cannot_ignore_an_incomplete_or_ambiguous_state_table(invalid_state: str) -> None:
    data = network()
    if invalid_state == "missing_energy":
        del data["species"][1]["free_energy"]
    elif invalid_state == "duplicate_id":
        data["species"].append(copy.deepcopy(data["species"][0]))
    elif invalid_state == "unknown_species":
        data["reactions"][0]["products"] = {"UNKNOWN": 1}
    else:
        data["reactions"][0]["products"] = {"B": 0}
    before = copy.deepcopy(data)
    report = CLOSURE.analyze(data, 0.05)
    assert report["ok"] is False
    assert report["errors"]
    assert data == before


def test_public_network_cli_rejects_species_energy_mismatch(tmp_path: Path) -> None:
    data = network()
    data["species"][1]["free_energy"] = 20.0
    path = tmp_path / "network.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    before = path.read_bytes()
    result = subprocess.run(
        [sys.executable, str(KINETICS / "scripts/validate_reaction_network.py"), str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "species free energies" in result.stdout
    assert path.read_bytes() == before


@pytest.mark.parametrize("convention", ["a=p/p0", "a=x", "a=gamma*c/c0", "unspecified"])
def test_concentration_tst_rejects_an_unsupported_activity_model(convention: str) -> None:
    with pytest.raises(TST.TSTContractError, match="activity convention"):
        standard = TST.StandardState(1.0, "M", convention)
        TST.eyring_rate(15.0, barrier_unit="kcal/mol", temperature_K=298.15, molecularity=2, standard_state=standard)


@pytest.mark.parametrize(
    "convention", ["a=c/c0", "a=c/c°", "ideal dilute activity", "dimensionless_activity_c_over_c0"]
)
def test_supported_concentration_conventions_preserve_the_rate(convention: str) -> None:
    temperature = 298.15
    barrier = 15.0 * 4184.0
    result = TST.eyring_rate(
        barrier,
        barrier_unit="J/mol",
        temperature_K=temperature,
        molecularity=2,
        standard_state=TST.StandardState(0.1, "M", convention),
    )
    expected = (
        (1.380649e-23 * temperature / 6.62607015e-34) * math.exp(-barrier / (8.31446261815324 * temperature)) / 0.1
    )
    assert result.value == pytest.approx(expected, rel=1e-13)


def test_explicit_barrier_reference_conversion_preserves_physical_bimolecular_rate() -> None:
    temperature = 298.15
    original = 15.0 * 4184.0
    concentration_ratio = 0.1
    converted = original - 8.31446261815324 * temperature * math.log(concentration_ratio)
    rates = [
        TST.eyring_rate(
            barrier,
            barrier_unit="J/mol",
            temperature_K=temperature,
            molecularity=2,
            standard_state=TST.StandardState(concentration, "M", "a=c/c0"),
        ).value
        for barrier, concentration in ((original, 1.0), (converted, 0.1))
    ]
    assert rates[0] == pytest.approx(rates[1], rel=1e-13)

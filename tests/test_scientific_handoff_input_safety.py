"""Reject ambiguous scientific inputs and preserve source evidence on handoff failure."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
KINETICS = ROOT / "skills/tsao-dft-kinetics-multiscale"
NETWORK = (KINETICS / "examples/catalysis/network.yaml").read_text(encoding="utf-8")
ENERGY = (
    "quantity: energy_difference\nterms:\n"
    "  - coefficient: 1\n    method_fingerprint: PBE\n"
    "  - coefficient: -1\n    method_fingerprint: PBE\n"
)
COMMANDS = (
    ("tsao-periodic-dft-materials", "check_energy_compatibility.py", ENERGY),
    ("tsao-dft-kinetics-multiscale", "check_thermodynamic_closure.py", NETWORK),
    ("tsao-dft-kinetics-multiscale", "validate_reaction_network.py", NETWORK),
    ("tsao-dft-kinetics-multiscale", "export_cantera_handoff.py", NETWORK),
)


def run_script(script: Path, source: Path, output: Path) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(script), str(source)]
    if script.name == "export_cantera_handoff.py":
        command.extend(["--out", str(output)])
    return subprocess.run(command, capture_output=True, text=True, check=False)


def duplicate_input(text: str) -> str:
    if "method_fingerprint:" in text:
        return text.replace("coefficient: -1\n", "coefficient: -1\n    method_fingerprint: B3LYP\n")
    return text.replace("reverse_barrier: 17.0", "reverse_barrier: 1.0\n    reverse_barrier: 17.0")


@pytest.mark.parametrize("skill,script,text", COMMANDS)
@pytest.mark.parametrize("malformation", ["duplicate", "underflow"])
def test_scientific_clis_reject_ambiguous_yaml_before_acceptance(
    tmp_path: Path, skill: str, script: str, text: str, malformation: str
) -> None:
    source = tmp_path / "source.yaml"
    payload = duplicate_input(text) if malformation == "duplicate" else text + "declared_precision: 1.0e-400\n"
    source.write_text(payload, encoding="utf-8")
    output = tmp_path / "handoff.yaml"
    result = run_script(ROOT / "skills" / skill / "scripts" / script, source, output)
    assert result.returncode == 1, result.stdout + result.stderr
    assert json.loads(result.stdout)["ok"] is False
    assert malformation in result.stdout
    assert "Traceback" not in result.stderr
    assert source.read_text(encoding="utf-8") == payload
    assert not output.exists()


@pytest.mark.parametrize("alias", ["same-path", "dotdot", "symlink", "hardlink"])
def test_cantera_export_rejects_input_aliases_without_changing_source(tmp_path: Path, alias: str) -> None:
    source = tmp_path / "network.yaml"
    source.write_text(NETWORK, encoding="utf-8")
    original = source.read_bytes()
    output = source
    if alias == "dotdot":
        (tmp_path / "nested").mkdir()
        output = tmp_path / "nested/../network.yaml"
    elif alias in {"symlink", "hardlink"}:
        output = tmp_path / "alias.yaml"
        try:
            if alias == "symlink":
                output.symlink_to(source)
            else:
                os.link(source, output)
        except OSError as exc:
            pytest.skip(f"{alias} is unavailable: {exc}")
    result = run_script(KINETICS / "scripts/export_cantera_handoff.py", source, output)
    assert result.returncode == 1
    assert "must not replace" in result.stdout
    assert source.read_bytes() == original
    assert output.read_bytes() == original


@pytest.mark.parametrize("invalid", ["empty", "malformed", "unbalanced"])
@pytest.mark.parametrize("existing_output", [False, True])
def test_cantera_export_validates_before_publishing(tmp_path: Path, invalid: str, existing_output: bool) -> None:
    source = tmp_path / "network.yaml"
    payload = {
        "empty": "{}\n",
        "malformed": "reactions: [\n",
        "unbalanced": NETWORK.replace("products: {B: 1}", "products: {B: 2}"),
    }[invalid]
    source.write_text(payload, encoding="utf-8")
    output = tmp_path / "cantera.yaml"
    if existing_output:
        output.write_bytes(b"previous reviewed handoff\n")
    result = run_script(KINETICS / "scripts/export_cantera_handoff.py", source, output)
    assert result.returncode == 1
    assert json.loads(result.stdout)["ok"] is False
    assert "Traceback" not in result.stderr
    assert source.read_text(encoding="utf-8") == payload
    if existing_output:
        assert output.read_bytes() == b"previous reviewed handoff\n"
    else:
        assert not output.exists()
    assert not list(tmp_path.glob(".cantera.yaml.*.tmp"))


def test_cantera_export_publishes_valid_handoff_without_modifying_source(tmp_path: Path) -> None:
    source = tmp_path / "network.yaml"
    source.write_text(NETWORK, encoding="utf-8")
    original = source.read_bytes()
    output = tmp_path / "new-directory/handoff.yaml"
    result = run_script(KINETICS / "scripts/export_cantera_handoff.py", source, output)
    assert result.returncode == 0, result.stdout + result.stderr
    document = yaml.safe_load(output.read_text(encoding="utf-8"))
    assert document["runnable_cantera_mechanism"] is False
    assert document["review_required"] is True
    assert document["validation_warnings"] == []
    assert document["reactions"][0]["rate_handoff"]["reverse_barrier"] == 17.0
    assert source.read_bytes() == original
    assert not list(output.parent.glob(".handoff.yaml.*.tmp"))


def test_cantera_export_failed_publication_keeps_destination(tmp_path: Path) -> None:
    source = tmp_path / "network.yaml"
    source.write_text(NETWORK, encoding="utf-8")
    output = tmp_path / "handoff.yaml"
    output.mkdir()
    marker = output / "keep.txt"
    marker.write_bytes(b"retained")
    result = run_script(KINETICS / "scripts/export_cantera_handoff.py", source, output)
    assert result.returncode == 1
    assert json.loads(result.stdout)["ok"] is False
    assert marker.read_bytes() == b"retained"
    assert source.read_text(encoding="utf-8") == NETWORK
    assert not list(tmp_path.glob(".handoff.yaml.*.tmp"))


@pytest.mark.parametrize("skill,script,text", COMMANDS)
def test_copy_installed_scientific_clis_use_the_canonical_decoder(
    tmp_path: Path, skill: str, script: str, text: str
) -> None:
    target = tmp_path / "skills"
    installation = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/install.py"),
            "--target",
            str(target),
            "--skill",
            skill,
            "--method",
            "copy",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert installation.returncode == 0, installation.stdout + installation.stderr
    assert not (target / "tsao-dft-hpc-provenance").exists()
    installed_script = target / skill / "scripts" / script
    canonical = ROOT / "skills/tsao-dft-hpc-provenance/scripts/benchmark_contract.py"
    assert (installed_script.parent / "_shared/benchmark_contract.py").read_bytes() == canonical.read_bytes()
    source = tmp_path / "input.yaml"
    output = tmp_path / "handoff.yaml"
    source.write_text(text, encoding="utf-8")
    valid = run_script(installed_script, source, output)
    assert valid.returncode == 0, valid.stdout + valid.stderr
    previous_output = output.read_bytes() if output.exists() else None
    source.write_text(duplicate_input(text), encoding="utf-8")
    invalid = run_script(installed_script, source, output)
    assert invalid.returncode == 1
    assert json.loads(invalid.stdout)["ok"] is False
    assert "duplicate" in invalid.stdout
    assert (output.read_bytes() if output.exists() else None) == previous_output

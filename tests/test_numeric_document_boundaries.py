"""Synthetic malformed-input checks, never evidence of a real DFT execution."""

from __future__ import annotations

import importlib.util
import json
import math
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
HPC = ROOT / "skills/tsao-dft-hpc-provenance/scripts"
GAUSSIAN = ROOT / "skills/tsao-dft-researcher/scripts/parse_gaussian.py"


def load(name: str):
    if str(HPC) not in sys.path:
        sys.path.insert(0, str(HPC))
    spec = importlib.util.spec_from_file_location("numeric_boundaries_" + name, HPC / (name + ".py"))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


READERS = {
    "campaign": load("compute_campaign_contract").load_mapping,
    "benchmark": load("benchmark_contract").load_json_mapping,
    "qualification": load("qualify_compute_campaign").load_json,
    "engine-capability": load("engine_capability").load_mapping,
    "benchmark-bridge": load("benchmark_bridge").load_mapping,
    "trust-boundary": load("trust_boundary").load_json,
    "evidence-json": load("performance_evidence").read_document,
    "evidence-jsonl": load("performance_evidence").load_records,
}


@pytest.mark.parametrize("reader", READERS)
@pytest.mark.parametrize("token", ["1e-400", "-1e-400", "1e999", "NaN"])
def test_public_evidence_readers_reject_unrepresentable_numbers(tmp_path: Path, reader: str, token: str) -> None:
    source = tmp_path / ("record.jsonl" if reader.endswith("jsonl") else "record.json")
    source.write_text('{"scientific":{"energy":' + token + "}}\n", encoding="utf-8")
    with pytest.raises(ValueError, match=r"underflow|non-finite"):
        READERS[reader](source)


@pytest.mark.parametrize("reader", READERS)
@pytest.mark.parametrize(
    "payload",
    [
        '{"state":"UNQUALIFIED","state":"QUALIFIED_FOR_REVIEW"}',
        '{"scientific":{"energy":1,"energy":2}}',
        '{"energy":1,"\\u0065nergy":2}',
    ],
)
def test_public_evidence_readers_reject_duplicate_keys(tmp_path: Path, reader: str, payload: str) -> None:
    source = tmp_path / ("record.jsonl" if reader.endswith("jsonl") else "record.json")
    source.write_text(payload + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate"):
        READERS[reader](source)


@pytest.mark.parametrize("reader", READERS)
@pytest.mark.parametrize("token", ["0e-9999", "-0.000e-9999", "5e-324", "-5e-324"])
def test_public_evidence_readers_preserve_zeros_subnormals_and_integer_values(
    tmp_path: Path, reader: str, token: str
) -> None:
    source = tmp_path / ("record.jsonl" if reader.endswith("jsonl") else "record.json")
    source.write_text('{"value":' + token + ',"count":9007199254740993}\n', encoding="utf-8")
    result = READERS[reader](source)
    record = result[0] if reader.endswith("jsonl") else result
    assert record["value"] == float(token)
    assert math.copysign(1.0, record["value"]) == math.copysign(1.0, float(token))
    assert type(record["count"]) is int and record["count"] == 9007199254740993


def gaussian_log(energy: str = "-10", extra: str = "") -> str:
    return (
        "Entering Gaussian System\nGaussian 16: Revision C.01\n #p B3LYP/6-31G(d) SP\n\n"
        "Charge = 0 Multiplicity = 1\nSCF Done: E(RB3LYP) = "
        + energy
        + " A.U.\n"
        + extra
        + "\nNormal termination of Gaussian\n"
    )


@pytest.mark.parametrize("token", ["1e-400", "1e999"])
@pytest.mark.parametrize("field", ["energy", "frequency", "orbital", "coordinates"])
def test_gaussian_actual_cli_rejects_unrepresentable_observables(tmp_path: Path, field: str, token: str) -> None:
    additions = {
        "energy": "",
        "frequency": "Frequencies -- " + token + " 100.0 200.0\n",
        "orbital": "Alpha occ. eigenvalues -- " + token + "\n",
        "coordinates": "Standard orientation:\n -----------\n Center Atomic Type X Y Z\n -----------\n"
        "1 1 0 " + token + " 0.0 0.0\n -----------\n",
    }
    source = tmp_path / "synthetic.log"
    source.write_text(gaussian_log(token if field == "energy" else "-10", additions[field]), encoding="utf-8")
    result = subprocess.run([sys.executable, str(GAUSSIAN), str(source), "--json"], capture_output=True, text=True)
    report = json.loads(result.stdout, parse_constant=lambda value: pytest.fail("non-finite JSON: " + value))
    assert result.returncode != 0
    assert report["parser_accepted"] is False
    assert "NUMERIC_RANGE_ERROR" in report["parser_reason_codes"]


@pytest.mark.parametrize("token", ["0e-9999", "-0.0e-9999", "5e-324", "-5e-324"])
def test_gaussian_actual_cli_preserves_legitimate_float_boundaries(tmp_path: Path, token: str) -> None:
    source = tmp_path / "synthetic.log"
    source.write_text(gaussian_log(token), encoding="utf-8")
    result = subprocess.run([sys.executable, str(GAUSSIAN), str(source), "--json"], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert report["last_scf_energy_hartree"] == float(token)
    assert report["scientific_acceptance"] == "PENDING_HUMAN_OR_CRITIC_REVIEW"


@pytest.mark.parametrize("suffix", ["json", "yaml"])
@pytest.mark.parametrize("token", ["1.0e-400", "-1.0e-400"])
def test_campaign_actual_cli_rejects_underflowed_tolerance(tmp_path: Path, suffix: str, token: str) -> None:
    campaign = yaml.safe_load((HPC.parent / "templates/compute-qualification-campaign.yaml").read_text())
    campaign["numerical_tolerances"]["energy_ev"]["absolute"] = "TOKEN"
    payload = json.dumps(campaign) if suffix == "json" else yaml.safe_dump(campaign)
    payload = payload.replace('"TOKEN"', token).replace("TOKEN", token)
    source = tmp_path / ("campaign." + suffix)
    source.write_text(payload, encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(HPC / "qualify_compute_campaign.py"), str(source)], capture_output=True, text=True
    )
    report = json.loads(result.stdout)
    assert result.returncode != 0
    assert report["ok"] is False
    assert report["state"] == "UNQUALIFIED"
    assert "underflow" in result.stdout


@pytest.mark.parametrize("token", ["+1e-400", "+1e999", "nan", "inf", "-inf"])
def test_csv_numeric_fallback_cannot_bypass_finite_range(tmp_path: Path, token: str) -> None:
    source = tmp_path / "evidence.csv"
    source.write_text("scientific.results.energy_ev\n" + token + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match=r"underflow|non-finite"):
        READERS["evidence-jsonl"](source)


@pytest.mark.parametrize("token", ["NaN", "Infinity", "-Infinity", "*****"])
def test_gaussian_explicit_invalid_scf_number_cannot_be_ignored(tmp_path: Path, token: str) -> None:
    source = tmp_path / "synthetic.log"
    source.write_text(gaussian_log(token), encoding="utf-8")
    result = subprocess.run([sys.executable, str(GAUSSIAN), str(source), "--json"], capture_output=True, text=True)
    report = json.loads(result.stdout)
    assert result.returncode != 0
    assert report["parser_accepted"] is False
    assert "NUMERIC_RANGE_ERROR" in report["parser_reason_codes"]


@pytest.mark.parametrize(
    ("token", "expected"),
    [("+0e-999", 0.0), ("+5e-324", 5e-324), ("pending", "pending"), ("1.2.3", "1.2.3"), ("+42", 42)],
)
def test_csv_numeric_fallback_preserves_valid_numbers_and_labels(tmp_path: Path, token: str, expected: object) -> None:
    source = tmp_path / "evidence.csv"
    source.write_text("value\n" + token + "\n", encoding="utf-8")
    assert READERS["evidence-jsonl"](source)[0]["value"] == expected

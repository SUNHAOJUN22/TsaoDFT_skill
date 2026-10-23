"""Synthetic YAML regressions; parser acceptance is not scientific qualification."""

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


def load(name: str):
    if str(HPC) not in sys.path:
        sys.path.insert(0, str(HPC))
    spec = importlib.util.spec_from_file_location("yaml_boundaries_" + name, HPC / (name + ".py"))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


READERS = {
    "bridge": load("benchmark_bridge").load_mapping,
    "capability": load("engine_capability").load_mapping,
    "evidence": load("performance_evidence").read_document,
    "policy": load("performance_evidence").load_policy,
    "trust-boundary": load("trust_boundary").load_yaml,
}


@pytest.mark.parametrize("reader", READERS)
@pytest.mark.parametrize("token", ["1.0e-400", "-1.0e-400", "1_0.0e-400", "1.0e+999", ".inf", "-.inf", ".nan"])
def test_yaml_readers_reject_nonfinite_and_nonzero_underflow(tmp_path: Path, reader: str, token: str) -> None:
    source = tmp_path / "document.yaml"
    source.write_text("scientific:\n  energy: " + token + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match=r"underflow|non-finite"):
        READERS[reader](source)


@pytest.mark.parametrize("reader", READERS)
@pytest.mark.parametrize(
    "text",
    [
        "parser_accepted: false\nparser_accepted: true\n",
        "scientific:\n  energy: 1\n  energy: 2\n",
        'energy: 1\n"\\u0065nergy": 2\n',
        "defaults: &base {energy: 1}\nscientific:\n  <<: *base\n  <<: *base\n",
        "scientific:\n  <<: {energy: 1, energy: 2}\n",
        '= : first\n"=": second\n',
    ],
)
def test_yaml_readers_reject_explicit_duplicates_before_merging(tmp_path: Path, reader: str, text: str) -> None:
    source = tmp_path / "document.yml"
    source.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate"):
        READERS[reader](source)


@pytest.mark.parametrize("reader", READERS)
@pytest.mark.parametrize("token", ["0.0e-9999", "-0.000e-9999", "5.0e-324", "-5.0e-324", "1_024.0", "0:0.0"])
def test_yaml_preserves_zero_subnormals_integer_and_quoted_tokens(tmp_path: Path, reader: str, token: str) -> None:
    source = tmp_path / "document.yaml"
    source.write_text("value: " + token + '\ncount: 9007199254740993\nlabel: "1.0e-400"\n', encoding="utf-8")
    expected = yaml.safe_load(source.read_text())
    result = READERS[reader](source)
    assert result == expected
    assert math.copysign(1.0, result["value"]) == math.copysign(1.0, expected["value"])
    assert type(result["count"]) is int


@pytest.mark.parametrize("reader", READERS)
def test_yaml_merge_priority_explicit_override_and_shared_aliases_remain_valid(tmp_path: Path, reader: str) -> None:
    source = tmp_path / "document.yaml"
    text = (
        "first: &first {energy: 1, force: 2}\n"
        "second: &second {energy: 3, stress: 4}\n"
        "overridden: &overridden\n  <<: [*first, *second]\n  force: 5\n"
        "reused:\n  <<: *overridden\n  stress: 6\n"
        'literal:\n  <<: *first\n  "<<": label\n  =: equation\n'
    )
    source.write_text(text, encoding="utf-8")
    result = READERS[reader](source)
    assert result == yaml.safe_load(text)
    assert result["overridden"] == {"energy": 1, "force": 5, "stress": 4}
    assert result["reused"] == {"energy": 1, "force": 5, "stress": 6}


@pytest.mark.parametrize("reader", READERS)
def test_yaml_invalid_mapping_keys_fail_without_acceptance(tmp_path: Path, reader: str) -> None:
    source = tmp_path / "document.yaml"
    source.write_text("? [energy, force]\n: 1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="hashable"):
        READERS[reader](source)


@pytest.mark.parametrize("malformation", ["duplicate", "underflow"])
def test_capability_cli_rejects_ambiguous_yaml_template(tmp_path: Path, malformation: str) -> None:
    text = (HPC.parent / "templates/vasp-engine-capability.yaml").read_text(encoding="utf-8")
    if malformation == "duplicate":
        text = text.replace("engine: vasp", "engine: unsupported\nengine: vasp")
    else:
        text = text.replace("  source_kind: declared", "  source_kind: declared\n  measured_precision: 1.0e-400")
    source = tmp_path / "capability.yaml"
    source.write_text(text, encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(HPC / "engine_capability.py"), str(source), "--json"], capture_output=True, text=True
    )
    report = json.loads(result.stdout)
    assert result.returncode != 0
    assert report["ok"] is False
    assert report["state"] == "UNQUALIFIED"
    assert malformation in result.stdout


@pytest.mark.parametrize("malformation", ["duplicate", "underflow"])
def test_benchmark_cli_rejects_yaml_before_losing_negative_values(tmp_path: Path, malformation: str) -> None:
    text = (HPC.parent / "templates/benchmark-result.yaml").read_text(encoding="utf-8")
    if malformation == "duplicate":
        text = text.replace("  wall_time_s: 1.0", "  wall_time_s: -1.0\n  wall_time_s: 1.0")
    else:
        text = text.replace("  cpu_time_s: 0.0", "  cpu_time_s: -1.0e-400")
    source = tmp_path / "benchmark.yaml"
    source.write_text(text, encoding="utf-8")
    output = tmp_path / "records.json"
    result = subprocess.run(
        [
            sys.executable,
            str(HPC / "validate_benchmark_result.py"),
            str(source),
            "--schema",
            str(HPC.parent / "templates/benchmark-result.schema.json"),
            "--records-out",
            str(output),
        ],
        capture_output=True,
        text=True,
    )
    report = json.loads(result.stdout)
    assert result.returncode != 0
    assert report["ok"] is False and report["valid_records"] == 0
    assert report["failures"][0]["stage"] == "read"
    assert malformation in result.stdout
    assert not output.exists()


@pytest.mark.parametrize("malformation", ["duplicate", "underflow"])
def test_bridge_cli_rejects_yaml_before_writing_an_accepted_record(tmp_path: Path, malformation: str) -> None:
    parsed = "engine_version: 6.5.1\nparser_accepted: true\nnormal_termination: true\nelapsed_time_s: 1.0\nenergy:\n  value: -10.0\n"
    if malformation == "duplicate":
        parsed = parsed.replace("parser_accepted: true", "parser_accepted: false\nparser_accepted: true")
    else:
        parsed = parsed.replace("value: -10.0", "value: 1.0e-400")
    source = tmp_path / "parser.yaml"
    source.write_text(parsed, encoding="utf-8")
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text(
        "input: INCAR\nexecutable: vasp_std\nsite_id: SITE-A\nbuild_fingerprint_id: BUILD-1\n", encoding="utf-8"
    )
    method = tmp_path / "method.yaml"
    method.write_text(
        "method_fingerprint_id: MF-1\nmodel_chemistry:\n  method: PBE\n  basis_or_pseudopotential: POTCAR-HASH\n",
        encoding="utf-8",
    )
    runtime = tmp_path / "runtime.txt"
    runtime.write_text("hardware_fingerprint_id=HW-A\nrun_id=RUN-1\n", encoding="utf-8")
    (tmp_path / "OUTCAR").write_text("synthetic parser fixture\n", encoding="utf-8")
    (tmp_path / "INCAR").write_text("ENCUT=500\n", encoding="utf-8")
    output = tmp_path / "record.json"
    result = subprocess.run(
        [
            sys.executable,
            str(HPC / "build_benchmark_result_from_vasp.py"),
            str(source),
            str(manifest),
            str(method),
            "--artifact-root",
            str(tmp_path),
            "--output-artifact",
            "OUTCAR",
            "--candidate-id",
            "cpu-reference",
            "--role",
            "scientific-reference",
            "--repeat-index",
            "1",
            "--runtime",
            str(runtime),
            "--out",
            str(output),
        ],
        capture_output=True,
        text=True,
    )
    report = json.loads(result.stdout)
    assert result.returncode != 0 and report["ok"] is False
    assert malformation in result.stdout
    assert not output.exists()

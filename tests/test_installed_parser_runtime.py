"""Selected copy-installed Skills retain their own audited parser runtime closure."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
RUNTIME = ROOT / "skills/tsao-dft-hpc-provenance/scripts"


@pytest.mark.parametrize(
    "skill,script,fixture,files",
    [
        (
            "tsao-periodic-dft-materials",
            "parse_cp2k.py",
            "examples/engine-adapters/cp2k/si.out",
            ["engine_scan_core.py"],
        ),
        (
            "tsao-periodic-dft-materials",
            "parse_vasp.py",
            "examples/engine-adapters/vasp/OUTCAR",
            ["engine_scan_core.py"],
        ),
        (
            "tsao-dft-researcher",
            "parse_gaussian.py",
            "tests/fixtures/rich.log",
            [
                "engine_parser_contract_v4.py",
                "_load_v18_core.py",
                "scientific_contracts_core_v18.py",
                "engine_scan_core.py",
            ],
        ),
    ],
)
def test_selected_skill_copy_runs_without_a_sibling_skill(
    tmp_path: Path, skill: str, script: str, fixture: str, files: list[str]
) -> None:
    target = tmp_path / "isolated-agent-skills"
    environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    install = subprocess.run(
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
        env=environment,
        check=False,
    )
    assert install.returncode == 0, install.stdout + install.stderr
    assert not (target / "tsao-dft-hpc-provenance").exists()
    installed = target / skill
    source = installed / fixture
    command = [sys.executable, str(installed / "scripts" / script), str(source)]
    if script == "parse_gaussian.py":
        command.append("--json")
    run = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True, env=environment, check=False)
    assert run.returncode == 0, run.stdout + run.stderr
    assert json.loads(run.stdout)["parser_accepted"] is True
    for name in files:
        bundled = installed / "scripts/_shared" / name
        assert hashlib.sha256(bundled.read_bytes()).digest() == hashlib.sha256((RUNTIME / name).read_bytes()).digest()
    marker = json.loads((target / ".tsao-skill-ownership" / f"{skill}.json").read_text())
    assert marker["method"] == "copy"
    assert marker["runtime_dependencies"] == {
        f"scripts/_shared/{name}": hashlib.sha256((RUNTIME / name).read_bytes()).hexdigest() for name in files
    }

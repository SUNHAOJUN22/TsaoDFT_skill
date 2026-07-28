#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(relative: str, old: str, new: str) -> None:
    path = ROOT / relative
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{relative}: expected one occurrence, found {count}: {old[:100]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


replace_once(
    "scripts/run_bandit.py",
    '''        if not all(isinstance(value, str) and value.strip() for value in (path_value, test_id, reason)):
            raise ValueError(f"Bandit allowlist entry[{index}] requires path, test_id and reason")
        key = (path_value, test_id)
''',
    '''        if not isinstance(path_value, str) or not path_value.strip():
            raise ValueError(f"Bandit allowlist entry[{index}] requires a non-empty path")
        if not isinstance(test_id, str) or not test_id.strip():
            raise ValueError(f"Bandit allowlist entry[{index}] requires a non-empty test_id")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError(f"Bandit allowlist entry[{index}] requires a non-empty reason")
        key = (path_value, test_id)
''',
)

replace_once(
    "skills/tsao-dft-catalysis-profile/scripts/build_coordination_campaign.py",
    "    rows = []\n",
    "    rows: list[dict[str, object]] = []\n",
)

replace_once(
    "skills/tsao-dft-hpc-provenance/scripts/generate_job_array.py",
    "from pathlib import Path\n",
    "from pathlib import Path\nfrom typing import Any\n",
)
replace_once(
    "skills/tsao-dft-hpc-provenance/scripts/generate_job_array.py",
    '''def task_record(campaign: dict, base: dict, task: dict) -> dict:
    merged = dict(base)
    merged.update({key: value for key, value in task.items() if key != "task_id"})
    record = {
        "task_id": str(task["task_id"]),
        "workdir": str(merged["workdir"]),
        "command": engine_command(merged),
        "environment": {},
    }
    if (base.get("scratch") or {}).get("path"):
        scratch = Path(str(campaign["scratch_root"])) / str(task["task_id"])
        record["scratch_path"] = str(scratch)
        if base.get("engine") == "gaussian":
            record["environment"]["GAUSS_SCRDIR"] = str(scratch)
    return record
''',
    '''def task_record(campaign: dict[str, Any], base: dict[str, Any], task: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = dict(base)
    merged.update({key: value for key, value in task.items() if key != "task_id"})
    environment: dict[str, str] = {}
    record: dict[str, Any] = {
        "task_id": str(task["task_id"]),
        "workdir": str(merged["workdir"]),
        "command": engine_command(merged),
        "environment": environment,
    }
    if (base.get("scratch") or {}).get("path"):
        scratch = Path(str(campaign["scratch_root"])) / str(task["task_id"])
        record["scratch_path"] = str(scratch)
        if base.get("engine") == "gaussian":
            environment["GAUSS_SCRDIR"] = str(scratch)
    return record
''',
)

replace_once(
    "skills/tsao-dft-kinetics-multiscale/scripts/validate_reaction_network.py",
    "def side_balance(side: dict, species: dict, key: str) -> dict:\n    out = {}\n",
    "def side_balance(side: dict, species: dict, key: str) -> dict[str, float]:\n    out: dict[str, float] = {}\n",
)

replace_once(
    "skills/tsao-dft-ml-active-learning/scripts/validate_dft_dataset.py",
    "from pathlib import Path\n",
    "from pathlib import Path\nfrom typing import Any\n",
)
replace_once(
    "skills/tsao-dft-ml-active-learning/scripts/validate_dft_dataset.py",
    "def load_rows(path: Path):\n",
    "def load_rows(path: Path) -> list[dict[str, str]]:\n",
)
replace_once(
    "skills/tsao-dft-ml-active-learning/scripts/validate_dft_dataset.py",
    "def canonical_rows_sha256(rows: list[dict], stream_threshold: int = STREAM_HASH_ROW_THRESHOLD) -> str:\n",
    "def canonical_rows_sha256(rows: list[dict[str, str]], stream_threshold: int = STREAM_HASH_ROW_THRESHOLD) -> str:\n",
)
replace_once(
    "skills/tsao-dft-ml-active-learning/scripts/validate_dft_dataset.py",
    '''def validate(rows: list[dict], cfg: dict) -> tuple[list[str], list[str], dict]:
    errors = []
    warnings = []
''',
    '''def validate(
    rows: list[dict[str, str]], cfg: dict[str, Any]
) -> tuple[list[str], list[str], dict[str, Any]]:
    errors: list[str] = []
    warnings: list[str] = []
''',
)
replace_once(
    "skills/tsao-dft-ml-active-learning/scripts/validate_dft_dataset.py",
    '''    fingerprints = {row.get(fingerprint) for row in rows if row.get(fingerprint)} if fingerprint in fields else set()
    fidelities = {row.get(fidelity) for row in rows if row.get(fidelity)} if fidelity in fields else set()
''',
    '''    fingerprints: set[str] = (
        {value for row in rows if (value := row.get(fingerprint))} if fingerprint in fields else set()
    )
    fidelities: set[str] = {value for row in rows if (value := row.get(fidelity))} if fidelity in fields else set()
''',
)
replace_once(
    "skills/tsao-dft-ml-active-learning/scripts/validate_dft_dataset.py",
    "    signatures = {}\n",
    "    signatures: dict[tuple[tuple[str, str], ...], list[int]] = {}\n",
)
replace_once(
    "skills/tsao-dft-ml-active-learning/scripts/validate_dft_dataset.py",
    '''    leakage = []
    if split in fields:
        group_splits = {}
        for row in rows:
            group_splits.setdefault(row.get(parent), set()).add(row.get(split))
        leakage = [(group, sorted(values)) for group, values in group_splits.items() if len(values - {None, ""}) > 1]
''',
    '''    leakage: list[tuple[str | None, list[str]]] = []
    if split in fields:
        group_splits: dict[str | None, set[str | None]] = {}
        for row in rows:
            group_splits.setdefault(row.get(parent), set()).add(row.get(split))
        leakage = [
            (group, sorted(str(value) for value in values if value not in {None, ""}))
            for group, values in group_splits.items()
            if len(values - {None, ""}) > 1
        ]
''',
)

replace_once(
    "skills/tsao-dft-researcher/scripts/validate_figure_manifest.py",
    '''                    vmin, vmax = params.get("esp_min"), params.get("esp_max")
                    numeric_scale = isinstance(vmin, (int, float)) and isinstance(vmax, (int, float))
                    if numeric_scale and not vmin < 0 < vmax:
                        errors.append(f"{pwhere}: ESP scale must cross zero")
                    if numeric_scale and not math.isclose(
                        abs(float(vmin)), abs(float(vmax)), rel_tol=1e-6, abs_tol=1e-12
                    ):
                        errors.append(f"{pwhere}: ESP comparison scale must be symmetric")
''',
    '''                    vmin, vmax = params.get("esp_min"), params.get("esp_max")
                    if isinstance(vmin, (int, float)) and isinstance(vmax, (int, float)):
                        if not vmin < 0 < vmax:
                            errors.append(f"{pwhere}: ESP scale must cross zero")
                        if not math.isclose(abs(vmin), abs(vmax), rel_tol=1e-6, abs_tol=1e-12):
                            errors.append(f"{pwhere}: ESP comparison scale must be symmetric")
''',
)

replace_once(
    "skills/tsao-dft-researcher/scripts/build_energy_profile.py",
    '''        for row in reader:
            label = row.get("label")
            energy_text = row.get(args.column)
''',
    '''        for source_row in reader:
            label = source_row.get("label")
            energy_text = source_row.get(args.column)
''',
)
replace_once(
    "skills/tsao-dft-researcher/scripts/build_energy_profile.py",
    '''        for row in rows:
            writer.writerow(
                {
                    "label": row["label"],
                    args.column: row["energy"],
                    "relative_kcal_mol": f"{row['relative_kcal_mol']:.4f}",
                }
            )
''',
    '''        for energy_row in rows:
            writer.writerow(
                {
                    "label": energy_row["label"],
                    args.column: energy_row["energy"],
                    "relative_kcal_mol": f"{energy_row['relative_kcal_mol']:.4f}",
                }
            )
''',
)

replace_once(
    "skills/tsao-periodic-dft-materials/scripts/preflight_vasp.py",
    "from pathlib import Path\n",
    "from pathlib import Path\nfrom typing import TypedDict\n",
)
replace_once(
    "skills/tsao-periodic-dft-materials/scripts/preflight_vasp.py",
    "\n\ndef parse_incar(path: Path) -> dict[str, str]:\n",
    '''

class PoscarData(TypedDict):
    comment: str
    scale: float
    lattice_vectors: list[list[float]]
    species: list[str]
    counts: list[int]
    atom_count: int
    selective_dynamics: bool
    coordinate_mode: str


def parse_incar(path: Path) -> dict[str, str]:
''',
)
replace_once(
    "skills/tsao-periodic-dft-materials/scripts/preflight_vasp.py",
    "def parse_poscar(path: Path) -> dict[str, object]:\n",
    "def parse_poscar(path: Path) -> PoscarData:\n",
)
replace_once(
    "skills/tsao-periodic-dft-materials/scripts/preflight_vasp.py",
    '''    try:
        pos = parse_poscar(run / "POSCAR") if (run / "POSCAR").exists() else {}
    except Exception as exc:
        e.append(f"POSCAR: {exc}")
        pos = {}
''',
    '''    try:
        pos: PoscarData | None = parse_poscar(run / "POSCAR") if (run / "POSCAR").exists() else None
    except Exception as exc:
        e.append(f"POSCAR: {exc}")
        pos = None
''',
)
replace_once(
    "skills/tsao-periodic-dft-materials/scripts/preflight_vasp.py",
    '    if pos.get("species") and titles:\n',
    '    if pos is not None and pos["species"] and titles:\n',
)
replace_once(
    "skills/tsao-periodic-dft-materials/scripts/preflight_vasp.py",
    '    if pos.get("selective_dynamics") and task == "static":\n',
    '    if pos is not None and pos["selective_dynamics"] and task == "static":\n',
)
replace_once(
    "skills/tsao-periodic-dft-materials/scripts/preflight_vasp.py",
    '    if pos.get("coordinate_mode", "").startswith("c") and abs(pos.get("scale", 1.0) - 1.0) > 1e-12:\n',
    '    if pos is not None and pos["coordinate_mode"].startswith("c") and abs(pos["scale"] - 1.0) > 1e-12:\n',
)
replace_once(
    "skills/tsao-periodic-dft-materials/scripts/preflight_vasp.py",
    '        "poscar": pos,\n',
    '        "poscar": pos or {},\n',
)

replace_once(
    "skills/tsao-periodic-dft-materials/scripts/preflight_qe.py",
    '''        for m in re.finditer(r"(\\w+)\\s*=\\s*([^,\\n/]+)", block.group(2)):
            vals[m.group(1).lower()] = m.group(2).strip().strip("'\\\"")
''',
    '''        for value_match in re.finditer(r"(\\w+)\\s*=\\s*([^,\\n/]+)", block.group(2)):
            vals[value_match.group(1).lower()] = value_match.group(2).strip().strip("'\\\"")
''',
)
replace_once(
    "skills/tsao-periodic-dft-materials/scripts/preflight_qe.py",
    "    m = re.search(\n",
    "    species_match = re.search(\n",
)
replace_once(
    "skills/tsao-periodic-dft-materials/scripts/preflight_qe.py",
    '''    if m:
        for line in m.group(1).splitlines():
''',
    '''    if species_match:
        for line in species_match.group(1).splitlines():
''',
)

print("Applied isolated mypy repairs.")

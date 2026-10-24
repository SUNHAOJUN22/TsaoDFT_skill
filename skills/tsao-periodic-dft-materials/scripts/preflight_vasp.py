#!/usr/bin/env python3
"""Preflight a VASP run directory without reading or distributing licensed POTCAR data beyond TITEL lines."""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import TypedDict

import numpy as np


class PoscarData(TypedDict):
    comment: str
    scale: float | None
    scale_factors: list[float]
    effective_scale_factors: list[float]
    raw_lattice_vectors: list[list[float]]
    lattice_vectors: list[list[float]]
    cell_volume_angstrom3: float
    species: list[str]
    counts: list[int]
    atom_count: int
    selective_dynamics: bool
    coordinate_mode: str


def parse_incar(path: Path) -> dict[str, str]:
    d: dict[str, str] = {}
    if not path.exists():
        return d
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.split("!", 1)[0].split("#", 1)[0].strip()
        if "=" in line:
            k, v = line.split("=", 1)
            d[k.strip().upper()] = v.strip()
    return d


def parse_poscar(path: Path) -> PoscarData:
    lines = [x.rstrip() for x in path.read_text(encoding="utf-8", errors="replace").splitlines() if x.strip()]
    if len(lines) < 8:
        raise ValueError("POSCAR too short")
    try:
        scale_factors = [float(value) for value in lines[1].split()]
    except ValueError as exc:
        raise ValueError("POSCAR scale factors must be numeric") from exc
    if len(scale_factors) not in (1, 3) or not all(math.isfinite(value) for value in scale_factors):
        raise ValueError("POSCAR requires one finite scale or three finite Cartesian scale factors")
    if len(scale_factors) == 3 and any(value <= 0.0 for value in scale_factors):
        raise ValueError("three-component POSCAR scale factors must be positive")
    if len(scale_factors) == 1 and scale_factors[0] == 0.0:
        raise ValueError("POSCAR scale must be nonzero")

    raw_vectors: list[list[float]] = []
    for index in range(2, 5):
        fields = lines[index].split()
        if len(fields) != 3:
            raise ValueError("each POSCAR lattice vector must contain exactly three values")
        try:
            vector = [float(value) for value in fields]
        except ValueError as exc:
            raise ValueError("POSCAR lattice vectors must be numeric") from exc
        if not all(math.isfinite(value) for value in vector):
            raise ValueError("POSCAR lattice vectors must be finite")
        raw_vectors.append(vector)

    raw_matrix = np.asarray(raw_vectors, dtype=np.float64)
    singular_values = np.linalg.svd(raw_matrix, compute_uv=False)
    # A relative condition check preserves equivalent cells under uniform POSCAR scaling.
    if (
        not np.isfinite(singular_values).all()
        or singular_values[0] <= 0.0
        or singular_values[-1] / singular_values[0] <= np.finfo(np.float64).eps * 64.0
    ):
        raise ValueError("POSCAR lattice vectors must form a numerically nonsingular cell")
    raw_volume = abs(float(np.linalg.det(raw_matrix)))
    if not math.isfinite(raw_volume) or raw_volume <= 0.0:
        raise ValueError("POSCAR lattice cell volume must be finite and positive")

    scale = scale_factors[0] if len(scale_factors) == 1 else None
    if len(scale_factors) == 1 and scale_factors[0] < 0.0:
        target_volume = abs(scale_factors[0])
        ratio = target_volume / raw_volume
        if not math.isfinite(ratio) or ratio <= 0.0:
            raise ValueError("negative POSCAR scale must specify a finite positive target volume")
        effective_scale = ratio ** (1.0 / 3.0)
        effective_scale_factors = [effective_scale] * 3
    elif len(scale_factors) == 1:
        effective_scale_factors = [scale_factors[0]] * 3
    else:
        effective_scale_factors = scale_factors.copy()

    with np.errstate(over="ignore", invalid="ignore"):
        scaled_matrix = raw_matrix * np.asarray(effective_scale_factors, dtype=np.float64)[None, :]
    if not np.isfinite(scaled_matrix).all():
        raise ValueError("scaled POSCAR lattice vectors exceed the finite range")
    cell_volume = abs(float(np.linalg.det(scaled_matrix)))
    if not math.isfinite(cell_volume) or cell_volume <= 0.0:
        raise ValueError("scaled POSCAR lattice cell volume must be finite and positive")

    species = lines[5].split()
    counts = [int(x) for x in lines[6].split()]
    if len(species) != len(counts) or not all(re.match(r"^[A-Z][a-z]?$", x) for x in species):
        raise ValueError("VASP5 species/count lines required for deterministic validation")
    if not counts or any(count <= 0 for count in counts):
        raise ValueError("POSCAR species counts must be positive integers")
    coord_line = 7
    selective = lines[coord_line].lower().startswith("s")
    if selective:
        coord_line += 1
    mode = lines[coord_line].strip().lower()
    coordinate_mode = "cartesian" if mode.startswith(("c", "k")) else "direct"
    coord_start = coord_line + 1
    n = sum(counts)
    if len(lines) < coord_start + n:
        raise ValueError("POSCAR has fewer coordinate rows than atom count")
    for index, line in enumerate(lines[coord_start : coord_start + n], start=1):
        fields = line.split()
        if len(fields) < 3:
            raise ValueError(f"POSCAR coordinate row {index} must contain three coordinates")
        try:
            coordinates = [float(value) for value in fields[:3]]
        except ValueError as exc:
            raise ValueError(f"POSCAR coordinate row {index} must be numeric") from exc
        if not all(math.isfinite(value) for value in coordinates):
            raise ValueError(f"POSCAR coordinate row {index} must be finite")
        if selective and (len(fields) < 6 or any(value.upper() not in {"T", "F"} for value in fields[3:6])):
            raise ValueError(f"POSCAR selective-dynamics row {index} requires three T/F flags")
        if coordinate_mode == "cartesian":
            scaled_coordinates = [
                value * factor for value, factor in zip(coordinates, effective_scale_factors, strict=True)
            ]
            if not all(math.isfinite(value) for value in scaled_coordinates):
                raise ValueError(f"POSCAR Cartesian coordinate row {index} exceeds the finite range after scaling")
    return {
        "comment": lines[0],
        "scale": scale,
        "scale_factors": scale_factors,
        "effective_scale_factors": effective_scale_factors,
        "raw_lattice_vectors": raw_vectors,
        "lattice_vectors": scaled_matrix.tolist(),
        "cell_volume_angstrom3": cell_volume,
        "species": species,
        "counts": counts,
        "atom_count": n,
        "selective_dynamics": selective,
        "coordinate_mode": coordinate_mode,
    }


def parse_kpoints(path: Path) -> dict:
    if not path.exists():
        return {}
    lines = [x.strip() for x in path.read_text(encoding="utf-8", errors="replace").splitlines() if x.strip()]
    if len(lines) < 4:
        return {"raw_lines": lines}
    return {"comment": lines[0], "declared_points": lines[1], "mode": lines[2], "mesh_or_first_point": lines[3]}


def potcar_titles(path: Path) -> list[str]:
    if not path.exists():
        return []
    titles = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if "TITEL" in line and "=" in line:
            titles.append(line.split("=", 1)[1].strip())
    return titles


def validate(run: Path) -> dict:
    e = []
    w = []
    for f in ["INCAR", "POSCAR"]:
        if not (run / f).exists():
            e.append(f"missing {f}")
    try:
        pos: PoscarData | None = parse_poscar(run / "POSCAR") if (run / "POSCAR").exists() else None
    except Exception as exc:
        e.append(f"POSCAR: {exc}")
        pos = None
    inc = parse_incar(run / "INCAR")
    kp = parse_kpoints(run / "KPOINTS")
    titles = potcar_titles(run / "POTCAR")
    if not inc:
        e.append("INCAR empty/unparseable")
    for key in ["ENCUT", "EDIFF", "PREC"]:
        if key not in inc:
            w.append(f"INCAR missing explicit {key}")
    if "KSPACING" not in inc and not kp:
        w.append("neither KSPACING nor KPOINTS found")
    if pos is not None and pos["species"] and titles:
        inferred = []
        for title in titles:
            m = re.search(r"PAW_[A-Z]+\s+([A-Z][a-z]?)", title)
            inferred.append(m.group(1) if m else title)
        if len(inferred) != len(pos["species"]):
            e.append(f"POTCAR dataset count {len(inferred)} != POSCAR species count {len(pos['species'])}")
        elif inferred != pos["species"]:
            e.append(f"POSCAR/POTCAR order mismatch: {pos['species']} vs {inferred}")
    elif not titles:
        w.append("POTCAR absent/unreadable; licensed potential mapping must be verified at the execution site")
    ibrion = inc.get("IBRION")
    nsw = (
        int(float(inc.get("NSW", "0").split()[0]))
        if inc.get("NSW", "0").split()[0].replace(".", "", 1).lstrip("-").isdigit()
        else 0
    )
    task = "relax" if nsw > 0 else "static"
    if task == "relax" and ibrion in (None, "-1"):
        w.append("relax inferred from NSW but IBRION is absent/-1")
    if pos is not None and pos["selective_dynamics"] and task == "static":
        w.append("selective dynamics present but NSW=0/static")
    if inc.get("ISPIN") == "2" and "MAGMOM" not in inc:
        w.append("spin-polarized run lacks explicit MAGMOM")
    if any(k.startswith("LDAU") for k in inc) and "LDAUU" not in inc:
        e.append("DFT+U tags present without LDAUU")
    if (
        pos is not None
        and pos["coordinate_mode"] == "cartesian"
        and any(abs(value - 1.0) > 1e-12 for value in pos["effective_scale_factors"])
    ):
        w.append("Cartesian POSCAR coordinates are interpreted using the resolved scale factors")
    return {
        "ok": not e,
        "errors": e,
        "warnings": w,
        "task_inferred": task,
        "incar": inc,
        "poscar": pos or {},
        "kpoints": kp,
        "potcar_titel": titles,
        "scientific_acceptance": "PENDING",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("run_dir", type=Path)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    r = validate(a.run_dir)
    print(json.dumps(r, indent=2))
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

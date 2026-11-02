#!/usr/bin/env python3
"""Preflight a VASP run directory without reading or distributing licensed POTCAR data beyond TITEL lines."""

from __future__ import annotations

import argparse
import json
import math
import re
from collections.abc import Iterator
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


def _incar_statements(text: str) -> Iterator[str]:
    """Read flat INCAR statements without promoting quoted data to global tags.

    VASP documents semicolons, backslash continuations and multiline double
    quotes at https://vasp.at/wiki/INCAR. Scoped brace blocks require a separate
    interpretation, so this selected-field preflight rejects them explicitly.
    """
    statement: list[str] = []
    quoted = False
    continued = False
    for raw in text.splitlines():
        continued = False
        for index, character in enumerate(raw):
            if character == '"':
                quoted = not quoted
                statement.append(character)
            elif not quoted and character in "#!":
                break
            elif not quoted and character in "{}":
                raise ValueError("scoped INCAR brace blocks are not supported by this preflight")
            elif not quoted and character == ";":
                yield "".join(statement).strip()
                statement.clear()
            elif not quoted and character == "\\" and index == len(raw) - 1:
                continued = True
            else:
                statement.append(character)
        if quoted:
            statement.append("\n")
        elif continued:
            statement.append(" ")
        else:
            yield "".join(statement).strip()
            statement.clear()
    if quoted:
        raise ValueError("INCAR has an unterminated double-quoted value")
    if continued:
        raise ValueError("INCAR has a continuation without a following line")


def parse_incar(path: Path) -> dict[str, str]:
    declarations: dict[str, str] = {}
    if not path.exists():
        return declarations
    for statement in _incar_statements(path.read_text(encoding="utf-8", errors="replace")):
        if "=" not in statement:
            continue
        key, value = (part.strip() for part in statement.split("=", 1))
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1].strip()
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_/]*", key) or not value:
            raise ValueError("INCAR statements require a tag name and a nonempty value")
        declarations[key.upper()] = value
    return declarations


def _incar_integer(declarations: dict[str, str], key: str, default: int | None = None) -> int | None:
    """Parse one complete integer declaration within this adapter's range.

    The signed 64-bit bound is a preflight support limit, not certification of
    an engine build's integer kind or a scientifically suitable step count.
    """
    text = declarations.get(key)
    if text is None:
        return default
    if re.fullmatch(r"[+-]?[0-9]+", text) is None:
        raise ValueError(f"{key} must be one signed decimal integer")
    digits = text.lstrip("+-").lstrip("0") or "0"
    # Bound conversion before int(): very long input must not depend on the
    # interpreter's configurable integer-string limit, or pass through float.
    if len(digits) > 19:
        raise ValueError(f"{key} exceeds the preflight supported signed 64-bit range")
    value = int(digits) * (-1 if text.startswith("-") else 1)
    if not -(2**63) <= value < 2**63:
        raise ValueError(f"{key} exceeds the preflight supported signed 64-bit range")
    return value


def _log_cell_volume(matrix: np.ndarray) -> float:
    # POSCAR raw vectors may use any length scale. Test the directions after
    # row normalization, retaining the existing relative singularity margin.
    lengths = np.max(np.abs(matrix), axis=1)
    if not np.isfinite(matrix).all() or np.any(lengths == 0.0):
        raise ValueError("POSCAR lattice vectors must form a numerically nonsingular cell")
    normalized = matrix / lengths[:, None]
    singular_values = np.linalg.svd(normalized, compute_uv=False)
    if singular_values[-1] <= np.finfo(np.float64).eps * float(singular_values[0]) * 64.0:
        raise ValueError("POSCAR lattice vectors must form a numerically nonsingular cell")
    _, log_volume = np.linalg.slogdet(normalized)
    return float(log_volume + np.log(lengths).sum())


def parse_poscar(path: Path) -> PoscarData:
    # The first record is a comment and may be blank; do not shift fixed fields.
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
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

    scale = scale_factors[0] if len(scale_factors) == 1 else None
    if len(scale_factors) == 1 and scale_factors[0] < 0.0:
        # A uniform target-volume scale needs the raw volume. Positive component
        # scales may improve the cell's conditioning, so validate those only
        # after applying the declared Cartesian transformation below.
        raw_log_volume = _log_cell_volume(raw_matrix)
        target_volume = abs(scale_factors[0])
        try:
            effective_scale = math.exp((math.log(target_volume) - raw_log_volume) / 3.0)
        except OverflowError as exc:
            raise ValueError("negative POSCAR scale exceeds the finite effective-scale range") from exc
        if effective_scale == 0.0:
            raise ValueError("negative POSCAR scale underflows the effective-scale range")
        effective_scale_factors = [effective_scale] * 3
    elif len(scale_factors) == 1:
        effective_scale_factors = [scale_factors[0]] * 3
    else:
        effective_scale_factors = scale_factors.copy()

    with np.errstate(over="ignore", invalid="ignore"):
        scaled_matrix = raw_matrix * np.asarray(effective_scale_factors, dtype=np.float64)[None, :]
    if not np.isfinite(scaled_matrix).all():
        raise ValueError("scaled POSCAR lattice vectors exceed the finite range")
    try:
        cell_volume = math.exp(_log_cell_volume(scaled_matrix))
    except OverflowError as exc:
        raise ValueError("scaled POSCAR lattice cell volume must be finite and positive") from exc
    if cell_volume <= 0.0:
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
        with np.errstate(over="ignore", invalid="ignore"):
            scaled_coordinates = (
                np.asarray(coordinates) * effective_scale_factors
                if coordinate_mode == "cartesian"
                else np.asarray(coordinates) @ scaled_matrix
            )
        if not np.isfinite(scaled_coordinates).all():
            raise ValueError(f"POSCAR {coordinate_mode} coordinate row {index} exceeds the finite range after scaling")
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
    try:
        inc = parse_incar(run / "INCAR")
    except (OSError, ValueError) as exc:
        e.append(f"INCAR: {exc}")
        inc = {}
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
    integer_controls: dict[str, int | None] = {}
    valid_integer_controls = True
    for key, default in (("NSW", 0), ("IBRION", None), ("ISPIN", None)):
        try:
            integer_controls[key] = _incar_integer(inc, key, default)
        except ValueError as exc:
            e.append(f"INCAR: {exc}")
            integer_controls[key] = None
            valid_integer_controls = False
    nsw = integer_controls["NSW"]
    ibrion = integer_controls["IBRION"]
    task = "unknown"
    if inc and valid_integer_controls:
        # NSW counts ionic steps; it does not select the ionic algorithm.
        # Keep the existing static/relax/unknown contract and leave MD,
        # phonons and other modes to their mode-specific preflight.
        if nsw is not None and nsw >= -1:
            if ibrion == -1 or (nsw <= 0 and ibrion in (None, 1, 2, 3)):
                task = "static"
            elif nsw > 0 and ibrion in (1, 2, 3):
                task = "relax"
        if task == "unknown":
            mode = "default (0 when NSW > 0)" if ibrion is None else str(ibrion)
            w.append(f"task inference limited to static/relax; NSW={nsw}, IBRION={mode} requires mode-specific review")
        elif task == "static" and nsw is not None and nsw > 0:
            w.append("IBRION=-1 with NSW>0 repeats the structure without structural updates")
    if pos is not None and pos["selective_dynamics"] and task == "static":
        w.append("selective dynamics present but no ionic structure update is inferred")
    if integer_controls["ISPIN"] == 2 and "MAGMOM" not in inc:
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

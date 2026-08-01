#!/usr/bin/env python3
"""Inspect an XYZ geometry for deterministic structural red flags.

This script does not assign bond orders, charge, multiplicity, protonation, or oxidation states.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

COVALENT = {
    "H": 0.31,
    "B": 0.85,
    "C": 0.76,
    "N": 0.71,
    "O": 0.66,
    "F": 0.57,
    "Si": 1.11,
    "P": 1.07,
    "S": 1.05,
    "Cl": 1.02,
    "Ti": 1.60,
    "Cr": 1.39,
    "Mn": 1.39,
    "Fe": 1.32,
    "Co": 1.26,
    "Ni": 1.24,
    "Cu": 1.32,
    "Zn": 1.22,
    "Br": 1.20,
    "I": 1.39,
    "Zr": 1.75,
    "Mo": 1.54,
    "Ru": 1.46,
    "Rh": 1.42,
    "Pd": 1.39,
    "Ag": 1.45,
    "Cd": 1.44,
    "Pt": 1.36,
    "Au": 1.36,
}
VALID = re.compile(r"^[A-Z][a-z]?$")
PAIR_BACKENDS = ("auto", "python", "numpy")
AUTO_NUMPY_ATOMS = 512


def parse_xyz(path: Path) -> tuple[str, list[dict[str, Any]]]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    if not lines:
        raise ValueError("empty XYZ")
    try:
        atom_count = int(lines[0].strip())
    except ValueError as exc:
        raise ValueError("first line must be atom count") from exc
    if atom_count < 1:
        raise ValueError("atom count must be positive")
    if len(lines) < atom_count + 2:
        raise ValueError(f"expected {atom_count} atoms but file has fewer lines")

    atoms: list[dict[str, Any]] = []
    for index, line in enumerate(lines[2 : 2 + atom_count], 1):
        parts = line.split()
        if len(parts) < 4:
            raise ValueError(f"atom line {index} has fewer than 4 fields")
        element = parts[0].capitalize()
        if VALID.fullmatch(element) is None:
            raise ValueError(f"invalid element token {parts[0]} at atom {index}")
        try:
            x, y, z = map(float, parts[1:4])
        except ValueError as exc:
            raise ValueError(f"non-numeric coordinate at atom {index}") from exc
        if not all(math.isfinite(value) for value in (x, y, z)):
            raise ValueError(f"non-finite coordinate at atom {index}")
        atoms.append({"index": index, "element": element, "x": x, "y": y, "z": z})
    return lines[1] if len(lines) > 1 else "", atoms


def distance(a: dict[str, Any], b: dict[str, Any]) -> float:
    return math.dist((a["x"], a["y"], a["z"]), (b["x"], b["y"], b["z"]))


def _pair_findings_python(
    atoms: list[dict[str, Any]],
    clash_scale: float,
    bond_scale: float,
) -> tuple[list[str], list[dict[str, Any]], float | None]:
    errors: list[str] = []
    bonds: list[dict[str, Any]] = []
    minimum: float | None = None
    for index, atom in enumerate(atoms):
        radius_a = COVALENT.get(atom["element"])
        for other in atoms[index + 1 :]:
            separation = distance(atom, other)
            if not math.isfinite(separation):
                errors.append(f"non-finite distance: atoms {atom['index']} and {other['index']}")
                continue
            minimum = separation if minimum is None else min(minimum, separation)
            radius_b = COVALENT.get(other["element"])
            if separation < 1e-6:
                errors.append(f"duplicate coordinates: atoms {atom['index']} and {other['index']}")
            if radius_a and radius_b:
                reference = radius_a + radius_b
                if separation < clash_scale * reference:
                    errors.append(f"severe contact {atom['index']}-{other['index']}: {separation:.3f} Å")
                if separation <= bond_scale * reference:
                    bonds.append(
                        {
                            "i": atom["index"],
                            "j": other["index"],
                            "distance_angstrom": round(separation, 6),
                            "heuristic_only": True,
                        }
                    )
    return errors, bonds, minimum


def _pair_findings_numpy(
    atoms: list[dict[str, Any]],
    clash_scale: float,
    bond_scale: float,
) -> tuple[list[str], list[dict[str, Any]], float | None]:
    """Vectorize pair distances while preserving deterministic pair ordering."""

    errors: list[str] = []
    bonds: list[dict[str, Any]] = []
    minimum: float | None = None
    if len(atoms) < 2:
        return errors, bonds, minimum

    coordinates = np.asarray([[atom["x"], atom["y"], atom["z"]] for atom in atoms], dtype=np.float64)
    radii = np.asarray([COVALENT.get(atom["element"], np.nan) for atom in atoms], dtype=np.float64)

    for index, atom in enumerate(atoms[:-1]):
        delta = coordinates[index + 1 :] - coordinates[index]
        separations = np.sqrt(np.einsum("ij,ij->i", delta, delta, optimize=True))
        finite = np.isfinite(separations)
        for offset in np.flatnonzero(~finite):
            other = atoms[index + 1 + int(offset)]
            errors.append(f"non-finite distance: atoms {atom['index']} and {other['index']}")
        finite_separations = separations[finite]
        if finite_separations.size:
            local_minimum = float(finite_separations.min())
            minimum = local_minimum if minimum is None else min(minimum, local_minimum)

        for offset in np.flatnonzero(finite & (separations < 1e-6)):
            other = atoms[index + 1 + int(offset)]
            errors.append(f"duplicate coordinates: atoms {atom['index']} and {other['index']}")

        radius_a = radii[index]
        if not np.isfinite(radius_a):
            continue
        other_radii = radii[index + 1 :]
        valid_radii = np.isfinite(other_radii)
        references = radius_a + other_radii
        severe_mask = finite & valid_radii & (separations < clash_scale * references)
        bond_mask = finite & valid_radii & (separations <= bond_scale * references)

        for offset in np.flatnonzero(severe_mask):
            other = atoms[index + 1 + int(offset)]
            separation = float(separations[offset])
            errors.append(f"severe contact {atom['index']}-{other['index']}: {separation:.3f} Å")
        for offset in np.flatnonzero(bond_mask):
            other = atoms[index + 1 + int(offset)]
            separation = float(separations[offset])
            bonds.append(
                {
                    "i": atom["index"],
                    "j": other["index"],
                    "distance_angstrom": round(separation, 6),
                    "heuristic_only": True,
                }
            )
    return errors, bonds, minimum


def inspect(
    atoms: list[dict[str, Any]],
    clash_scale: float = 0.55,
    bond_scale: float = 1.25,
    backend: str = "auto",
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not atoms:
        errors.append("no atoms")
    if not math.isfinite(clash_scale) or clash_scale <= 0:
        errors.append("clash_scale must be positive finite")
    if not math.isfinite(bond_scale) or bond_scale <= 0:
        errors.append("bond_scale must be positive finite")
    if backend not in PAIR_BACKENDS:
        errors.append(f"backend must be one of {PAIR_BACKENDS}")
        backend = "python"

    for atom in atoms:
        if atom["element"] not in COVALENT:
            warnings.append(f"no covalent radius for {atom['element']}; pair heuristics incomplete")

    selected_backend = "numpy" if backend == "numpy" or (backend == "auto" and len(atoms) >= AUTO_NUMPY_ATOMS) else "python"
    if selected_backend == "numpy":
        pair_errors, bonds, minimum = _pair_findings_numpy(atoms, clash_scale, bond_scale)
    else:
        pair_errors, bonds, minimum = _pair_findings_python(atoms, clash_scale, bond_scale)
    errors.extend(pair_errors)

    degree = {atom["index"]: 0 for atom in atoms}
    for bond in bonds:
        degree[bond["i"]] += 1
        degree[bond["j"]] += 1
    isolated = [index for index, value in degree.items() if value == 0]
    if isolated:
        warnings.append(f"heuristically isolated atoms: {isolated}; review fragments/coordination")
    centroid = {axis: sum(atom[axis] for atom in atoms) / len(atoms) for axis in ("x", "y", "z")} if atoms else {}
    span = (
        {axis: max(atom[axis] for atom in atoms) - min(atom[axis] for atom in atoms) for axis in ("x", "y", "z")}
        if atoms
        else {}
    )
    return {
        "ok": not errors,
        "errors": sorted(set(errors)),
        "warnings": sorted(set(warnings)),
        "atom_count": len(atoms),
        "elements": dict(sorted(Counter(atom["element"] for atom in atoms).items())),
        "centroid_angstrom": centroid,
        "span_angstrom": span,
        "minimum_pair_distance_angstrom": minimum,
        "heuristic_bonds": bonds,
        "pair_backend": selected_backend,
        "pair_count": len(atoms) * (len(atoms) - 1) // 2,
        "note": "Bond list is a geometry heuristic, not electronic-structure evidence.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("xyz", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--backend", choices=PAIR_BACKENDS, default="auto")
    args = parser.parse_args()
    try:
        comment, atoms = parse_xyz(args.xyz)
        result = inspect(atoms, backend=args.backend)
        result["comment"] = comment
        result["source"] = str(args.xyz.resolve())
    except (OSError, UnicodeError, ValueError) as exc:
        result = {"ok": False, "errors": [str(exc)], "warnings": [], "source": str(args.xyz.resolve())}
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

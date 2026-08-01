#!/usr/bin/env python3
"""Inspect an XYZ geometry for deterministic structural red flags.

This script does not assign bond orders, charge, multiplicity, protonation, or oxidation states.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any

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


def inspect(
    atoms: list[dict[str, Any]],
    clash_scale: float = 0.55,
    bond_scale: float = 1.25,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    pairs: list[float] = []
    bonds: list[dict[str, Any]] = []
    if not atoms:
        errors.append("no atoms")
    if not math.isfinite(clash_scale) or clash_scale <= 0:
        errors.append("clash_scale must be positive finite")
    if not math.isfinite(bond_scale) or bond_scale <= 0:
        errors.append("bond_scale must be positive finite")

    for index, atom in enumerate(atoms):
        if atom["element"] not in COVALENT:
            warnings.append(f"no covalent radius for {atom['element']}; pair heuristics incomplete")
        for other in atoms[index + 1 :]:
            separation = distance(atom, other)
            if not math.isfinite(separation):
                errors.append(f"non-finite distance: atoms {atom['index']} and {other['index']}")
                continue
            pairs.append(separation)
            radius_a = COVALENT.get(atom["element"])
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
        "elements": {
            element: sum(atom["element"] == element for atom in atoms)
            for element in sorted({atom["element"] for atom in atoms})
        },
        "centroid_angstrom": centroid,
        "span_angstrom": span,
        "minimum_pair_distance_angstrom": min(pairs) if pairs else None,
        "heuristic_bonds": bonds,
        "note": "Bond list is a geometry heuristic, not electronic-structure evidence.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("xyz", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    try:
        comment, atoms = parse_xyz(args.xyz)
        result = inspect(atoms)
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

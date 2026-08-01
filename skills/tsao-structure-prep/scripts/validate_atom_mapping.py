#!/usr/bin/env python3
"""Validate atom ordering/mapping between two XYZ structures."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from inspect_xyz import parse_xyz


def atom_record(value: Any, label: str, errors: list[str]) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        errors.append(f"{label} must be a mapping")
        return None
    element = value.get("element")
    if not isinstance(element, str) or not element:
        errors.append(f"{label}.element must be a non-empty string")
    coordinates: dict[str, float] = {}
    for axis in ("x", "y", "z"):
        raw = value.get(axis)
        if isinstance(raw, bool) or not isinstance(raw, (int, float)) or not math.isfinite(float(raw)):
            errors.append(f"{label}.{axis} must be finite numeric")
        else:
            coordinates[axis] = float(raw)
    if len(coordinates) != 3 or not isinstance(element, str) or not element:
        return None
    return {"element": element, **coordinates}


def validate(
    reference: Any,
    candidate: Any,
    mapping: Any = None,
) -> tuple[list[str], list[str], dict[str, Any]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(reference, list) or not isinstance(candidate, list):
        return ["reference and candidate atoms must be lists"], warnings, {}

    atoms_a: list[dict[str, Any]] = []
    atoms_b: list[dict[str, Any]] = []
    for index, value in enumerate(reference):
        atom = atom_record(value, f"reference[{index}]", errors)
        if atom is not None:
            atoms_a.append(atom)
    for index, value in enumerate(candidate):
        atom = atom_record(value, f"candidate[{index}]", errors)
        if atom is not None:
            atoms_b.append(atom)
    if errors:
        return sorted(set(errors)), warnings, {}

    if len(atoms_a) != len(atoms_b):
        errors.append(f"atom count differs: {len(atoms_a)} vs {len(atoms_b)}")
        return errors, warnings, {}
    atom_count = len(atoms_a)
    if mapping is None:
        normalized_mapping = list(range(1, atom_count + 1))
    elif not isinstance(mapping, list) or not all(
        isinstance(item, int) and not isinstance(item, bool) for item in mapping
    ):
        errors.append("mapping must be a list of integers")
        return errors, warnings, {}
    else:
        normalized_mapping = mapping
    if len(normalized_mapping) != atom_count or sorted(normalized_mapping) != list(range(1, atom_count + 1)):
        errors.append("mapping must be a 1-based permutation")
        return errors, warnings, {}

    squared_distance = 0.0
    maximum_distance = 0.0
    element_mismatches: list[tuple[int, int, object, object]] = []
    for index, candidate_index in enumerate(normalized_mapping):
        atom_a = atoms_a[index]
        atom_b = atoms_b[candidate_index - 1]
        if atom_a["element"] != atom_b["element"]:
            element_mismatches.append((index + 1, candidate_index, atom_a["element"], atom_b["element"]))
        distance = math.dist(
            (atom_a["x"], atom_a["y"], atom_a["z"]),
            (atom_b["x"], atom_b["y"], atom_b["z"]),
        )
        if not math.isfinite(distance):
            errors.append(f"non-finite displacement for atom {index + 1}")
            continue
        squared_distance += distance * distance
        maximum_distance = max(maximum_distance, distance)
    if element_mismatches:
        errors.append(f"element mismatches: {element_mismatches}")
    rmsd = math.sqrt(squared_distance / atom_count) if atom_count else 0.0
    if rmsd > 2.0:
        warnings.append("large raw-coordinate RMSD; alignment was not performed")
    return (
        sorted(set(errors)),
        sorted(set(warnings)),
        {
            "atom_count": atom_count,
            "raw_rmsd_angstrom": rmsd,
            "max_displacement_angstrom": maximum_distance,
            "mapping": normalized_mapping,
            "note": "RMSD uses provided coordinates without rotation/translation alignment.",
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--mapping", help="comma-separated 1-based candidate indices")
    args = parser.parse_args()
    try:
        _, reference = parse_xyz(args.reference)
        _, candidate = parse_xyz(args.candidate)
        mapping = [int(value) for value in args.mapping.split(",")] if args.mapping is not None else None
        errors, warnings, summary = validate(reference, candidate, mapping)
    except (OSError, UnicodeError, ValueError) as exc:
        errors = [f"atom mapping input failed: {exc}"]
        warnings = []
        summary = {}
    print(json.dumps({"ok": not errors, "errors": errors, "warnings": warnings, "summary": summary}, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

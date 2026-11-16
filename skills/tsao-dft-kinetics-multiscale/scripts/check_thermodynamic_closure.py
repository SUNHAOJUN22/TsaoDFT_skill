#!/usr/bin/env python3
"""Check forward/reverse barrier thermodynamic closure: ΔG‡rev = ΔG‡fwd - ΔGrxn."""

from __future__ import annotations

import argparse
import json
import math
from fractions import Fraction
from pathlib import Path
from typing import Any

import yaml


def finite_number(value: Any, label: str, errors: list[str]) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        errors.append(f"{label} must be finite numeric")
        return None
    try:
        result = float(value)
    except (OverflowError, ValueError):
        errors.append(f"{label} must be finite numeric")
        return None
    if not math.isfinite(result):
        errors.append(f"{label} must be finite numeric")
        return None
    return result


def species_energies(document: dict[str, Any], errors: list[str]) -> dict[str, float] | None:
    """Resolve the optional state table without inventing missing thermochemistry."""
    if "species" not in document:
        return None
    records = document["species"]
    if not isinstance(records, list) or not records:
        errors.append("species must be a non-empty list when checking species free energies")
        return {}
    energies: dict[str, float] = {}
    seen: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append(f"species[{index}] must be a mapping")
            continue
        identifier = record.get("id")
        if not isinstance(identifier, str) or not identifier:
            errors.append(f"species[{index}].id must be a non-empty string")
            continue
        if identifier in seen:
            errors.append(f"duplicate species id in thermodynamic closure: {identifier}")
            continue
        seen.add(identifier)
        energy = finite_number(record.get("free_energy"), f"species[{index}].free_energy", errors)
        if energy is not None:
            energies[identifier] = energy
    return energies


def species_reaction_energy(
    reaction: dict[str, Any], energies: dict[str, float] | None, label: str, errors: list[str]
) -> Fraction | None:
    """Use the written stoichiometry and the network's common energy basis."""
    if energies is None:
        return None
    before = len(errors)
    delta = Fraction(0)
    for side_name, sign in (("reactants", -1), ("products", 1)):
        side = reaction.get(side_name)
        if not isinstance(side, dict) or not side:
            errors.append(f"{label}.{side_name} is required to check species free energies")
            continue
        for identifier, raw_coefficient in side.items():
            if not isinstance(identifier, str) or identifier not in energies:
                errors.append(f"{label} has no species free energy for {identifier!r}")
                continue
            coefficient = finite_number(raw_coefficient, f"{label}.{side_name}.{identifier}", errors)
            if coefficient is None:
                continue
            if coefficient <= 0:
                errors.append(f"{label}.{side_name}.{identifier} coefficient must be positive")
                continue
            delta += sign * Fraction(coefficient) * Fraction(energies[identifier])
    if len(errors) != before:
        return None
    try:
        float(delta)
    except OverflowError:
        errors.append(f"{label} species reaction free energy exceeds the finite floating-point range")
        return None
    return delta


def analyze(document: Any, tolerance: Any) -> dict[str, Any]:
    errors: list[str] = []
    rows: list[dict[str, Any]] = []

    threshold = finite_number(tolerance, "tolerance", errors)
    if threshold is not None and threshold < 0:
        errors.append("tolerance must be non-negative")
    if threshold is None or threshold < 0:
        threshold = 0.0

    if not isinstance(document, dict):
        return {
            "ok": False,
            "errors": sorted(set([*errors, "root must be a mapping"])),
            "reactions": rows,
            "unit": None,
            "tolerance": threshold,
            "species_energy_checked": False,
        }

    reactions = document.get("reactions")
    if not isinstance(reactions, list):
        errors.append("reactions must be a list")
        reactions = []
    energies = species_energies(document, errors)
    checked_reactions = 0

    for index, raw in enumerate(reactions):
        label = f"reactions[{index}]"
        if not isinstance(raw, dict):
            errors.append(f"{label} must be a mapping")
            continue
        reaction_id = raw.get("id")
        if not isinstance(reaction_id, str) or not reaction_id:
            errors.append(f"{label}.id must be a non-empty string")
            reaction_id = label
        reversible = raw.get("reversible", False)
        if not isinstance(reversible, bool):
            errors.append(f"{label}.reversible must be boolean")
            continue
        derived_energy = species_reaction_energy(raw, energies, reaction_id, errors)
        if derived_energy is not None:
            checked_reactions += 1
        reaction_energy = None
        if reversible or raw.get("reaction_free_energy") is not None:
            reaction_energy = finite_number(raw.get("reaction_free_energy"), f"{label}.reaction_free_energy", errors)
        if (
            derived_energy is not None
            and reaction_energy is not None
            and abs(Fraction(reaction_energy) - derived_energy) > Fraction(threshold)
        ):
            errors.append(
                f"{reaction_id} reaction_free_energy disagrees with species free energies "
                f"({float(derived_energy):.6g} {document.get('energy_unit')}) beyond tolerance {threshold}"
            )
        if not reversible:
            continue

        forward = finite_number(raw.get("forward_barrier"), f"{label}.forward_barrier", errors)
        if forward is None or reaction_energy is None:
            continue

        try:
            expected_reverse = math.fsum((forward, -reaction_energy))
        except OverflowError:
            errors.append(f"{reaction_id} expected reverse barrier exceeds the finite floating-point range")
            continue
        reported_raw = raw.get("reverse_barrier")
        reported_reverse: float | None = None
        closure_error: float | None = None
        if reported_raw is not None:
            reported_reverse = finite_number(reported_raw, f"{label}.reverse_barrier", errors)
            if reported_reverse is not None:
                try:
                    closure_error = math.fsum((reported_reverse, -expected_reverse))
                except OverflowError:
                    errors.append(f"{reaction_id} closure error exceeds the finite floating-point range")
                    continue
                if abs(closure_error) > threshold:
                    errors.append(f"{reaction_id} closure error {closure_error:.6g} exceeds {threshold}")
        rows.append(
            {
                "reaction_id": reaction_id,
                "expected_reverse_barrier": expected_reverse,
                "reported_reverse_barrier": reported_reverse,
                "closure_error": closure_error,
                "species_reaction_free_energy": float(derived_energy) if derived_energy is not None else None,
            }
        )

    return {
        "ok": not errors,
        "errors": sorted(set(errors)),
        "reactions": rows,
        "unit": document.get("energy_unit"),
        "tolerance": threshold,
        "species_energy_checked": energies is not None and bool(reactions) and checked_reactions == len(reactions),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("network", type=Path)
    parser.add_argument("--tolerance", type=float, default=0.05)
    args = parser.parse_args()
    try:
        document = yaml.safe_load(args.network.read_text(encoding="utf-8"))
        report = analyze(document, args.tolerance)
    except (OSError, UnicodeError, TypeError, ValueError, yaml.YAMLError) as exc:
        report = {
            "ok": False,
            "errors": [f"thermodynamic closure input failed: {exc}"],
            "reactions": [],
            "unit": None,
            "tolerance": args.tolerance,
        }
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Export a review-required Cantera-oriented handoff from a validated DFT reaction network.

The output is not claimed to be a complete runnable Cantera mechanism unless downstream
thermo and rate models are supplied and independently validated.
"""

from __future__ import annotations

import argparse
import json
import os
import runpy
import tempfile
from pathlib import Path
from typing import Any

import yaml


def build_handoff(d: dict[str, Any], warnings: list[str]) -> dict[str, Any]:
    species = []
    for s in d.get("species", []):
        species.append(
            {
                "name": s["id"],
                "composition": s.get("composition", {}),
                "charge": s.get("charge", 0),
                "thermo_handoff": {
                    "free_energy": s.get("free_energy"),
                    "unit": d.get("energy_unit"),
                    "temperature_K": d.get("temperature_K"),
                    "artifact_id": s.get("artifact_id"),
                },
            }
        )
    reactions = []

    def side(x):
        return " + ".join((f"{v:g} {k}" if float(v) != 1 else k) for k, v in x.items())

    for r in d.get("reactions", []):
        reactions.append(
            {
                "id": r["id"],
                "equation": f"{side(r['reactants'])} {'<=>' if r.get('reversible') else '=>'} {side(r['products'])}",
                "rate_handoff": {
                    "forward_barrier": r.get("forward_barrier"),
                    "reverse_barrier": r.get("reverse_barrier"),
                    "reaction_free_energy": r.get("reaction_free_energy"),
                    "energy_unit": d.get("energy_unit"),
                    "path_degeneracy": r.get("path_degeneracy", 1),
                    "transition_state_artifact_id": r.get("transition_state_artifact_id"),
                },
            }
        )
    return {
        "generator": "TsaoDFT",
        "format": "cantera-oriented-handoff",
        "runnable_cantera_mechanism": False,
        "review_required": True,
        "validation_warnings": warnings,
        "phase_model": d.get("phase_model"),
        "standard_state": d.get("standard_state"),
        "temperature_K": d.get("temperature_K"),
        "species": species,
        "reactions": reactions,
        "missing_for_runnable_model": [
            "heat-capacity/enthalpy/entropy thermo models across temperature",
            "dimensionally consistent rate expressions",
            "phase/site definitions",
            "transport/reactor settings",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("network", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    temporary_path: Path | None = None
    try:
        if args.out.resolve() == args.network.resolve() or (args.out.exists() and args.out.samefile(args.network)):
            raise ValueError("handoff output must not replace the input reaction network")
        if args.out.is_symlink():
            raise ValueError("handoff output must not be a symlink")
        directory = Path(__file__).resolve().parent
        runtime = directory / "_shared/benchmark_contract.py"
        if not runtime.is_file():
            runtime = directory.parents[1] / "tsao-dft-hpc-provenance/scripts/benchmark_contract.py"
        decode_yaml = runpy.run_path(str(runtime))["decode_yaml"]
        document = decode_yaml(args.network.read_text(encoding="utf-8"))
        validate = runpy.run_path(str(directory / "validate_reaction_network.py"))["validate"]
        errors, warnings = validate(document)
        if errors:
            raise ValueError("reaction network validation failed: " + "; ".join(errors))
        output = build_handoff(document, warnings)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=args.out.parent, prefix=f".{args.out.name}.", suffix=".tmp", delete=False
        ) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(yaml.safe_dump(output, sort_keys=False))
        os.replace(temporary_path, args.out)
    except (OSError, UnicodeError, TypeError, ValueError, yaml.YAMLError) as exc:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        print(json.dumps({"ok": False, "errors": [str(exc)]}, indent=2))
        return 1
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

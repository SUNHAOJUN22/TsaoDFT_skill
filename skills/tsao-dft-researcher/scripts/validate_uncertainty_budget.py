#!/usr/bin/env python3
"""Validate a DFT uncertainty/sensitivity budget."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import yaml

ALLOWED = {
    "conformer",
    "method",
    "basis",
    "dispersion",
    "solvent",
    "standard_state",
    "low_frequency",
    "spin_state",
    "numerical",
    "model_truncation",
    "sampling",
    "reference_state",
    "other",
}
RULES = {"root_sum_square", "sum_bounds", "report_separately"}


def validate(data: Any) -> tuple[list[str], list[str], dict[str, Any]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(data, dict):
        return ["uncertainty budget root must be a mapping"], warnings, {"combined_magnitude": None, "unit": None}

    for key in ["schema_version", "project_id", "observable", "unit", "components", "combination_rule", "status"]:
        if key not in data:
            errors.append(f"missing {key}")
    unit = data.get("unit")
    if not isinstance(unit, str) or not unit.strip():
        errors.append("unit must be a nonempty string")
        unit = None

    components = data.get("components")
    if not isinstance(components, list):
        errors.append("components must be a list")
        components = []
    if not components:
        warnings.append("no uncertainty components declared")

    values: list[float] = []
    for index, component in enumerate(components):
        if not isinstance(component, dict):
            errors.append(f"components[{index}] must be a mapping")
            continue
        component_type = component.get("type")
        if not isinstance(component_type, str) or component_type not in ALLOWED:
            errors.append(f"components[{index}] invalid type")
        raw_magnitude = component.get("magnitude")
        if isinstance(raw_magnitude, bool) or not isinstance(raw_magnitude, (int, float)):
            errors.append(f"components[{index}] magnitude must be finite numeric")
        else:
            try:
                magnitude = float(raw_magnitude)
            except OverflowError:
                magnitude = math.inf
            if not math.isfinite(magnitude):
                errors.append(f"components[{index}] magnitude must be finite numeric")
            elif magnitude < 0:
                errors.append(f"components[{index}] magnitude must be nonnegative")
            else:
                values.append(magnitude)
        if not component.get("basis"):
            warnings.append(f"components[{index}] has no evidence/basis")

    rule = data.get("combination_rule")
    if not isinstance(rule, str) or rule not in RULES:
        errors.append("invalid combination_rule")

    combined: float | None = None
    # Never describe a partial valid subset as the budget's combined magnitude.
    # Stable accumulation avoids intermediate overflow but cannot make an
    # unrepresentable final magnitude a valid finite result.
    if values and not errors:
        try:
            if rule == "root_sum_square":
                combined = math.hypot(*values)
            elif rule == "sum_bounds":
                combined = math.fsum(values)
            if combined is not None and not math.isfinite(combined):
                raise OverflowError("nonfinite combined magnitude")
        except OverflowError:
            combined = None
            errors.append("combined magnitude exceeds the finite floating-point range")

    if data.get("status") == "accepted" and (errors or warnings):
        errors.append("accepted uncertainty budget has unresolved errors/warnings")
    return (
        sorted(set(errors)),
        sorted(set(warnings)),
        {"combined_magnitude": combined, "unit": unit},
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("budget", type=Path)
    args = parser.parse_args()
    try:
        data = yaml.safe_load(args.budget.read_text(encoding="utf-8"))
        errors, warnings, summary = validate(data)
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        errors = [f"uncertainty budget parse failed: {exc}"]
        warnings = []
        summary = {"combined_magnitude": None, "unit": None}
    print(
        json.dumps(
            {"ok": not errors, "errors": errors, "warnings": warnings, "summary": summary}, indent=2, allow_nan=False
        )
    )
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

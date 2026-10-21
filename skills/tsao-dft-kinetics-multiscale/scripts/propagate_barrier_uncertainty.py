#!/usr/bin/env python3
"""Propagate a symmetric activation-free-energy bound into a TST rate interval."""

from __future__ import annotations

import argparse
import json

from eyring_rates import concentration_log_factor, rate_unit
from tst_math import rate_from_log, tst_rate_interval


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--barrier", type=float, required=True)
    parser.add_argument("--uncertainty", type=float, required=True)
    parser.add_argument("--temperature", type=float, required=True)
    parser.add_argument("--kappa", type=float, default=1.0)
    parser.add_argument("--degeneracy", type=float, default=1.0)
    parser.add_argument("--molecularity", type=int, default=1)
    parser.add_argument("--standard-state", default="")
    parser.add_argument("--barrier-standard-state", default="")
    parser.add_argument("--activity-convention", default="")
    args = parser.parse_args()
    try:
        interval = tst_rate_interval(
            args.barrier,
            args.uncertainty,
            args.temperature,
            args.kappa,
            args.degeneracy,
        )
        correction = concentration_log_factor(
            args.molecularity, args.standard_state, args.barrier_standard_state, args.activity_convention
        )
        for label in ("central", "lower", "upper"):
            interval[f"{label}_ln_rate"] += correction
            interval[f"{label}_rate"] = rate_from_log(interval[f"{label}_ln_rate"])
        unit = rate_unit(args.molecularity)
    except (ValueError, OverflowError) as exc:
        print(json.dumps({"ok": False, "errors": [str(exc)]}, indent=2))
        return 1

    print(
        json.dumps(
            {
                "ok": True,
                "barrier_kcal_mol": args.barrier,
                "uncertainty_kcal_mol": args.uncertainty,
                "temperature_K": args.temperature,
                **interval,
                "rate_unit": unit,
                "standard_state": args.standard_state,
                "barrier_standard_state": args.barrier_standard_state,
                "activity_convention": args.activity_convention,
                "note": "Interval reflects only the declared barrier bound, not model/transport uncertainty.",
            },
            indent=2,
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

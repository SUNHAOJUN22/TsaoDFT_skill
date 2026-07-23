#!/usr/bin/env python3
"""Extract auditable evidence from Gaussian log files without overclaiming acceptance."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

FLOAT = r"[-+]?\d*\.?\d+(?:[DEde][-+]?\d+)?"


def fnum(value: str) -> float:
    return float(value.replace("D", "E").replace("d", "e"))


def _route_sections(text: str) -> list[str]:
    sections: list[str] = []
    lines = text.splitlines()
    collecting = False
    buf: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            collecting = True
            buf = [stripped]
            continue
        if collecting:
            if not stripped or stripped.startswith("---"):
                if buf:
                    sections.append(" ".join(buf))
                collecting = False
                buf = []
            else:
                buf.append(stripped)
    if collecting and buf:
        sections.append(" ".join(buf))
    return sections


def _error_links(text: str) -> list[str]:
    values = re.findall(r"Error termination via Lnk1e in .*?l(\d+)\.exe", text, flags=re.IGNORECASE)
    return [f"L{value}" for value in values]


def parse_log(text: str) -> dict[str, Any]:
    normal_count = text.count("Normal termination of Gaussian")
    error = "Error termination" in text
    route_sections = _route_sections(text)
    route = route_sections[-1] if route_sections else None

    charge_mult = re.findall(r"Charge\s*=\s*(-?\d+)\s+Multiplicity\s*=\s*(\d+)", text)
    scf = [fnum(x) for x in re.findall(r"SCF Done:\s+E\([^)]*\)\s*=\s*(%s)" % FLOAT, text)]
    frequencies: list[float] = []
    for line in re.findall(r"Frequencies --\s+([^\n]+)", text):
        for token in line.split():
            try:
                frequencies.append(fnum(token))
            except ValueError:
                pass
    imag = [x for x in frequencies if x < -1e-6]

    thermal_patterns = {
        "zero_point_correction_hartree": r"Zero-point correction=\s*(%s)" % FLOAT,
        "thermal_correction_energy_hartree": r"Thermal correction to Energy=\s*(%s)" % FLOAT,
        "thermal_correction_enthalpy_hartree": r"Thermal correction to Enthalpy=\s*(%s)" % FLOAT,
        "thermal_correction_gibbs_hartree": r"Thermal correction to Gibbs Free Energy=\s*(%s)" % FLOAT,
        "sum_electronic_zpe_hartree": r"Sum of electronic and zero-point Energies=\s*(%s)" % FLOAT,
        "sum_electronic_thermal_hartree": r"Sum of electronic and thermal Energies=\s*(%s)" % FLOAT,
        "sum_electronic_enthalpy_hartree": r"Sum of electronic and thermal Enthalpies=\s*(%s)" % FLOAT,
        "sum_electronic_gibbs_hartree": r"Sum of electronic and thermal Free Energies=\s*(%s)" % FLOAT,
    }
    thermal: dict[str, float] = {}
    for key, pattern in thermal_patterns.items():
        values = re.findall(pattern, text)
        if values:
            thermal[key] = fnum(values[-1])

    temperature_matches = re.findall(r"Temperature\s+(%s)\s+Kelvin\.\s+Pressure\s+(%s)\s+Atm" % (FLOAT, FLOAT), text)
    temperature_K = fnum(temperature_matches[-1][0]) if temperature_matches else None
    pressure_atm = fnum(temperature_matches[-1][1]) if temperature_matches else None

    s2 = []
    for before, after in re.findall(r"S\*\*2 before annihilation\s+(%s),\s+after\s+(%s)" % (FLOAT, FLOAT), text):
        s2.append({"before": fnum(before), "after": fnum(after)})

    excited_states = []
    pattern = re.compile(
        r"Excited State\s+(\d+):\s+([^\n]+?)\s+(%s)\s+eV\s+(%s)\s+nm\s+f=(%s)" % (FLOAT, FLOAT, FLOAT)
    )
    for state, label, ev, nm, osc in pattern.findall(text):
        excited_states.append({
            "state": int(state), "label": label.strip(), "energy_eV": fnum(ev),
            "wavelength_nm": fnum(nm), "oscillator_strength": fnum(osc),
        })

    opt_completed = "Optimization completed" in text or "Stationary point found" in text
    convergence_rows = re.findall(
        r"(Maximum Force|RMS\s+Force|Maximum Displacement|RMS\s+Displacement)\s+(%s)\s+(%s)\s+(YES|NO)" % (FLOAT, FLOAT),
        text,
    )
    convergence = [
        {"criterion": name.replace("  ", " "), "value": fnum(value), "threshold": fnum(threshold), "converged": flag == "YES"}
        for name, value, threshold, flag in convergence_rows[-4:]
    ]
    convergence_all_yes = bool(convergence) and all(row["converged"] for row in convergence)

    stable_requested = bool(route and re.search(r"\bstable(?:=|\b)", route, flags=re.IGNORECASE))
    stable_optimized = "The wavefunction is stable under the perturbations considered" in text or "Stable=Opt" in text and normal_count > 0

    irc_points = len(re.findall(r"Point Number\s+\d+\s+in FORWARD path direction|Point Number\s+\d+\s+in REVERSE path direction", text))
    irc_complete = "Calculation of FORWARD path complete" in text or "Calculation of REVERSE path complete" in text

    if normal_count == 0:
        status = "RUN_FAILED" if error else "RUN_INCOMPLETE"
    elif frequencies:
        if len(imag) == 0:
            status = "MINIMUM_CANDIDATE"
        elif len(imag) == 1:
            status = "TS_CANDIDATE"
        else:
            status = "HIGHER_ORDER_SADDLE_CANDIDATE"
    elif excited_states:
        status = "EXCITED_STATE_DATA_COMPLETED"
    else:
        status = "COMPLETED_UNCLASSIFIED"

    warnings: list[str] = []
    if status == "TS_CANDIDATE":
        warnings.append("One imaginary frequency is insufficient: inspect displacement and confirm required IRC endpoints.")
    if status == "MINIMUM_CANDIDATE" and frequencies and min(frequencies) < 20:
        warnings.append("Very low positive modes detected; inspect geometry and qRRHO/low-frequency treatment.")
    if frequencies and not opt_completed and route and "opt" in route.lower():
        warnings.append("Frequency data were found but optimization completion was not detected.")
    if s2:
        warnings.append("Open-shell S^2 values were found; compare with the ideal spin value and assess stability.")
    if stable_requested and not stable_optimized:
        warnings.append("A stability check appears requested but a stable-wavefunction confirmation was not detected.")
    if normal_count > 1:
        warnings.append("Multiple Gaussian jobs/normal terminations detected; extracted values refer to the last matching records.")

    return {
        "status": status,
        "normal_termination": normal_count > 0,
        "normal_termination_count": normal_count,
        "error_termination": error,
        "error_links": _error_links(text),
        "route_sections": route_sections,
        "last_route_section": route,
        "charge": int(charge_mult[-1][0]) if charge_mult else None,
        "multiplicity": int(charge_mult[-1][1]) if charge_mult else None,
        "last_scf_energy_hartree": scf[-1] if scf else None,
        "scf_energy_count": len(scf),
        "optimization_completed": opt_completed,
        "optimization_convergence": convergence,
        "optimization_all_criteria_yes": convergence_all_yes,
        "frequency_count": len(frequencies),
        "imaginary_frequencies_cm-1": imag,
        "lowest_frequencies_cm-1": sorted(frequencies)[:6],
        "temperature_K": temperature_K,
        "pressure_atm": pressure_atm,
        "thermal": thermal,
        "spin_s2": s2[-1] if s2 else None,
        "wavefunction_stability_requested": stable_requested,
        "wavefunction_stable_detected": stable_optimized,
        "excited_states": excited_states,
        "irc_point_records": irc_points,
        "irc_completion_detected": irc_complete,
        "warnings": warnings,
        "scientific_acceptance": "PENDING_HUMAN_OR_CRITIC_REVIEW",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    text = args.log.read_text(encoding="utf-8", errors="replace")
    result = parse_log(text)
    result["source"] = str(args.log.resolve())
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for key, value in result.items():
            print(f"{key}: {value}")
    return 0 if result["normal_termination"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

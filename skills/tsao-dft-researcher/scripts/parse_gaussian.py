#!/usr/bin/env python3
"""Parse Gaussian logs into auditable DFT evidence without claiming scientific acceptance."""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any

FLOAT = r"[-+]?\d*\.?\d+(?:[DEde][-+]?\d+)?"
ATOMIC_SYMBOLS = [
    "X", "H", "He", "Li", "Be", "B", "C", "N", "O", "F", "Ne", "Na", "Mg", "Al", "Si", "P", "S", "Cl", "Ar",
    "K", "Ca", "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn", "Ga", "Ge", "As", "Se", "Br", "Kr",
    "Rb", "Sr", "Y", "Zr", "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd", "In", "Sn", "Sb", "Te", "I", "Xe",
    "Cs", "Ba", "La", "Ce", "Pr", "Nd", "Pm", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu",
    "Hf", "Ta", "W", "Re", "Os", "Ir", "Pt", "Au", "Hg", "Tl", "Pb", "Bi", "Po", "At", "Rn",
]


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


def _error_taxonomy(text: str) -> list[dict[str, str]]:
    rules = [
        ("SCF_CONVERGENCE", r"Convergence failure -- run terminated|SCF has not converged|No convergence is achieved"),
        ("OPTIMIZATION", r"Number of steps exceeded|Optimization stopped|FormBX had a problem|Error in internal coordinate system"),
        ("MEMORY", r"Out-of-memory|Not enough memory|galloc: could not allocate|Erroneous write|malloc failed"),
        ("DISK_OR_IO", r"No space left on device|FileIO operation on non-existent file|Erroneous write|read-write file error"),
        ("GEOMETRY", r"Atoms too close|Problem with the distance matrix|End of file in ZSymb|Linear angle in Bend"),
        ("BASIS_ECP", r"Unrecognized atomic symbol|Atomic number out of range|No basis functions|ECP.*not found|Error reading general basis"),
        ("CHECKPOINT", r"FileIO operation on non-existent file|No data on checkpoint file|GetChg"),
        ("L502", r"l502\.exe"),
        ("L9999", r"l9999\.exe"),
    ]
    out = []
    for category, pattern in rules:
        if re.search(pattern, text, re.IGNORECASE):
            out.append({"category": category, "evidence_pattern": pattern})
    return out


def _gaussian_version(text: str) -> str | None:
    patterns = [
        r"Gaussian\s+16:\s+.*?Revision\s+([A-Z0-9.]+)",
        r"Gaussian\s+16,\s+Revision\s+([A-Z0-9.]+)",
        r"Gaussian\s+(\d+),\s+Revision\s+([A-Z0-9.]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return "Gaussian " + " ".join(match.groups()) if len(match.groups()) > 1 else f"Gaussian 16 Revision {match.group(1)}"
    return None


def _route_metadata(route: str | None) -> dict[str, Any]:
    if not route:
        return {"method": None, "basis": None, "job_types": [], "solvent": None, "dispersion": None, "integration_grid": None}
    cleaned = re.sub(r"^#\s*[pPnNtT]?\s*", "", route).strip()
    method = basis = None
    for token in cleaned.split():
        if "/" in token and not token.lower().startswith(("iop", "scrf", "oniom")):
            left, right = token.split("/", 1)
            if left and right:
                method, basis = left, right.rstrip(",")
                break
    low = route.lower()
    job_types = []
    job_rules = [
        ("optimization", r"\bopt(?:=|\b)"), ("frequency", r"\bfreq(?:=|\b)"),
        ("transition_state", r"opt\s*=\s*\([^)]*\bts\b|opt\s*=\s*ts|\bqst[23]\b"),
        ("irc", r"\birc(?:=|\b)"), ("td_dft", r"\btd(?:=|\b)|\btddft\b"),
        ("nmr", r"\bnmr(?:=|\b)"), ("stability", r"\bstable(?:=|\b)"),
        ("population", r"\bpop(?:=|\b)"), ("single_point", r"\bsp\b"),
        ("scan", r"modredundant|\bscan\b"), ("counterpoise", r"counterpoise"),
    ]
    for name, pattern in job_rules:
        if re.search(pattern, low):
            job_types.append(name)
    solvent = None
    match = re.search(r"scrf\s*=\s*\(([^)]*)\)|scrf\s*=\s*([^\s]+)", route, re.IGNORECASE)
    if match:
        raw = next((x for x in match.groups() if x), "")
        sm = re.search(r"solvent\s*=\s*([^,\s)]+)", raw, re.IGNORECASE)
        solvent = sm.group(1) if sm else raw
    dispersion = None
    dm = re.search(r"empiricaldispersion\s*=\s*([^\s,)]+)|\b(d3bj|gd3bj|d3|gd3)\b", route, re.IGNORECASE)
    if dm:
        dispersion = next(x for x in dm.groups() if x)
    grid = None
    gm = re.search(r"(?:int|integral)\s*=\s*(?:\(([^)]*)\)|([^\s]+))", route, re.IGNORECASE)
    if gm:
        grid = next((x for x in gm.groups() if x), None)
    return {"method": method, "basis": basis, "job_types": job_types, "solvent": solvent, "dispersion": dispersion, "integration_grid": grid}


def _orientation_blocks(text: str) -> list[list[dict[str, Any]]]:
    blocks: list[list[dict[str, Any]]] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        if "Standard orientation:" in lines[i] or "Input orientation:" in lines[i]:
            i += 1
            dash_count = 0
            while i < len(lines):
                if re.match(r"\s*-{5,}\s*$", lines[i]):
                    dash_count += 1
                    if dash_count == 2:
                        i += 1
                        break
                i += 1
            atoms: list[dict[str, Any]] = []
            while i < len(lines) and not re.match(r"\s*-{5,}\s*$", lines[i]):
                parts = lines[i].split()
                if len(parts) >= 6 and all(re.match(r"^-?\d+$", p) for p in parts[:3]):
                    try:
                        center, atomic_number = int(parts[0]), int(parts[1])
                        x, y, z = map(float, parts[-3:])
                        symbol = ATOMIC_SYMBOLS[atomic_number] if 0 <= atomic_number < len(ATOMIC_SYMBOLS) else str(atomic_number)
                        atoms.append({"center": center, "atomic_number": atomic_number, "element": symbol, "x_angstrom": x, "y_angstrom": y, "z_angstrom": z})
                    except ValueError:
                        pass
                i += 1
            if atoms:
                blocks.append(atoms)
        i += 1
    return blocks


def _orbital_energies(text: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    channels = {
        "alpha_occ_hartree": r"Alpha\s+occ\. eigenvalues --\s+([^\n]+)",
        "alpha_virt_hartree": r"Alpha\s+virt\. eigenvalues --\s+([^\n]+)",
        "beta_occ_hartree": r"Beta\s+occ\. eigenvalues --\s+([^\n]+)",
        "beta_virt_hartree": r"Beta\s+virt\. eigenvalues --\s+([^\n]+)",
    }
    for key, pattern in channels.items():
        vals: list[float] = []
        for line in re.findall(pattern, text):
            for token in line.split():
                try:
                    vals.append(fnum(token))
                except ValueError:
                    pass
        if vals:
            result[key] = vals
    if result.get("alpha_occ_hartree"):
        result["alpha_homo_hartree"] = result["alpha_occ_hartree"][-1]
    if result.get("alpha_virt_hartree"):
        result["alpha_lumo_hartree"] = result["alpha_virt_hartree"][0]
    if result.get("beta_occ_hartree"):
        result["beta_homo_hartree"] = result["beta_occ_hartree"][-1]
    if result.get("beta_virt_hartree"):
        result["beta_lumo_hartree"] = result["beta_virt_hartree"][0]
    return result


def _dipole(text: str) -> dict[str, float] | None:
    matches = re.findall(
        r"Dipole moment \(field-independent basis, Debye\):\s*\n\s*X=\s*(%s)\s+Y=\s*(%s)\s+Z=\s*(%s)\s+Tot=\s*(%s)" % (FLOAT, FLOAT, FLOAT, FLOAT),
        text,
    )
    if not matches:
        return None
    x, y, z, total = matches[-1]
    return {"x_debye": fnum(x), "y_debye": fnum(y), "z_debye": fnum(z), "total_debye": fnum(total)}


def _nmr_shieldings(text: str) -> list[dict[str, Any]]:
    values = []
    pattern = re.compile(r"^\s*(\d+)\s+([A-Za-z]{1,2})\s+Isotropic\s*=\s*(%s)\s+Anisotropy\s*=\s*(%s)" % (FLOAT, FLOAT), re.MULTILINE)
    for idx, element, iso, aniso in pattern.findall(text):
        values.append({"atom_index": int(idx), "element": element, "isotropic_ppm": fnum(iso), "anisotropy_ppm": fnum(aniso)})
    return values


def _excited_states(text: str) -> list[dict[str, Any]]:
    lines = text.splitlines()
    output: list[dict[str, Any]] = []
    header = re.compile(r"Excited State\s+(\d+):\s+(.+?)\s+(%s)\s+eV\s+(%s)\s+nm\s+f=(%s)" % (FLOAT, FLOAT, FLOAT))
    contribution = re.compile(r"\s*(\d+)([AB])?\s*->\s*(\d+)([AB])?\s+(%s)" % FLOAT)
    i = 0
    while i < len(lines):
        match = header.search(lines[i])
        if not match:
            i += 1
            continue
        state, label, ev, nm, osc = match.groups()
        item = {"state": int(state), "label": label.strip(), "energy_eV": fnum(ev), "wavelength_nm": fnum(nm), "oscillator_strength": fnum(osc), "contributions": []}
        j = i + 1
        while j < len(lines) and j <= i + 30:
            cm = contribution.match(lines[j])
            if cm:
                src, src_spin, dst, dst_spin, coeff = cm.groups()
                item["contributions"].append({"from_orbital": int(src), "from_spin": src_spin or None, "to_orbital": int(dst), "to_spin": dst_spin or None, "coefficient": fnum(coeff)})
            elif lines[j].strip().startswith("Excited State") or (not lines[j].strip() and item["contributions"]):
                break
            j += 1
        output.append(item)
        i = j
    return output


def parse_log(text: str) -> dict[str, Any]:
    normal_count = text.count("Normal termination of Gaussian")
    error = "Error termination" in text
    route_sections = _route_sections(text)
    route = route_sections[-1] if route_sections else None
    route_meta = _route_metadata(route)

    charge_mult = re.findall(r"Charge\s*=\s*(-?\d+)\s+Multiplicity\s*=\s*(\d+)", text)
    charge = int(charge_mult[-1][0]) if charge_mult else None
    multiplicity = int(charge_mult[-1][1]) if charge_mult else None
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
    spin_diag = s2[-1] if s2 else None
    if spin_diag and multiplicity:
        spin = (multiplicity - 1) / 2
        ideal = spin * (spin + 1)
        spin_diag = {**spin_diag, "ideal": ideal, "after_minus_ideal": spin_diag["after"] - ideal}

    excited_states = _excited_states(text)
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
    stable_optimized = bool(re.search(r"wavefunction is stable under the perturbations considered|wavefunction is stable", text, re.IGNORECASE))

    forward_points = len(re.findall(r"Point Number\s+\d+\s+in FORWARD path direction", text))
    reverse_points = len(re.findall(r"Point Number\s+\d+\s+in REVERSE path direction", text))
    forward_complete = bool(re.search(r"Calculation of FORWARD path complete", text, re.IGNORECASE))
    reverse_complete = bool(re.search(r"Calculation of REVERSE path complete", text, re.IGNORECASE))

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
    if spin_diag:
        warnings.append("Open-shell S^2 values were found; compare after-annihilation S^2 with the ideal value and run stability checks when needed.")
        if abs(spin_diag.get("after_minus_ideal", 0.0)) > 0.2:
            warnings.append("Substantial post-annihilation spin contamination may be present.")
    if stable_requested and not stable_optimized:
        warnings.append("A stability check appears requested but a stable-wavefunction confirmation was not detected.")
    if normal_count > 1:
        warnings.append("Multiple Gaussian jobs/normal terminations detected; extracted scalar values use the last matching record.")
    if route_meta["method"] is None or route_meta["basis"] is None:
        warnings.append("Method/basis could not be inferred reliably from the last route section.")
    if route_meta["job_types"] and "irc" in route_meta["job_types"] and not (forward_complete or reverse_complete):
        warnings.append("IRC route detected but no completed path direction was found.")

    orientations = _orientation_blocks(text)
    return {
        "status": status,
        "gaussian_version": _gaussian_version(text),
        "normal_termination": normal_count > 0,
        "normal_termination_count": normal_count,
        "error_termination": error,
        "error_links": _error_links(text),
        "error_taxonomy": _error_taxonomy(text),
        "route_sections": route_sections,
        "last_route_section": route,
        "route_metadata": route_meta,
        "charge": charge,
        "multiplicity": multiplicity,
        "last_scf_energy_hartree": scf[-1] if scf else None,
        "scf_energy_count": len(scf),
        "optimization_completed": opt_completed,
        "optimization_convergence": convergence,
        "optimization_all_criteria_yes": convergence_all_yes,
        "frequency_count": len(frequencies),
        "imaginary_frequencies_cm-1": imag,
        "lowest_frequencies_cm-1": sorted(frequencies)[:9],
        "temperature_K": temperature_K,
        "pressure_atm": pressure_atm,
        "thermal": thermal,
        "spin_s2": spin_diag,
        "wavefunction_stability_requested": stable_requested,
        "wavefunction_stable_detected": stable_optimized,
        "orbital_energies": _orbital_energies(text),
        "dipole_moment": _dipole(text),
        "nmr_shieldings": _nmr_shieldings(text),
        "excited_states": excited_states,
        "irc": {
            "forward_point_records": forward_points,
            "reverse_point_records": reverse_points,
            "forward_completion_detected": forward_complete,
            "reverse_completion_detected": reverse_complete,
        },
        "final_coordinates": orientations[-1] if orientations else [],
        "orientation_block_count": len(orientations),
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

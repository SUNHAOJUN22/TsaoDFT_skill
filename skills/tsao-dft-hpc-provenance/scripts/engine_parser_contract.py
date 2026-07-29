#!/usr/bin/env python3
"""Unified fail-closed parser state machines for Gaussian, VASP, QE and CP2K."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

PARSER_VERSION = "1.0"
HARTREE_TO_EV = 27.211386245988
RY_TO_EV = 13.605693122994
RY_BOHR_TO_EV_ANGSTROM = 25.71104309541616
KBAR_TO_GPA = 0.1


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def base_result(engine: str, path: Path) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "engine": engine,
        "engine_version": None,
        "parser_version": PARSER_VERSION,
        "source_artifact": {"path": path.name, "sha256": None},
        "normal_termination": False,
        "fatal_marker": None,
        "electronic_converged": False,
        "geometry_converged": None,
        "parser_accepted": False,
        "parser_acceptance_reasons": [],
        "energy": {"value": None, "unit": "eV"},
        "forces": {"values": None, "unit": "eV/angstrom"},
        "stress": {"values": None, "unit": "GPa"},
        "scf_iterations": None,
        "elapsed_time_s": None,
        "warnings": [],
        "failed_stage": None,
        "scientific_acceptance": "PENDING",
        "job_index": None,
    }


def missing_result(engine: str, path: Path) -> dict[str, Any]:
    result = base_result(engine, path)
    result["fatal_marker"] = "SOURCE_MISSING"
    result["failed_stage"] = "input"
    result["parser_acceptance_reasons"] = ["source output is missing or empty"]
    return result


def _finalize(result: dict[str, Any], path: Path) -> dict[str, Any]:
    if path.is_file() and path.stat().st_size:
        result["source_artifact"]["sha256"] = sha256_file(path)
    result["parser_acceptance_reasons"] = sorted(set(result["parser_acceptance_reasons"]))
    result["warnings"] = sorted(set(result["warnings"]))
    return result


def _numbers(text: str) -> list[float]:
    return [
        float(value.replace("D", "E").replace("d", "e"))
        for value in re.findall(r"[-+]?\d*\.?\d+(?:[DEde][-+]?\d+)?", text)
    ]


def parse_gaussian(path: Path) -> dict[str, Any]:
    if not path.is_file() or not path.stat().st_size:
        return missing_result("gaussian", path)
    text = path.read_text(encoding="utf-8", errors="replace")
    sections = re.split(r"(?=Entering Link 1)", text)
    if not sections:
        sections = [text]
    final = sections[-1]
    result = base_result("gaussian", path)
    result["job_index"] = len(sections)
    version = re.search(r"Gaussian\s+(?:16[:,]?\s*)?.*?Revision\s+([A-Z0-9.]+)", final, re.IGNORECASE)
    result["engine_version"] = version.group(1) if version else None
    normal = "Normal termination of Gaussian" in final
    error = "Error termination" in final
    result["normal_termination"] = normal and not error
    result["fatal_marker"] = "ERROR_TERMINATION" if error else None
    scf_values = re.findall(r"SCF Done:\s+E\([^)]*\)\s*=\s*([-+]?\d*\.?\d+(?:[DEde][-+]?\d+)?)", final)
    if scf_values:
        result["energy"]["value"] = float(scf_values[-1].replace("D", "E").replace("d", "e")) * HARTREE_TO_EV
        result["electronic_converged"] = True
        result["scf_iterations"] = len(scf_values)
    route = " ".join(line.strip() for line in final.splitlines() if line.lstrip().startswith("#"))
    frequencies = []
    for line in re.findall(r"Frequencies --\s+([^\n]+)", final):
        frequencies.extend(_numbers(line))
    imag = [value for value in frequencies if value < -1e-6]
    geometry = "Optimization completed" in final or "Stationary point found" in final
    result["geometry_converged"] = geometry if "opt" in route.lower() else None
    if error:
        result["failed_stage"] = "engine"
        result["parser_acceptance_reasons"].append("final Link1 job ended with error termination")
    elif not normal:
        result["failed_stage"] = "termination"
        result["parser_acceptance_reasons"].append("final Link1 job lacks normal termination")
    elif "opt" in route.lower() and not geometry:
        result["failed_stage"] = "geometry"
        result["parser_acceptance_reasons"].append("optimization route lacks completion marker")
    elif "freq" in route.lower() and len(imag) > 1:
        result["failed_stage"] = "scientific-gate"
        result["parser_acceptance_reasons"].append("frequency result is a higher-order saddle candidate")
    else:
        result["parser_accepted"] = True
        result["parser_acceptance_reasons"].append("final Link1 job passed termination and route-specific gates")
    if len(sections) > 1:
        result["warnings"].append("multiple Link1 jobs detected; only the final job determines acceptance")
    return _finalize(result, path)


def parse_vasp(path: Path) -> dict[str, Any]:
    if not path.is_file() or not path.stat().st_size:
        return missing_result("vasp", path)
    text = path.read_text(encoding="utf-8", errors="replace")
    result = base_result("vasp", path)
    version = re.search(r"vasp\.([\d.]+)", text, re.IGNORECASE)
    result["engine_version"] = version.group(1) if version else None
    fatal_rules = (
        ("BRMIX_FATAL", r"BRMIX: very serious problems"),
        ("ZBRENT_FATAL", r"ZBRENT: fatal error"),
        ("DIAGONALIZATION_FATAL", r"EDDDAV: Call to ZHEGV failed"),
        ("SUBSPACE_FATAL", r"Sub-Space-Matrix is not hermitian"),
    )
    for label, pattern in fatal_rules:
        if re.search(pattern, text, re.IGNORECASE):
            result["fatal_marker"] = label
            result["parser_acceptance_reasons"].append(f"fatal VASP marker detected: {label}")
            break
    normal = "General timing and accounting informations for this job" in text
    electronic = "EDIFF is reached" in text or "aborting loop because EDIFF is reached" in text
    geometry = "reached required accuracy - stopping structural energy minimisation" in text
    result["normal_termination"] = normal and result["fatal_marker"] is None
    result["electronic_converged"] = electronic
    result["geometry_converged"] = geometry
    energies = re.findall(r"free\s+energy\s+TOTEN\s*=\s*([-+]?\d*\.?\d+(?:[Ee][-+]?\d+)?)\s+eV", text)
    if energies:
        result["energy"]["value"] = float(energies[-1])
        result["scf_iterations"] = len(energies)
    elapsed = re.findall(r"Elapsed time \(sec\):\s*([-+]?\d*\.?\d+)", text)
    result["elapsed_time_s"] = float(elapsed[-1]) if elapsed else None
    force_blocks = list(re.finditer(r"TOTAL-FORCE \(eV/Angst\)(.*?)(?:total drift|$)", text, re.DOTALL))
    if force_blocks:
        vector: list[float] = []
        for line in force_blocks[-1].group(1).splitlines():
            fields = line.split()
            if len(fields) >= 6:
                try:
                    vector.extend(float(value) for value in fields[-3:])
                except ValueError:
                    continue
        result["forces"]["values"] = vector or None
    if result["fatal_marker"]:
        result["failed_stage"] = "engine"
    elif not normal:
        result["failed_stage"] = "termination"
        result["parser_acceptance_reasons"].append("VASP timing/accounting termination marker is missing")
    elif not electronic:
        result["failed_stage"] = "electronic"
        result["parser_acceptance_reasons"].append("electronic convergence marker is missing")
    else:
        result["parser_accepted"] = True
        result["parser_acceptance_reasons"].append("termination and electronic convergence gates passed")
    return _finalize(result, path)


def parse_qe(path: Path) -> dict[str, Any]:
    if not path.is_file() or not path.stat().st_size:
        return missing_result("quantum-espresso", path)
    text = path.read_text(encoding="utf-8", errors="replace")
    result = base_result("quantum-espresso", path)
    version = re.search(r"Program PWSCF v\.([\w.\-]+)", text)
    result["engine_version"] = version.group(1) if version else None
    routine_error = re.search(r"Error in routine", text, re.IGNORECASE) is not None
    nonconverged = "convergence NOT achieved" in text
    done = "JOB DONE." in text
    result["fatal_marker"] = "ERROR_IN_ROUTINE" if routine_error else "SCF_NOT_CONVERGED" if nonconverged else None
    result["normal_termination"] = done and result["fatal_marker"] is None
    result["electronic_converged"] = "convergence has been achieved" in text and not nonconverged
    result["geometry_converged"] = (
        "End of BFGS Geometry Optimization" in text or re.search(r"bfgs converged in", text, re.IGNORECASE) is not None
    )
    energies = re.findall(r"!\s+total energy\s+=\s*([-+]?\d*\.?\d+(?:[Ee][-+]?\d+)?)\s+Ry", text)
    if energies:
        result["energy"]["value"] = float(energies[-1]) * RY_TO_EV
        result["scf_iterations"] = len(energies)
    force = re.findall(r"Total force =\s*([-+]?\d*\.?\d+(?:[Ee][-+]?\d+)?)", text)
    if force:
        result["forces"]["values"] = [float(force[-1]) * RY_BOHR_TO_EV_ANGSTROM]
    pressure = re.findall(r"P=\s*([-+]?\d*\.?\d+(?:[Ee][-+]?\d+)?)", text)
    if pressure:
        result["stress"]["values"] = [float(pressure[-1]) * KBAR_TO_GPA]
    if result["fatal_marker"]:
        result["failed_stage"] = "engine" if routine_error else "electronic"
        result["parser_acceptance_reasons"].append(f"QE fatal marker detected: {result['fatal_marker']}")
    elif not done:
        result["failed_stage"] = "termination"
        result["parser_acceptance_reasons"].append("JOB DONE marker is missing")
    elif not result["electronic_converged"]:
        result["failed_stage"] = "electronic"
        result["parser_acceptance_reasons"].append("SCF convergence marker is missing")
    else:
        result["parser_accepted"] = True
        result["parser_acceptance_reasons"].append("termination and SCF gates passed")
    return _finalize(result, path)


def parse_cp2k(path: Path) -> dict[str, Any]:
    if not path.is_file() or not path.stat().st_size:
        return missing_result("cp2k", path)
    text = path.read_text(encoding="utf-8", errors="replace")
    result = base_result("cp2k", path)
    version = re.search(r"CP2K\| version string:\s*(.+)", text)
    result["engine_version"] = version.group(1).strip() if version else None
    abort = re.search(r"\bABORT\b", text) is not None
    nonconverged = "SCF run NOT converged" in text
    ended = "PROGRAM ENDED AT" in text
    result["fatal_marker"] = "ABORT" if abort else "SCF_NOT_CONVERGED" if nonconverged else None
    result["normal_termination"] = ended and result["fatal_marker"] is None
    result["electronic_converged"] = "SCF run converged" in text and not nonconverged
    result["geometry_converged"] = (
        "GEOMETRY OPTIMIZATION COMPLETED" in text or "Reevaluating energy at the minimum" in text
    )
    energies = re.findall(r"ENERGY\| Total FORCE_EVAL.*?energy \(a\.u\.\):\s*([-+]?\d*\.?\d+(?:[Ee][-+]?\d+)?)", text)
    if energies:
        result["energy"]["value"] = float(energies[-1]) * HARTREE_TO_EV
        result["scf_iterations"] = len(energies)
    gradients = re.findall(r"Max\. gradient\s*=\s*([-+]?\d*\.?\d+(?:[Ee][-+]?\d+)?)", text)
    if gradients:
        result["forces"]["values"] = [float(gradients[-1]) * HARTREE_TO_EV / 0.529177210903]
    if result["fatal_marker"]:
        result["failed_stage"] = "engine" if abort else "electronic"
        result["parser_acceptance_reasons"].append(f"CP2K fatal marker detected: {result['fatal_marker']}")
    elif not ended:
        result["failed_stage"] = "termination"
        result["parser_acceptance_reasons"].append("PROGRAM ENDED AT marker is missing")
    elif not result["electronic_converged"]:
        result["failed_stage"] = "electronic"
        result["parser_acceptance_reasons"].append("SCF convergence marker is missing")
    else:
        result["parser_accepted"] = True
        result["parser_acceptance_reasons"].append("termination and SCF gates passed")
    return _finalize(result, path)


def parse_engine_output(engine: str, path: Path) -> dict[str, Any]:
    routes = {
        "gaussian": parse_gaussian,
        "vasp": parse_vasp,
        "quantum-espresso": parse_qe,
        "cp2k": parse_cp2k,
    }
    if engine not in routes:
        raise ValueError(f"unsupported engine parser: {engine}")
    return routes[engine](path)

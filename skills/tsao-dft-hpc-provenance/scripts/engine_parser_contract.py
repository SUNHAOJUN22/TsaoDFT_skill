#!/usr/bin/env python3
"""Unified fail-closed parser state machines for Gaussian, VASP, QE and CP2K."""

from __future__ import annotations

import importlib.util
import math
import mmap
import re
import sys
from pathlib import Path
from typing import Any

PARSER_VERSION = "1.2"
HARTREE_TO_EV = 27.211386245988
RY_TO_EV = 13.605693122994
BOHR_TO_ANGSTROM = 0.529177210903
RY_BOHR_TO_EV_ANGSTROM = RY_TO_EV / BOHR_TO_ANGSTROM
KBAR_TO_GPA = 0.1
FLOAT = rb"[-+]?\d*\.?\d+(?:[DEde][-+]?\d+)?"


def _load_scan_core() -> Any:
    path = Path(__file__).with_name("engine_scan_core.py")
    spec = importlib.util.spec_from_file_location("tsao_engine_scan_core", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_SCAN = _load_scan_core()

GAUSSIAN_VERSION_RE = re.compile(rb"Gaussian\s+(?:16[:,]?\s*)?.*?Revision\s+([A-Z0-9.]+)", re.IGNORECASE)
GAUSSIAN_SCF_RE = re.compile(rb"SCF Done:\s+E\([^)]*\)\s*=\s*(" + FLOAT + rb")")
GAUSSIAN_FREQUENCY_RE = re.compile(rb"Frequencies --\s+([^\r\n]+)")
GAUSSIAN_OPT_ROUTE_RE = re.compile(rb"\bopt(?:\s*=|\b)", re.IGNORECASE)
GAUSSIAN_FREQ_ROUTE_RE = re.compile(rb"\bfreq(?:\s*=|\b)", re.IGNORECASE)
VASP_VERSION_RE = re.compile(rb"(?im)^[ \t]*vasp\.([\d.]+)")
VASP_ENERGY_RE = re.compile(rb"free\s+energy\s+TOTEN\s*=\s*(" + FLOAT + rb")\s+eV", re.IGNORECASE)
VASP_SCF_ITERATION_RE = re.compile(rb"(?im)^[ \t]*(?:DAV|RMM|CG|SDA|CGA|DMP|DIA):[ \t]*(\d+)(?:[ \t]|$)")
VASP_ELAPSED_RE = re.compile(rb"Elapsed time \(sec\):\s*(" + FLOAT + rb")")
QE_VERSION_RE = re.compile(rb"Program PWSCF v\.([\w.\-]+)")
QE_ERROR_RE = re.compile(rb"Error in routine", re.IGNORECASE)
QE_BFGS_CONVERGED_RE = re.compile(rb"bfgs converged in", re.IGNORECASE)
QE_ENERGY_RE = re.compile(rb"!\s+total energy\s+=\s*(" + FLOAT + rb")\s+Ry")
QE_SCF_ITERATION_RE = re.compile(rb"(?im)^[ \t]*iteration[ \t]*#[ \t]*(\d+)(?:[ \t]|$)")
QE_FORCE_BLOCK_RE = re.compile(rb"(?im)^[ \t]*Forces acting on atoms[^\r\n]*")
QE_FORCE_UNIT_RE = re.compile(rb"\bRy/au\b", re.IGNORECASE)
QE_ATOM_COUNT_RE = re.compile(rb"(?im)^[ \t]*number of atoms/cell[ \t]*=[ \t]*(\d+)[ \t]*\r?$")
QE_ATOM_FORCE_RE = re.compile(
    rb"(?im)^[ \t]*atom[ \t]+(\d+)[ \t]+type[ \t]+\d+[ \t]+force[ \t]*=[ \t]*("
    + FLOAT
    + rb")[ \t]+("
    + FLOAT
    + rb")[ \t]+("
    + FLOAT
    + rb")[ \t]*(?:\r?$)"
)
QE_TOTAL_FORCE_RE = re.compile(rb"(?im)^[ \t]*Total force[ \t]*=[ \t]*(" + FLOAT + rb")")
QE_PRESSURE_RE = re.compile(rb"P=\s*(" + FLOAT + rb")")
CP2K_VERSION_RE = re.compile(rb"CP2K\| version string:\s*([^\r\n]+)")
CP2K_ENERGY_RE = re.compile(rb"ENERGY\| Total FORCE_EVAL.*?energy \(a\.u\.\):\s*(" + FLOAT + rb")")
CP2K_GRADIENT_RE = re.compile(rb"Max\. gradient\s*=\s*(" + FLOAT + rb")")
CP2K_SCF_STEPS_RE = re.compile(
    rb"(?im)^[ \t]*(?:\*+[ \t]*)?SCF run (?:NOT )?converged"
    rb"(?:[ \t]+in[ \t]+(\d+)[ \t]+steps\b)?"
)


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Compatibility entry point for the shared bounded artifact hasher."""

    result = _SCAN.sha256_file(path, chunk_size=chunk_size)
    if not isinstance(result, str):
        raise TypeError("shared scanner must return a SHA-256 string")
    if re.fullmatch(r"[0-9a-f]{64}", result) is None:
        raise ValueError("shared scanner returned an invalid SHA-256 digest")
    return result


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


def _finalize(result: dict[str, Any], artifact: Any) -> dict[str, Any]:
    if isinstance(artifact, Path):
        digest = sha256_file(artifact) if artifact.is_file() else None
    else:
        digest = getattr(artifact, "sha256", None)
    result["source_artifact"]["sha256"] = digest
    result["parser_acceptance_reasons"] = sorted(set(result["parser_acceptance_reasons"]))
    result["warnings"] = sorted(set(result["warnings"]))
    return result


class NumericRangeError(ValueError):
    """A parsed engine quantity cannot be represented without numeric data loss."""


def _float(value: bytes, *, factor: float = 1.0) -> float:
    token = value.replace(b"D", b"E").replace(b"d", b"e")
    parsed = float(token)
    if not math.isfinite(parsed):
        raise NumericRangeError("engine output contains a non-finite numeric value")
    if parsed == 0 and any(digit in b"123456789" for digit in token.lower().split(b"e", 1)[0]):
        raise NumericRangeError("non-zero engine numeric value underflows the finite range")
    converted = parsed * factor
    if not math.isfinite(converted) or (parsed != 0 and converted == 0):
        raise NumericRangeError("engine numeric unit conversion exceeds the finite range")
    return converted


def _numbers(text: bytes) -> list[float]:
    return [_float(value) for value in re.findall(FLOAT, text)]


def _parse_force_block(data: mmap.mmap, bounds: tuple[int, int] | None) -> list[float] | None:
    if bounds is None:
        return None
    vector: list[float] = []
    start, end = bounds
    for line in data[start:end].splitlines():
        fields = line.split()
        if len(fields) < 6:
            continue
        try:
            vector.extend(_float(value) for value in fields[-3:])
        except NumericRangeError:
            raise
        except ValueError:
            continue
    return vector or None


def _parse_qe_forces(data: mmap.mmap, job_start: int) -> tuple[list[float] | None, str | None]:
    """Return the final complete QE per-atom force vector in atom-index order.

    QE's ``Total force`` line is a scalar norm, not a force vector. A block is
    emitted only when its atom count, unique 1..N indices, three components per
    atom and closing summary are all present in the final PWSCF job.
    """

    latest_header = None
    for match in QE_FORCE_BLOCK_RE.finditer(data, job_start):
        latest_header = match
    if latest_header is None:
        total_force, _ = _SCAN.last_group(data, QE_TOTAL_FORCE_RE, start=job_start)
        if total_force is not None:
            _float(total_force, factor=RY_BOHR_TO_EV_ANGSTROM)
            return None, "QE Total force is a scalar summary; no per-atom force vector is available"
        return None, None
    if QE_FORCE_UNIT_RE.search(latest_header.group(0)) is None:
        return None, "QE final per-atom force block has an unsupported or missing unit; force vector is unavailable"

    natom_match = None
    for match in QE_ATOM_COUNT_RE.finditer(data, job_start, latest_header.start()):
        natom_match = match
    if natom_match is None:
        return None, "QE per-atom force block has no preceding atom count; force vector is unavailable"
    try:
        natom = int(natom_match.group(1))
    except ValueError:
        return None, "QE per-atom force block has an invalid atom count; force vector is unavailable"
    if natom < 1:
        return None, "QE per-atom force block has an invalid atom count; force vector is unavailable"

    closing = QE_TOTAL_FORCE_RE.search(data, latest_header.end())
    if closing is None:
        return None, "QE final per-atom force block is incomplete; force vector is unavailable"
    _float(closing.group(1), factor=RY_BOHR_TO_EV_ANGSTROM)

    components_by_atom: dict[int, tuple[float, float, float]] = {}
    for match in QE_ATOM_FORCE_RE.finditer(data, latest_header.end(), closing.start()):
        try:
            atom_index = int(match.group(1))
        except ValueError:
            return None, "QE final per-atom force block has an invalid atom index; force vector is unavailable"
        if atom_index in components_by_atom:
            return None, "QE final per-atom force block has duplicate atom indices; force vector is unavailable"
        components_by_atom[atom_index] = (
            _float(match.group(2), factor=RY_BOHR_TO_EV_ANGSTROM),
            _float(match.group(3), factor=RY_BOHR_TO_EV_ANGSTROM),
            _float(match.group(4), factor=RY_BOHR_TO_EV_ANGSTROM),
        )

    if (
        len(components_by_atom) != natom
        or min(components_by_atom, default=0) != 1
        or max(components_by_atom, default=0) != natom
    ):
        return None, "QE final per-atom force block does not contain exactly one 3-component row for every atom"
    return [value for atom_index in range(1, natom + 1) for value in components_by_atom[atom_index]], None


def _last_route_section(lines: list[bytes]) -> bytes | None:
    """Collect the last Gaussian route section, including unprefixed continuations."""
    sections: list[bytes] = []
    collecting = False
    current: list[bytes] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(b"#"):
            if collecting:
                sections.append(b" ".join(current))
            collecting = True
            current = [stripped]
        elif collecting:
            if not stripped or stripped.startswith(b"---"):
                sections.append(b" ".join(current))
                collecting = False
                current = []
            else:
                current.append(stripped)
    if current:
        sections.append(b" ".join(current))
    return sections[-1] if sections else None


def parse_gaussian(path: Path) -> dict[str, Any]:
    with _SCAN.mapped_artifact(path) as artifact:
        if artifact is None:
            return missing_result("gaussian", path)
        data = artifact.data
        final_start = data.rfind(b"Entering Link 1")
        final_start = 0 if final_start < 0 else final_start
        result = base_result("gaussian", path)
        result["job_index"] = _SCAN.count(data, b"Entering Link 1") + 1
        result["engine_version"] = _SCAN.decode(_SCAN.first_group(data, GAUSSIAN_VERSION_RE, start=final_start))
        normal = _SCAN.contains(data, b"Normal termination of Gaussian", start=final_start)
        error = _SCAN.contains(data, b"Error termination", start=final_start)
        result["normal_termination"] = normal and not error
        result["fatal_marker"] = "ERROR_TERMINATION" if error else None

        scf_values = _SCAN.all_groups(data, GAUSSIAN_SCF_RE, start=final_start)
        if scf_values:
            result["energy"]["value"] = _float(scf_values[-1], factor=HARTREE_TO_EV)
            result["electronic_converged"] = True
            result["scf_iterations"] = len(scf_values)

        final_lines = data[final_start:].splitlines()
        route = _last_route_section(final_lines)
        route_bytes = route or b""
        opt_requested = GAUSSIAN_OPT_ROUTE_RE.search(route_bytes) is not None
        freq_requested = GAUSSIAN_FREQ_ROUTE_RE.search(route_bytes) is not None
        frequencies: list[float] = []
        for value in _SCAN.all_groups(data, GAUSSIAN_FREQUENCY_RE, start=final_start):
            frequencies.extend(_numbers(value))
        imaginary = [value for value in frequencies if value < -1e-6]
        geometry = _SCAN.contains(data, b"Optimization completed", start=final_start) or _SCAN.contains(
            data,
            b"Stationary point found",
            start=final_start,
        )
        result["geometry_converged"] = geometry if opt_requested else None
        if error:
            result["failed_stage"] = "engine"
            result["parser_acceptance_reasons"].append("final Link1 job ended with error termination")
        elif not normal:
            result["failed_stage"] = "termination"
            result["parser_acceptance_reasons"].append("final Link1 job lacks normal termination")
        elif route is None:
            result["failed_stage"] = "input"
            result["parser_acceptance_reasons"].append("final Link1 job lacks a Gaussian route section")
        elif not scf_values:
            result["failed_stage"] = "electronic"
            result["parser_acceptance_reasons"].append("final Link1 job lacks a converged SCF energy record")
        elif opt_requested and not geometry:
            result["failed_stage"] = "geometry"
            result["parser_acceptance_reasons"].append("optimization route lacks completion marker")
        elif freq_requested and not frequencies:
            result["failed_stage"] = "scientific-gate"
            result["parser_acceptance_reasons"].append("frequency route lacks parsed frequency records")
        elif freq_requested and len(imaginary) > 1:
            result["failed_stage"] = "scientific-gate"
            result["parser_acceptance_reasons"].append("frequency result is a higher-order saddle candidate")
        else:
            result["parser_accepted"] = True
            result["parser_acceptance_reasons"].append("final Link1 job passed termination and route-specific gates")
        if result["job_index"] > 1:
            result["warnings"].append("multiple Link1 jobs detected; only the final job determines acceptance")
        return _finalize(result, artifact)


def parse_vasp(path: Path) -> dict[str, Any]:
    with _SCAN.mapped_artifact(path) as artifact:
        if artifact is None:
            return missing_result("vasp", path)
        data = artifact.data
        result = base_result("vasp", path)
        starts = _SCAN.job_start_positions(data, "vasp")
        job_start = starts[-1]
        versions = tuple(VASP_VERSION_RE.finditer(data, job_start))
        result["engine_version"] = _SCAN.decode(versions[-1].group(1) if versions else None)
        result["job_index"] = len(starts)
        if len(starts) > 1:
            result["warnings"].append("multiple VASP runs detected; only the final run determines acceptance")
        fatal_rules = (
            ("BRMIX_FATAL", re.compile(rb"BRMIX: very serious problems", re.IGNORECASE)),
            ("ZBRENT_FATAL", re.compile(rb"ZBRENT: fatal error", re.IGNORECASE)),
            ("DIAGONALIZATION_FATAL", re.compile(rb"EDDDAV: Call to ZHEGV failed", re.IGNORECASE)),
            ("SUBSPACE_FATAL", re.compile(rb"Sub-Space-Matrix is not hermitian", re.IGNORECASE)),
        )
        for label, pattern in fatal_rules:
            if pattern.search(data, job_start):
                result["fatal_marker"] = label
                result["parser_acceptance_reasons"].append(f"fatal VASP marker detected: {label}")
                break
        if result["fatal_marker"] is None and _SCAN.has_fatal_marker(data, "vasp", start=job_start):
            result["fatal_marker"] = "FATAL_MARKER"
            result["parser_acceptance_reasons"].append("fatal VASP marker detected in final job")
        normal = _SCAN.contains(
            data,
            b"General timing and accounting informations for this job",
            start=job_start,
        )
        electronic = _SCAN.contains(data, b"EDIFF is reached", start=job_start) or _SCAN.contains(
            data,
            b"aborting loop because EDIFF is reached",
            start=job_start,
        )
        geometry = _SCAN.contains(
            data,
            b"reached required accuracy - stopping structural energy minimisation",
            start=job_start,
        )
        result["normal_termination"] = normal and result["fatal_marker"] is None
        result["electronic_converged"] = electronic
        result["geometry_converged"] = geometry
        energy, _ = _SCAN.last_group(data, VASP_ENERGY_RE, start=job_start)
        if energy is not None:
            result["energy"]["value"] = _float(energy)
        scf_markers = _SCAN.all_groups(data, VASP_SCF_ITERATION_RE, start=job_start)
        if scf_markers:
            result["scf_iterations"] = len(scf_markers)
        elapsed, _ = _SCAN.last_group(data, VASP_ELAPSED_RE, start=job_start)
        result["elapsed_time_s"] = _float(elapsed) if elapsed is not None else None
        result["forces"]["values"] = _parse_force_block(
            data,
            _SCAN.last_block(data, b"TOTAL-FORCE (eV/Angst)", b"total drift", start=job_start),
        )
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
        return _finalize(result, artifact)


def parse_qe(path: Path) -> dict[str, Any]:
    with _SCAN.mapped_artifact(path) as artifact:
        if artifact is None:
            return missing_result("quantum-espresso", path)
        data = artifact.data
        result = base_result("quantum-espresso", path)
        latest_version = None
        for match in QE_VERSION_RE.finditer(data):
            latest_version = match
        result["engine_version"] = _SCAN.decode(latest_version.group(1) if latest_version else None)
        job_start = latest_version.start() if latest_version else 0
        routine_error = bool(QE_ERROR_RE.search(data, job_start))
        nonconverged = _SCAN.contains(data, b"convergence NOT achieved", start=job_start)
        done = _SCAN.contains(data, b"JOB DONE.", start=job_start)
        result["fatal_marker"] = "ERROR_IN_ROUTINE" if routine_error else "SCF_NOT_CONVERGED" if nonconverged else None
        result["normal_termination"] = done and result["fatal_marker"] is None
        result["electronic_converged"] = (
            _SCAN.contains(
                data,
                b"convergence has been achieved",
                start=job_start,
            )
            and not nonconverged
        )
        result["geometry_converged"] = _SCAN.contains(
            data,
            b"End of BFGS Geometry Optimization",
            start=job_start,
        ) or bool(QE_BFGS_CONVERGED_RE.search(data, job_start))
        energy, _ = _SCAN.last_group(data, QE_ENERGY_RE, start=job_start)
        if energy is not None:
            result["energy"]["value"] = _float(energy, factor=RY_TO_EV)
        scf_markers = _SCAN.all_groups(data, QE_SCF_ITERATION_RE, start=job_start)
        if scf_markers:
            result["scf_iterations"] = len(scf_markers)
        forces, force_warning = _parse_qe_forces(data, job_start)
        result["forces"]["values"] = forces
        if force_warning:
            result["warnings"].append(force_warning)
        pressure, _ = _SCAN.last_group(data, QE_PRESSURE_RE, start=job_start)
        if pressure is not None:
            _float(pressure, factor=KBAR_TO_GPA)
            result["warnings"].append("QE P= is scalar pressure; it is not emitted as a stress tensor")
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
        return _finalize(result, artifact)


def parse_cp2k(path: Path) -> dict[str, Any]:
    with _SCAN.mapped_artifact(path) as artifact:
        if artifact is None:
            return missing_result("cp2k", path)
        data = artifact.data
        result = base_result("cp2k", path)
        starts = _SCAN.job_start_positions(data, "cp2k")
        job_start = starts[-1]
        result["job_index"] = len(starts)
        if len(starts) > 1:
            result["warnings"].append("multiple CP2K runs detected; only the final run determines acceptance")
        version = _SCAN.decode(_SCAN.first_group(data, CP2K_VERSION_RE, start=job_start))
        result["engine_version"] = version.strip() if version else None
        abort = bool(re.compile(rb"\bABORT\b").search(data, job_start))
        fatal = _SCAN.has_fatal_marker(data, "cp2k", start=job_start)
        nonconverged = _SCAN.contains(data, b"SCF run NOT converged", start=job_start)
        ended = _SCAN.contains(data, b"PROGRAM ENDED AT", start=job_start)
        result["fatal_marker"] = (
            "ABORT" if abort else "FATAL_MARKER" if fatal else "SCF_NOT_CONVERGED" if nonconverged else None
        )
        result["normal_termination"] = ended and result["fatal_marker"] is None
        result["electronic_converged"] = (
            _SCAN.contains(data, b"SCF run converged", start=job_start) and not nonconverged
        )
        result["geometry_converged"] = _SCAN.contains(
            data,
            b"GEOMETRY OPTIMIZATION COMPLETED",
            start=job_start,
        ) or _SCAN.contains(data, b"Reevaluating energy at the minimum", start=job_start)
        energy, _ = _SCAN.last_group(data, CP2K_ENERGY_RE, start=job_start)
        if energy is not None:
            result["energy"]["value"] = _float(energy, factor=HARTREE_TO_EV)
        # Inner SCF summaries report actual electronic steps. Do not count
        # energy evaluations or add an outer-SCF aggregate a second time.
        scf_steps = [match.group(1) for match in CP2K_SCF_STEPS_RE.finditer(data, job_start)]
        if scf_steps and all(value is not None for value in scf_steps):
            result["scf_iterations"] = sum(int(value) for value in scf_steps if value is not None)
        gradient, _ = _SCAN.last_group(data, CP2K_GRADIENT_RE, start=job_start)
        if gradient is not None:
            _float(gradient, factor=HARTREE_TO_EV / BOHR_TO_ANGSTROM)
            result["warnings"].append(
                "CP2K Max. gradient is a scalar convergence metric; per-atom force vectors are not parsed"
            )
        if result["fatal_marker"]:
            result["failed_stage"] = "engine" if fatal else "electronic"
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
        return _finalize(result, artifact)


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

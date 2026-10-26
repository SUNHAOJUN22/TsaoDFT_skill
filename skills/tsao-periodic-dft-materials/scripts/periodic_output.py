"""Bounded single-pass periodic-log parser with final-job numeric provenance.

Only the final job can qualify. A complete parser record is still not scientific
acceptance; these adapters never launch an external electronic-structure engine.
"""

from __future__ import annotations

import hashlib
import importlib.util
import math
import re
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import TypedDict

_SCRIPT_DIR = Path(__file__).resolve().parent
_SCAN_PATH = _SCRIPT_DIR / "_shared" / "engine_scan_core.py"
if not _SCAN_PATH.is_file():
    _SCAN_PATH = _SCRIPT_DIR.parents[1] / "tsao-dft-hpc-provenance/scripts/engine_scan_core.py"
_SCAN_SPEC = importlib.util.spec_from_file_location("tsao_periodic_engine_scan", _SCAN_PATH)
if _SCAN_SPEC is None or _SCAN_SPEC.loader is None:
    raise RuntimeError(f"cannot load {_SCAN_PATH}")
_SCAN = importlib.util.module_from_spec(_SCAN_SPEC)
sys.modules[_SCAN_SPEC.name] = _SCAN
_SCAN_SPEC.loader.exec_module(_SCAN)

MAX_LINE_BYTES = 1024 * 1024
MAX_ARTIFACT_BYTES = 1024 * 1024 * 1024
MAX_JOBS = 10000
FLOAT = r"([-+]?\S+)"


class EngineSpec(TypedDict):
    start: re.Pattern[str]
    version: re.Pattern[str]
    energy: re.Pattern[str]
    energy_key: str
    factor: float
    done_key: str
    done: tuple[str, ...]
    scf_key: str
    scf: tuple[str, ...]
    ionic_key: str
    ionic: tuple[str, ...]
    numbers: dict[str, re.Pattern[str]]


SPECS: dict[str, EngineSpec] = {
    "qe": {
        "start": re.compile(r"^\s*Program PWSCF"),
        "version": re.compile(r"Program PWSCF v\.([^\s]+)"),
        "energy": re.compile(r"!\s+total energy\s*=\s*" + FLOAT + r"\s+Ry"),
        "energy_key": "last_total_energy_Ry",
        "factor": 13.605693122994,
        "done_key": "job_done",
        "done": ("job done",),
        "scf_key": "scf_converged",
        "scf": ("convergence has been achieved",),
        "ionic_key": "ionic_converged",
        "ionic": ("end of bfgs geometry optimization", "bfgs converged in"),
        "numbers": {
            "fermi_energy_eV": re.compile(r"the Fermi energy is\s*" + FLOAT, re.I),
            "last_total_force_Ry_per_bohr": re.compile(r"Total force =\s*" + FLOAT),
            "last_pressure_kbar": re.compile(r"P=\s*" + FLOAT),
        },
    },
    "vasp": {
        "start": re.compile(r"^\s*vasp(?:\.|\s)", re.I),
        "version": re.compile(r"vasp\.([\d.]+)", re.I),
        "energy": re.compile(r"free\s+energy\s+TOTEN\s*=\s*" + FLOAT + r"\s+eV", re.I),
        "energy_key": "last_toten_eV",
        "factor": 1.0,
        "done_key": "normal_termination",
        "done": ("general timing and accounting informations",),
        "scf_key": "electronic_converged",
        "scf": ("ediff is reached",),
        "ionic_key": "ionic_converged",
        "ionic": ("reached required accuracy",),
        "numbers": {
            "fermi_energy_eV": re.compile(r"E-fermi\s*:\s*" + FLOAT, re.I),
            "elapsed_seconds": re.compile(r"Elapsed time \(sec\):\s*" + FLOAT),
            "nions": re.compile(r"NIONS\s*=\s*(\d+)"),
        },
    },
    "cp2k": {
        "start": re.compile(r"^\s*(?:PROGRAM STARTED AT|CP2K\|\s*version)"),
        "version": re.compile(r"CP2K\| version(?: string)?:\s*(.+)"),
        "energy": re.compile(r"ENERGY\| Total FORCE_EVAL.*?energy \(a\.u\.\):\s*" + FLOAT),
        "energy_key": "last_total_energy_hartree",
        "factor": 27.211386245988,
        "done_key": "program_ended",
        "done": ("program ended at",),
        "scf_key": "scf_converged",
        "scf": ("scf run converged",),
        "ionic_key": "geometry_converged",
        "ionic": ("geometry optimization completed", "reevaluating energy at the minimum"),
        "numbers": {"last_max_gradient": re.compile(r"Max\. gradient\s*=\s*" + FLOAT)},
    },
}
NONCONVERGED = (
    "convergence not achieved",
    "scf run not converged",
    "scf not converged",
    "maximum number of electronic steps reached",
)


def _fresh(spec, line, offset):
    return {
        "version": None,
        "energy_count": 0,
        spec["energy_key"]: None,
        "last_total_energy_eV": None,
        spec["done_key"]: False,
        spec["scf_key"]: False,
        spec["ionic_key"]: False,
        **dict.fromkeys(spec["numbers"]),
        "max_force_eV_per_angstrom": None,
        "warnings": [],
        "numeric_witnesses": {},
        "reason_codes": [],
        "start_line": line,
        "start_byte": offset,
        "fatal": False,
        "nonconverged": False,
    }


def _number(literal, field, job, line, offset, factor=1.0):
    job["numeric_witnesses"][field] = {"literal": literal, "line": line, "byte_offset": offset}
    try:
        token = literal.replace("D", "E").replace("d", "e")
        precise = Decimal(token)
        value = float(token)
        if not precise.is_finite() or not math.isfinite(value):
            raise ValueError("nonfinite")
        if precise != 0 and value == 0:
            raise ValueError("underflow")
        converted = value * factor
        if not math.isfinite(converted) or (converted == 0 and value != 0):
            raise ValueError("conversion range")
        return converted
    except (ValueError, OverflowError, InvalidOperation):
        job["reason_codes"].append(f"NUMERIC_RANGE_ERROR:{field}:line={line}")
        return None


def parse_output(engine: str, source: Path) -> dict:
    spec = SPECS[engine]
    path = source / "OUTCAR" if engine == "vasp" and source.is_dir() else source
    job = _fresh(spec, 1, 0)
    jobs = []
    digest = hashlib.sha256()
    offset = 0
    line_number = 0
    force_block = False
    job_start_seen = False
    header_state = _SCAN.JobBoundaryState()
    generic_header_pending = False
    stream_complete = True
    try:
        with path.open("rb") as handle:
            while True:
                raw = handle.readline(MAX_LINE_BYTES + 1)
                if not raw:
                    break
                line_number += 1
                if len(raw) > MAX_LINE_BYTES or offset + len(raw) > MAX_ARTIFACT_BYTES:
                    job["reason_codes"].append("PARSER_RESOURCE_LIMIT")
                    stream_complete = False
                    break
                digest.update(raw)
                text = raw.decode("utf-8", errors="strict")
                folded = text.casefold()
                generic_start = text.strip() == "--- JOB START ---"
                if generic_start:
                    start = True
                    generic_header_pending = True
                    header_state = _SCAN.JobBoundaryState()
                elif engine in {"vasp", "cp2k"}:
                    kind = _SCAN.job_header_kind(text, engine)
                    start = kind is not None and header_state.advance(kind)
                    if kind is not None and generic_header_pending:
                        start = False
                        generic_header_pending = False
                else:
                    start = bool(spec["start"].search(text))
                    if start and generic_header_pending:
                        start = False
                        generic_header_pending = False
                if start and job_start_seen:
                    jobs.append(job)
                    if len(jobs) >= MAX_JOBS:
                        raise ValueError("job count exceeds parser budget")
                    job = _fresh(spec, line_number, offset)
                    job_start_seen = True
                    force_block = False
                elif start and not job_start_seen:
                    # The initial _fresh record is only a placeholder when
                    # preamble text precedes the first actual job marker.
                    job["start_line"] = line_number
                    job["start_byte"] = offset
                    job_start_seen = True
                if match := spec["version"].search(text):
                    job["version"] = match.group(1).strip()
                job["fatal"] |= _SCAN.has_fatal_marker(text, engine)
                job["nonconverged"] |= any(marker in folded for marker in NONCONVERGED)
                for key, markers in (
                    (spec["done_key"], spec["done"]),
                    (spec["scf_key"], spec["scf"]),
                    (spec["ionic_key"], spec["ionic"]),
                ):
                    if any(marker in folded for marker in markers):
                        job[key] = True
                if match := spec["energy"].search(text):
                    job["energy_count"] += 1
                    literal = match.group(1)
                    job[spec["energy_key"]] = _number(literal, spec["energy_key"], job, line_number, offset)
                    job["last_total_energy_eV"] = _number(
                        literal, "last_total_energy_eV", job, line_number, offset, spec["factor"]
                    )
                for field, pattern in spec["numbers"].items():
                    if match := pattern.search(text):
                        job[field] = _number(match.group(1), field, job, line_number, offset)
                        if field == "nions" and job[field] is not None:
                            job[field] = int(job[field])
                if engine == "vasp":
                    if "TOTAL-FORCE (eV/Angst)" in text:
                        force_block = True
                        job["max_force_eV_per_angstrom"] = None
                    elif "total drift" in folded:
                        force_block = False
                    elif force_block:
                        fields = text.split()
                        if len(fields) == 6:
                            force = [
                                _number(token, "force_component", job, line_number, offset) for token in fields[-3:]
                            ]
                            if all(value is not None for value in force):
                                norm = math.hypot(*force)
                                if math.isfinite(norm):
                                    job["max_force_eV_per_angstrom"] = max(
                                        job["max_force_eV_per_angstrom"] or 0.0, norm
                                    )
                                else:
                                    job["reason_codes"].append(f"NUMERIC_RANGE_ERROR:force_norm:line={line_number}")
                offset += len(raw)
    except (OSError, UnicodeError, ValueError) as exc:
        job["reason_codes"].append(f"SOURCE_READ_ERROR:{exc}")
        stream_complete = False
    jobs.append(job)
    reasons = list(job["reason_codes"])
    if job["fatal"]:
        reasons.append("FATAL_MARKER_PRESENT")
    if job["nonconverged"]:
        reasons.append("NONCONVERGENCE_MARKER_PRESENT")
    if not job[spec["done_key"]]:
        reasons.append("NORMAL_TERMINATION_MISSING")
    if not job[spec["scf_key"]]:
        reasons.append("SCF_CONVERGENCE_MISSING")
    if job[spec["energy_key"]] is None:
        reasons.append("FINAL_JOB_ENERGY_MISSING")
    accepted = not reasons and stream_complete
    status = (
        ("RELAX_VALIDATED_CANDIDATE" if job[spec["ionic_key"]] else "STATIC_VALIDATED_CANDIDATE")
        if accepted
        else "INVALID_OUTPUT"
    )
    if job["fatal"]:
        status = "FATAL"
    elif job["nonconverged"]:
        status = "NONCONVERGED"
    elif not job[spec["done_key"]]:
        status = "INCOMPLETE"
    result = dict(job)
    result.update(
        status=status,
        parser_accepted=accepted,
        parser_contract_status="CONVERGED" if accepted else status,
        parser_reason_codes=reasons,
        parser_segment_count=len(jobs),
        jobs=jobs,
        source_sha256=digest.hexdigest(),
        source_bytes=offset,
        source_complete=stream_complete,
        source_lines=line_number,
        scientific_acceptance="PENDING",
    )
    if not accepted:
        result[spec["done_key"]] = False
    return result

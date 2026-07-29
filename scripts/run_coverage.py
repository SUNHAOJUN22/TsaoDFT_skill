#!/usr/bin/env python3
"""Run deterministic statement/branch coverage with explicit trust-core thresholds."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from coverage import Coverage

ROOT = Path(__file__).resolve().parents[1]
TRUST_CORE = (
    "skills/tsao-dft-hpc-provenance/scripts/shell_contract.py",
    "skills/tsao-dft-hpc-provenance/scripts/trust_boundary.py",
    "skills/tsao-dft-hpc-provenance/scripts/engine_parser_contract.py",
    "skills/tsao-dft-hpc-provenance/scripts/benchmark_bridge.py",
    "skills/tsao-dft-hpc-provenance/scripts/generate_job_script.py",
    "skills/tsao-dft-hpc-provenance/scripts/validate_hpc_manifest.py",
)


def percent(numerator: int, denominator: int) -> float:
    return 100.0 if denominator == 0 else 100.0 * numerator / denominator


def test_suites() -> list[Path]:
    candidates = [ROOT / "tests", *sorted((ROOT / "skills").glob("*/tests"))]
    return [path for path in candidates if path.is_dir()]


def collect_coverage(data_file: Path) -> list[str]:
    errors: list[str] = []
    for index, suite in enumerate(test_suites()):
        command = [
            sys.executable,
            "-m",
            "coverage",
            "run",
            f"--data-file={data_file}",
            "--branch",
            "--source=scripts,skills",
        ]
        if index:
            command.append("--append")
        command.extend(
            [
                "-m",
                "unittest",
                "discover",
                "-s",
                str(suite),
                "-p",
                "test_*.py",
                "-v",
            ]
        )
        completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
        if completed.returncode:
            output = ((completed.stdout or "") + (completed.stderr or "")).rstrip()
            errors.append(f"coverage suite failed: {suite.relative_to(ROOT)}\n{output}")
            break
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", dest="json_output")
    parser.add_argument("--total-statement", type=float, default=90.0)
    parser.add_argument("--total-branch", type=float, default=80.0)
    parser.add_argument("--core-statement", type=float, default=100.0)
    parser.add_argument("--core-branch", type=float, default=95.0)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as temporary:
        data_file = Path(temporary) / ".coverage"
        collection_errors = collect_coverage(data_file)
        if collection_errors:
            payload = {"ok": False, "errors": collection_errors}
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 1
        coverage = Coverage(data_file=str(data_file), branch=True)
        coverage.load()
        measured = sorted(coverage.get_data().measured_files())
        total_statements = total_missing = total_branches = total_missing_branches = 0
        per_file: dict[str, dict[str, float]] = {}
        for filename in measured:
            path = Path(filename)
            try:
                relative = path.resolve().relative_to(ROOT.resolve()).as_posix()
            except ValueError:
                continue
            analysis = coverage._analyze(filename)
            statements = len(analysis.statements)
            missing = len(analysis.missing)
            branches = analysis.numbers.n_branches
            missing_branches = analysis.numbers.n_missing_branches
            total_statements += statements
            total_missing += missing
            total_branches += branches
            total_missing_branches += missing_branches
            per_file[relative] = {
                "statement": percent(statements - missing, statements),
                "branch": percent(branches - missing_branches, branches),
            }
        total_statement = percent(total_statements - total_missing, total_statements)
        total_branch = percent(total_branches - total_missing_branches, total_branches)
        failures = []
        if total_statement < args.total_statement:
            failures.append(f"total statement coverage {total_statement:.2f} < {args.total_statement:.2f}")
        if total_branch < args.total_branch:
            failures.append(f"total branch coverage {total_branch:.2f} < {args.total_branch:.2f}")
        for relative in TRUST_CORE:
            values = per_file.get(relative)
            if values is None:
                failures.append(f"trust core was not measured: {relative}")
                continue
            if values["statement"] < args.core_statement:
                failures.append(f"{relative} statement coverage {values['statement']:.2f} < {args.core_statement:.2f}")
            if values["branch"] < args.core_branch:
                failures.append(f"{relative} branch coverage {values['branch']:.2f} < {args.core_branch:.2f}")
        payload = {
            "ok": not failures,
            "total": {"statement": round(total_statement, 2), "branch": round(total_branch, 2)},
            "thresholds": {
                "total_statement": args.total_statement,
                "total_branch": args.total_branch,
                "core_statement": args.core_statement,
                "core_branch": args.core_branch,
            },
            "trust_core": {path: per_file.get(path) for path in TRUST_CORE},
            "per_file": per_file,
            "failures": failures,
        }
        if args.json_output:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(f"Coverage statement={total_statement:.2f}% branch={total_branch:.2f}%")
            for relative in TRUST_CORE:
                values = per_file.get(relative)
                print(f"CORE {relative}: {values}")
            for failure in failures:
                print(f"FAIL: {failure}")
        return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Run deterministic statement/branch coverage with explicit trust-core thresholds."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

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


def write_coverage_config(path: Path, data_file: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "[run]",
                "branch = true",
                "parallel = true",
                "patch =",
                "    subprocess",
                "source =",
                f"    {ROOT / 'scripts'}",
                f"    {ROOT / 'skills'}",
                f"data_file = {data_file}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def collect_coverage(config_file: Path) -> list[str]:
    errors: list[str] = []
    for suite in test_suites():
        command = [
            sys.executable,
            "-m",
            "coverage",
            "run",
            f"--rcfile={config_file}",
            "--parallel-mode",
            "-m",
            "unittest",
            "discover",
            "-s",
            str(suite),
            "-p",
            "test_*.py",
            "-v",
        ]
        completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
        if completed.returncode:
            output = ((completed.stdout or "") + (completed.stderr or "")).rstrip()
            errors.append(f"coverage suite failed: {suite.relative_to(ROOT)}\n{output}")
            break
    return errors


def write_report(path: Path | None, payload: dict[str, Any]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", dest="json_output")
    parser.add_argument("--report", type=Path, default=Path("coverage-report.json"))
    parser.add_argument("--total-statement", type=float, default=90.0)
    parser.add_argument("--total-branch", type=float, default=80.0)
    parser.add_argument("--core-statement", type=float, default=100.0)
    parser.add_argument("--core-branch", type=float, default=95.0)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as temporary:
        temporary_path = Path(temporary)
        data_file = temporary_path / ".coverage"
        config_file = temporary_path / "coveragerc"
        write_coverage_config(config_file, data_file)
        collection_errors = collect_coverage(config_file)
        if collection_errors:
            payload: dict[str, Any] = {"ok": False, "errors": collection_errors}
            write_report(args.report, payload)
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 1
        coverage = Coverage(config_file=str(config_file), data_file=str(data_file))
        try:
            coverage.combine(data_paths=[str(temporary_path)], strict=True)
        except Exception as exc:
            payload = {"ok": False, "errors": [f"coverage combine failed: {exc}"]}
            write_report(args.report, payload)
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 1
        coverage.save()
        coverage.load()
        measured = sorted(coverage.get_data().measured_files())
        total_statements = total_missing = total_branches = total_missing_branches = 0
        per_file: dict[str, dict[str, Any]] = {}
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
                "statement": round(percent(statements - missing, statements), 2),
                "branch": round(percent(branches - missing_branches, branches), 2),
                "statements": statements,
                "missing_statements": missing,
                "branches": branches,
                "missing_branches": missing_branches,
                "missing_lines": sorted(analysis.missing),
                "missing_branch_arcs": {
                    str(line): sorted(destinations)
                    for line, destinations in sorted(analysis.missing_branch_arcs().items())
                },
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
        write_report(args.report, payload)
        if args.json_output:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(f"Coverage statement={total_statement:.2f}% branch={total_branch:.2f}%")
            for relative in TRUST_CORE:
                print(f"CORE {relative}: {json.dumps(per_file.get(relative), ensure_ascii=False)}")
            low_files = sorted(
                (
                    (relative, values)
                    for relative, values in per_file.items()
                    if values["statement"] < args.total_statement or values["branch"] < args.total_branch
                ),
                key=lambda item: (item[1]["statement"], item[1]["branch"], item[0]),
            )
            for relative, values in low_files:
                print(f"GAP {relative}: {json.dumps(values, ensure_ascii=False)}")
            for failure in failures:
                print(f"FAIL: {failure}")
        return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Run root and per-skill unittest suites with isolated discovery."""
from __future__ import annotations

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def run_suite(directory: Path) -> int:
    print(f"\n=== unittest: {directory.relative_to(ROOT)} ===", flush=True)
    return subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", str(directory), "-p", "test_*.py", "-v"],
        cwd=ROOT,
    ).returncode


def main() -> int:
    suites = [ROOT / "tests"] + sorted((ROOT / "skills").glob("*/tests"))
    failures = sum(run_suite(path) != 0 for path in suites if path.exists())
    print(f"\nSuites: {len(suites)}  Failed suites: {failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

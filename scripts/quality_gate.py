#!/usr/bin/env python3
"""Run the complete TsaoDFT quality gate in a deterministic fail-fast sequence."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Stage:
    name: str
    command: tuple[str, ...]


def stages(include_tests: bool = True) -> list[Stage]:
    items = [
        Stage("demo assets", (sys.executable, "scripts/generate_readme_demos.py")),
        Stage("catalog", (sys.executable, "scripts/validate_catalog.py")),
        Stage("AI assets", (sys.executable, "scripts/validate_ai_assets.py")),
        Stage("README visuals", (sys.executable, "scripts/validate_readme_visuals.py", "--strict")),
        Stage("Ruff lint", (sys.executable, "-m", "ruff", "check", ".")),
        Stage("Ruff format", (sys.executable, "-m", "ruff", "format", "--check", ".")),
        Stage("repository", (sys.executable, "scripts/validate_repo.py", "--strict")),
    ]
    if include_tests:
        items.append(Stage("unit tests", (sys.executable, "scripts/run_all_tests.py")))
    return items


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-tests", action="store_true", help="Run static gates only")
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args()

    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    results: list[dict[str, object]] = []
    started = time.monotonic()

    for index, stage in enumerate(stages(include_tests=not args.skip_tests), start=1):
        stage_started = time.monotonic()
        process = subprocess.run(stage.command, cwd=ROOT, text=True, env=env)
        elapsed = round(time.monotonic() - stage_started, 3)
        results.append({"stage": stage.name, "returncode": process.returncode, "seconds": elapsed})
        if not args.json_output:
            print(f"[{index}] {stage.name}: {'PASS' if process.returncode == 0 else 'FAIL'} ({elapsed:.3f}s)")
        if process.returncode != 0:
            break

    expected = stages(include_tests=not args.skip_tests)
    ok = len(results) == len(expected) and all(item["returncode"] == 0 for item in results)
    payload = {
        "ok": ok,
        "python": sys.version.split()[0],
        "seconds": round(time.monotonic() - started, 3),
        "stages": results,
    }
    if args.json_output:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"QUALITY GATE: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

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
    timeout_seconds: float = 240.0


def stages(include_tests: bool = True) -> list[Stage]:
    items = [
        Stage("demo assets", (sys.executable, "scripts/generate_readme_demos.py")),
        Stage("dependency contract", (sys.executable, "scripts/validate_dependencies.py")),
        Stage("packaging model", (sys.executable, "scripts/validate_packaging_model.py")),
        Stage("catalog", (sys.executable, "scripts/validate_catalog.py")),
        Stage("Agent eval contracts", (sys.executable, "scripts/validate_agent_evals.py")),
        Stage("AI assets", (sys.executable, "scripts/validate_ai_assets.py")),
        Stage("README visuals", (sys.executable, "scripts/validate_readme_visuals.py", "--strict")),
        Stage("README links", (sys.executable, "scripts/validate_readme_links.py")),
        Stage("Ruff lint", (sys.executable, "-m", "ruff", "check", ".")),
        Stage("Ruff format", (sys.executable, "-m", "ruff", "format", "--check", ".")),
        Stage("mypy", (sys.executable, "scripts/run_type_checks.py"), timeout_seconds=900.0),
        Stage("Bandit", (sys.executable, "scripts/run_bandit.py"), timeout_seconds=600.0),
        Stage("repository", (sys.executable, "scripts/validate_repo.py", "--strict")),
    ]
    if include_tests:
        items.append(Stage("unit tests", (sys.executable, "scripts/run_all_tests.py"), timeout_seconds=900.0))
    return items


def run_stage(
    stage: Stage,
    env: dict[str, str],
    *,
    timeout_override: float | None = None,
    capture_output: bool = False,
) -> dict[str, object]:
    started = time.monotonic()
    timeout = timeout_override if timeout_override is not None else stage.timeout_seconds
    try:
        process = subprocess.run(
            stage.command,
            cwd=ROOT,
            text=True,
            env=env,
            timeout=timeout,
            capture_output=capture_output,
            check=False,
        )
        result: dict[str, object] = {
            "stage": stage.name,
            "returncode": process.returncode,
            "seconds": round(time.monotonic() - started, 3),
            "timed_out": False,
        }
        if capture_output and process.returncode != 0:
            result["output"] = ((process.stdout or "") + (process.stderr or "")).rstrip()
        return result
    except subprocess.TimeoutExpired as exc:
        result = {
            "stage": stage.name,
            "returncode": 124,
            "seconds": round(time.monotonic() - started, 3),
            "timed_out": True,
            "timeout_seconds": timeout,
        }
        if capture_output:
            stdout = exc.stdout if isinstance(exc.stdout, str) else ""
            stderr = exc.stderr if isinstance(exc.stderr, str) else ""
            result["output"] = (stdout + stderr).rstrip()
        return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-tests", action="store_true", help="Run static gates only")
    parser.add_argument("--json", action="store_true", dest="json_output")
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="Override the timeout for every stage in seconds; must be positive",
    )
    args = parser.parse_args()
    if args.timeout is not None and args.timeout <= 0:
        parser.error("--timeout must be positive")

    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    results: list[dict[str, object]] = []
    started = time.monotonic()
    expected = stages(include_tests=not args.skip_tests)

    for index, stage in enumerate(expected, start=1):
        result = run_stage(stage, env, timeout_override=args.timeout, capture_output=args.json_output)
        results.append(result)
        if not args.json_output:
            status = "PASS" if result["returncode"] == 0 else "TIMEOUT" if result["timed_out"] else "FAIL"
            print(f"[{index}] {stage.name}: {status} ({result['seconds']:.3f}s)")
        if result["returncode"] != 0:
            break

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

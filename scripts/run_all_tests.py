#!/usr/bin/env python3
"""Run root and per-Skill unittest suites deterministically and report a stable summary."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def run_suite(path: Path, timeout: int = 240) -> dict[str, Any]:
    command = [sys.executable, "-m", "unittest", "discover", "-s", str(path), "-p", "test_*.py", "-v"]
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        process = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
        output = (process.stdout or "") + (process.stderr or "")
        match = re.search(r"Ran\s+(\d+)\s+tests?", output)
        return {
            "path": path,
            "returncode": process.returncode,
            "count": int(match.group(1)) if match else 0,
            "output": output,
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        return {"path": path, "returncode": 124, "count": 0, "output": stdout + stderr, "timed_out": True}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", dest="json_output")
    parser.add_argument("--timeout", type=int, default=240, help="Per-suite timeout in seconds")
    args = parser.parse_args()

    candidates = [ROOT / "tests"] + sorted((ROOT / "skills").glob("*/tests"))
    suites = [path for path in candidates if path.is_dir()]
    if not suites:
        print("FAIL: no unittest suites found")
        return 1

    # Sequential execution is intentional. Some suites exercise repository-wide files;
    # parallel discovery made failures intermittent and obscured the first root cause.
    results = [run_suite(path, timeout=args.timeout) for path in suites]
    failed = [result for result in results if result["returncode"] != 0]
    total = sum(result["count"] for result in results)

    if args.json_output:
        payload = {
            "ok": not failed,
            "suites": len(results),
            "tests": total,
            "failed_suites": [str(result["path"].relative_to(ROOT)) for result in failed],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for result in results:
            print(f"\n=== unittest: {result['path'].relative_to(ROOT)} ===")
            print(result["output"].rstrip())
            if result["timed_out"]:
                print("FAIL: suite timed out")
        print(f"\nSuites: {len(results)}  Tests: {total}  Failed suites: {len(failed)}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

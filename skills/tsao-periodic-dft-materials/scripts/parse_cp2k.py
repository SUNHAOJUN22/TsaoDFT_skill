#!/usr/bin/env python3
"""Parse CP2K output using bounded, final-job-bound scientific records."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

_MODULE = Path(__file__).with_name("periodic_output.py")
_SPEC = importlib.util.spec_from_file_location("tsao_periodic_output", _MODULE)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"cannot load {_MODULE}")
_CORE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_CORE)


def parse(path: Path) -> dict:
    return _CORE.parse_output("cp2k", path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = parse(args.output)
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0 if result["parser_accepted"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPLACEMENTS = {
    "skills/tsao-dft-hpc-provenance/scripts/generate_job_array.py": [
        (
            "from validate_hpc_manifest import (\n",
            "from validate_hpc_manifest import (  # noqa: E402 -- local validator import follows SCRIPT_DIR path setup\n",
        )
    ],
    "skills/tsao-dft-hpc-provenance/scripts/generate_job_script.py": [
        (
            "from validate_hpc_manifest import (\n",
            "from validate_hpc_manifest import (  # noqa: E402 -- local validator import follows SCRIPT_DIR path setup\n",
        )
    ],
    "skills/tsao-dft-researcher/scripts/preflight_project.py": [
        (
            "from validate_figure_manifest import (\n",
            "from validate_figure_manifest import (  # noqa: E402 -- local validator import follows SCRIPT_DIR path setup\n",
        ),
        (
            "from validate_research_manifest import (\n",
            "from validate_research_manifest import (  # noqa: E402 -- local validator import follows SCRIPT_DIR path setup\n",
        ),
    ],
    "skills/tsao-dft-researcher/tests/test_figure_manifest.py": [
        (
            "from validate_figure_manifest import (\n",
            "from validate_figure_manifest import (  # noqa: E402 -- test import follows explicit scripts path setup\n",
        )
    ],
    "skills/tsao-dft-researcher/tests/test_research_manifest.py": [
        (
            "from validate_research_manifest import (\n",
            "from validate_research_manifest import (  # noqa: E402 -- test import follows explicit scripts path setup\n",
        )
    ],
}

for relative, replacements in REPLACEMENTS.items():
    path = ROOT / relative
    text = path.read_text(encoding="utf-8")
    for old, new in replacements:
        count = text.count(old)
        if count != 1:
            raise RuntimeError(f"{relative}: expected one match for {old!r}, found {count}")
        text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")

print("Annotated six intentional dynamic imports.")

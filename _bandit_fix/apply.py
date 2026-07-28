#!/usr/bin/env python3
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(relative: str, old: str, new: str) -> None:
    path = ROOT / relative
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{relative}: expected one occurrence, found {count}: {old!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


replace_once(
    "scripts/install.py",
    """        else:
            assert staged is not None
            os.replace(staged, destination)
""",
    """        else:
            if staged is None:
                raise InstallSafetyError("internal error: copy installation was not staged")
            os.replace(staged, destination)
""",
)

replace_once(
    "scripts/validate_governance.py",
    '            data = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)\n',
    '            data = yaml.safe_load(path.read_text(encoding="utf-8"))\n',
)
replace_once(
    "scripts/validate_governance.py",
    '        triggers = data.get("on", {})\n',
    '        triggers = data.get("on", data.get(True, {}))\n',
)

allowlist = ROOT / "config" / "bandit_allowlist.yaml"
text = allowlist.read_text(encoding="utf-8").rstrip() + "\n"
entries = """  - path: scripts/run_bandit.py
    test_id: B404
    reason: the wrapper imports subprocess only to invoke the pinned Bandit module with a fixed repository-owned argv list.
  - path: scripts/run_bandit.py
    test_id: B603
    reason: Bandit receives fixed paths and flags through an argv list; shell execution and user command text are not used.
  - path: scripts/run_type_checks.py
    test_id: B404
    reason: the wrapper imports subprocess only to invoke the pinned mypy module for discovered repository directories.
  - path: scripts/run_type_checks.py
    test_id: B603
    reason: mypy receives sys.executable, fixed flags and repository-owned directory paths through an argv list with shell disabled.
"""
for marker in (
    "path: scripts/run_bandit.py\n    test_id: B404",
    "path: scripts/run_bandit.py\n    test_id: B603",
    "path: scripts/run_type_checks.py\n    test_id: B404",
    "path: scripts/run_type_checks.py\n    test_id: B603",
):
    if marker in text:
        raise RuntimeError(f"Bandit allowance already present: {marker}")
allowlist.write_text(text + entries, encoding="utf-8")

workflow = ROOT / ".github" / "workflows" / "bandit-fix.yml"
if workflow.exists():
    workflow.unlink()
shutil.rmtree(ROOT / "_bandit_fix")
print("Applied Bandit closure and removed one-time files.")

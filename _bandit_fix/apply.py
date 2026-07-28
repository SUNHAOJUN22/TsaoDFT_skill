#!/usr/bin/env python3
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BEGIN_MARKER = "  # BEGIN ONE-TIME BANDIT CLOSURE"
END_MARKER = "  # END ONE-TIME BANDIT CLOSURE"


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

ci_path = ROOT / ".github" / "workflows" / "ci.yml"
ci_text = ci_path.read_text(encoding="utf-8")
if ci_text.count(BEGIN_MARKER) != 1 or ci_text.count(END_MARKER) != 1:
    raise RuntimeError("one-time Bandit closure markers are missing or duplicated")
start = ci_text.index(BEGIN_MARKER)
end = ci_text.index(END_MARKER, start) + len(END_MARKER)
restored = ci_text[:start].rstrip() + "\n" + ci_text[end:].lstrip("\n")
ci_path.write_text(restored, encoding="utf-8")

legacy_workflow = ROOT / ".github" / "workflows" / "bandit-fix.yml"
if legacy_workflow.exists():
    legacy_workflow.unlink()
shutil.rmtree(ROOT / "_bandit_fix")
print("Applied Bandit closure and restored the permanent repository layout.")

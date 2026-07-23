#!/usr/bin/env python3
"""Generate a stable SHA-256 manifest for repository release files."""
from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "SHA256SUMS"
EXCLUDE = {".git", "__pycache__"}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    paths = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path == OUTPUT or any(part in EXCLUDE for part in path.parts) or path.suffix == ".pyc":
            continue
        paths.append(path)
    lines = [f"{digest(path)}  {path.relative_to(ROOT).as_posix()}" for path in sorted(paths)]
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT} with {len(lines)} entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

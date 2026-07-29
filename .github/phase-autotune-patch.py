#!/usr/bin/env python3
"""Apply one reviewed, compressed TsaoComputation payload to repository paths."""
from __future__ import annotations

import base64
import json
import lzma
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD_GLOB = "phase-autotune-payload.*"
ALLOWED_PREFIXES = (
    "config/bandit_allowlist.yaml",
    "skills/tsao-dft-hpc-provenance/scripts/",
    "skills/tsao-dft-hpc-provenance/templates/",
    "skills/tsao-dft-hpc-provenance/tests/",
)


def allowed(path: str) -> bool:
    return any(path == prefix or path.startswith(prefix) for prefix in ALLOWED_PREFIXES)


def main() -> int:
    parts = sorted((ROOT / ".github").glob(PAYLOAD_GLOB))
    if not parts:
        raise RuntimeError("autotuning payload is missing")
    encoded = "".join(part.read_text(encoding="utf-8").strip() for part in parts)
    decoded = lzma.decompress(base64.b64decode(encoded))
    entries: Any = json.loads(decoded)
    if not isinstance(entries, list) or not entries:
        raise RuntimeError("autotuning payload must be a non-empty list")
    written: list[str] = []
    for raw in entries:
        if not isinstance(raw, dict):
            raise RuntimeError("payload entry must be a mapping")
        path = str(raw.get("path", ""))
        content = raw.get("content")
        if not path or not allowed(path) or Path(path).is_absolute() or ".." in Path(path).parts:
            raise RuntimeError(f"payload path is not allowed: {path!r}")
        if not isinstance(content, str):
            raise RuntimeError(f"payload content must be text: {path}")
        target = ROOT / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        written.append(path)
    print(json.dumps({"ok": True, "written": written}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

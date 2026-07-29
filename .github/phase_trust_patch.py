#!/usr/bin/env python3
from __future__ import annotations

import base64
import lzma
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
parts = sorted((ROOT / ".github").glob("phase_trust_payload.*"))
if not parts:
    raise SystemExit("phase trust payload is missing")
encoded = "".join(path.read_text(encoding="ascii") for path in parts)
source = lzma.decompress(base64.b64decode(encoded)).decode("utf-8")
exec(
    compile(source, "phase_trust_patch_payload.py", "exec"),
    {"__name__": "__main__", "__file__": str(ROOT / ".github" / "phase_trust_patch.py")},
)

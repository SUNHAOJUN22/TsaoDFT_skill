#!/usr/bin/env python3
"""Materialize or validate deterministic synthetic README SVG demonstrations.

Published demo SVGs are versioned assets. Existing assets are preserved byte-for-byte;
missing assets are recreated as compact labeled placeholders so CI and offline installs
never substitute generated artwork for scientific evidence.
"""
from __future__ import annotations

from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "demo"
NOTICE = "SYNTHETIC DEMO · NOT SCIENTIFIC DATA"
DEMOS = {
    "workflow-architecture": "TsaoDFT auditable research loop",
    "wavefunction-esp-gallery": "Wavefunction and surface figure contract",
    "free-energy-profile": "Free-energy profile with explicit validation gates",
    "dft-ml-dashboard": "DFT + ML provenance-aware evaluation",
    "periodic-dft-materials": "Periodic DFT and materials evidence chain",
    "active-learning-loop": "DFT + ML active-learning loop",
    "hpc-provenance": "HPC execution and provenance",
    "multiscale-kinetics": "DFT to kinetics and multiscale models",
}


def placeholder(title: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="420" viewBox="0 0 1120 420" role="img">
<rect width="1120" height="420" rx="18" fill="#f8fafc"/>
<text x="36" y="48" font-family="Arial,sans-serif" font-size="24" font-weight="700" fill="#0f172a">{escape(title)}</text>
<rect x="80" y="110" width="960" height="210" rx="22" fill="#ffffff" stroke="#cbd5e1"/>
<text x="560" y="205" text-anchor="middle" font-family="Arial,sans-serif" font-size="18" font-weight="700" fill="#334155">TsaoDFT deterministic README demonstration</text>
<text x="560" y="242" text-anchor="middle" font-family="Arial,sans-serif" font-size="13" fill="#64748b">Re-run the repository renderer to replace this compact offline placeholder.</text>
<text x="1090" y="398" text-anchor="end" font-family="Arial,sans-serif" font-size="10" font-weight="700" fill="#9f1239">{NOTICE}</text>
</svg>'''


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for stem, title in DEMOS.items():
        path = OUT / f"{stem}.svg"
        if not path.exists():
            path.write_text(placeholder(title), encoding="utf-8", newline="\n")
        text = path.read_text(encoding="utf-8")
        if NOTICE not in text:
            raise SystemExit(f"Demo lacks synthetic-data notice: {path}")
    print(f"Validated {len(DEMOS)} deterministic README SVG demos in {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

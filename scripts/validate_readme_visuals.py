#!/usr/bin/env python3
"""Validate README image references and the AI/deterministic visual boundary."""
from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
AI_MANIFEST = ROOT / "assets/ai/manifest.yaml"

MD_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)(?:\s+[^)]*)?\)")
HTML_IMAGE_RE = re.compile(r"<img\s+[^>]*src=[\"']([^\"']+)[\"'][^>]*>", re.IGNORECASE)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate() -> tuple[list[str], list[str]]:
    failures: list[str] = []
    warnings: list[str] = []
    readme = README.read_text(encoding="utf-8")
    refs = set(MD_IMAGE_RE.findall(readme)) | set(HTML_IMAGE_RE.findall(readme))
    local_refs = {ref for ref in refs if not ref.startswith(("http://", "https://"))}

    for ref in sorted(local_refs):
        if not (ROOT / ref).is_file():
            failures.append(f"README references missing image: {ref}")

    manifest = yaml.safe_load(AI_MANIFEST.read_text(encoding="utf-8"))
    assets = manifest.get("assets", []) if isinstance(manifest, dict) else []
    if len(assets) < 8:
        failures.append("AI manifest must contain at least eight governed assets")

    for item in assets:
        path_value = item.get("path")
        if not path_value:
            failures.append("AI manifest entry has no path")
            continue
        path = ROOT / str(path_value)
        if str(path_value) not in local_refs:
            failures.append(f"governed AI asset is not embedded in README: {path_value}")
        if not path.is_file():
            failures.append(f"AI asset missing: {path_value}")
            continue
        if item.get("sha256") != digest(path):
            failures.append(f"AI asset hash mismatch: {path_value}")
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "NOT COMPUTATIONAL DATA" not in text and "NOT SCIENTIFIC DATA" not in text:
            failures.append(f"AI asset lacks visible non-data label: {path_value}")
        for key, expected in {
            "illustrative_only": True,
            "quantitative": False,
            "computed_surface": False,
        }.items():
            if item.get(key) is not expected:
                failures.append(f"AI asset {path_value} has invalid {key}")

    required_demos = {
        "assets/demo/workflow-architecture.svg",
        "assets/demo/wavefunction-esp-gallery.svg",
        "assets/demo/periodic-dft-materials.svg",
        "assets/demo/active-learning-loop.svg",
        "assets/demo/hpc-provenance.svg",
        "assets/demo/multiscale-kinetics.svg",
    }
    missing_demo_refs = required_demos - local_refs
    for ref in sorted(missing_demo_refs):
        failures.append(f"deterministic README demo is not embedded: {ref}")

    first_ai = min(
        (readme.find(ref) for ref in local_refs if ref.startswith("assets/ai/") and readme.find(ref) >= 0),
        default=-1,
    )
    declaration = readme.find("AI图像声明")
    if first_ai >= 0 and (declaration < 0 or declaration > first_ai + 600):
        warnings.append("AI declaration should appear immediately beside the first AI image")

    forbidden_phrases = [
        "AI生成的真实计算结果",
        "AI-generated computational result",
        "AI calculated orbital",
    ]
    for phrase in forbidden_phrases:
        if phrase.lower() in readme.lower():
            failures.append(f"README contains forbidden AI-result wording: {phrase}")

    return failures, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    failures, warnings = validate()
    for warning in warnings:
        print(f"WARN: {warning}")
    for failure in failures:
        print(f"FAIL: {failure}")
    if args.strict and warnings:
        failures.extend(f"strict warning: {warning}" for warning in warnings)
    print(f"README visual validation: {'PASS' if not failures else 'FAIL'}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())

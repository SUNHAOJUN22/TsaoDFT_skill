#!/usr/bin/env python3
"""Validate provenance and non-quantitative policy for README AI images."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import re
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "assets/ai/manifest.yaml"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def svg_size(path: Path) -> tuple[int, int]:
    head = path.read_text(encoding="utf-8")[:600]
    width = re.search(r'\bwidth="(\d+)"', head)
    height = re.search(r'\bheight="(\d+)"', head)
    if not width or not height:
        raise ValueError("SVG width/height missing")
    text = path.read_text(encoding="utf-8")
    if "AI-generated conceptual illustration" not in text and "AI-assisted conceptual illustration" not in text:
        raise ValueError("SVG lacks AI conceptual aria label")
    return int(width.group(1)), int(height.group(1))


def validate(manifest_path: Path = MANIFEST) -> list[str]:
    failures: list[str] = []
    try:
        data: Any = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"manifest parse failed: {exc}"]
    if not isinstance(data, dict):
        return ["manifest root must be a mapping"]
    assets = data.get("assets")
    if not isinstance(assets, list) or not assets:
        return ["manifest assets must be a non-empty list"]
    paths: set[str] = set()
    for index, item in enumerate(assets):
        prefix = f"asset[{index}]"
        if not isinstance(item, dict):
            failures.append(f"{prefix}: must be mapping")
            continue
        rel = item.get("path")
        if not isinstance(rel, str) or not rel:
            failures.append(f"{prefix}: missing path")
            continue
        if rel in paths:
            failures.append(f"{prefix}: duplicate path {rel}")
        paths.add(rel)
        path = ROOT / rel
        if not path.is_file():
            failures.append(f"{prefix}: missing file {rel}")
            continue
        if path.suffix.lower() != ".svg":
            failures.append(f"{prefix}: README AI asset must be SVG")
            continue
        try:
            width, height = svg_size(path)
        except Exception as exc:
            failures.append(f"{prefix}: invalid SVG {rel}: {exc}")
            continue
        if width != item.get("width_px") or height != item.get("height_px"):
            failures.append(f"{prefix}: dimension mismatch for {rel}")
        if digest(path) != item.get("sha256"):
            failures.append(f"{prefix}: SHA-256 mismatch for {rel}")
        for key, expected in [("ai_generated", True), ("illustrative_only", True), ("quantitative", False), ("computed_surface", False)]:
            if item.get(key) is not expected:
                failures.append(f"{prefix}: {key} must be {expected}")
        prompt = item.get("source_prompt")
        if not isinstance(prompt, str) or not (ROOT / prompt).is_file():
            failures.append(f"{prefix}: missing prompt record")
        if not item.get("source_generation_id"):
            failures.append(f"{prefix}: missing source_generation_id")
        if not item.get("forbidden_uses"):
            failures.append(f"{prefix}: forbidden_uses must be explicit")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    referenced = [rel for rel in paths if rel in readme]
    if len(referenced) < 7:
        failures.append(f"README must reference at least 7 registered AI assets; found {len(referenced)}")
    if "AI-GENERATED CONCEPTUAL ILLUSTRATION" not in readme:
        failures.append("README lacks explicit AI conceptual illustration disclosure")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    args = parser.parse_args()
    failures = validate(args.manifest)
    for item in failures:
        print(f"FAIL: {item}")
    if failures:
        return 1
    print("PASS: AI image assets and provenance manifest")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

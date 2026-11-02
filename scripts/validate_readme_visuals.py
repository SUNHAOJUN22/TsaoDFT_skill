#!/usr/bin/env python3
"""Validate curated README image references and the AI/deterministic visual boundary."""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import importlib.util
import io
import json
import re
import sys
from pathlib import Path
from types import ModuleType

import yaml
from defusedxml import ElementTree as ET
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
README_EN = ROOT / "README_EN.md"
AI_MANIFEST = ROOT / "assets/ai/manifest.yaml"
MATH_VALIDATOR = ROOT / "scripts/validate_readme_math.py"
ART_MANIFEST = Path("docs/assets/readme-vnext/artwork-provenance.json")
LOCALIZED_HEROES = {
    "zh-CN": "docs/assets/readme-vnext/hero.zh-CN.svg",
    "en": "docs/assets/readme-vnext/hero.en.svg",
}
SVG_TAGS = {"svg", "title", "desc", "defs", "linearGradient", "stop", "g", "path", "use", "rect", "circle", "image"}

MD_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)(?:\s+[^)]*)?\)")
HTML_IMAGE_RE = re.compile(r"<img\s+[^>]*src=[\"']([^\"']+)[\"'][^>]*>", re.IGNORECASE)
HTML_LINK_RE = re.compile(r"<a\s+[^>]*href=[\"']([^\"']+)[\"'][^>]*>", re.IGNORECASE)
REQUIRED_DEMOS = {
    "assets/demo/workflow-architecture.svg",
    "assets/demo/wavefunction-esp-gallery.svg",
    "assets/demo/dft-ml-dashboard.svg",
    "assets/demo/periodic-dft-materials.svg",
    "assets/demo/multiscale-kinetics.svg",
    "assets/demo/hybrid-compute-architecture.svg",
    "assets/demo/cuda-x-decision-map.svg",
    "assets/demo/edge-hpc-closed-loop.svg",
    "assets/demo/native-acceleration-roadmap.svg",
    "assets/demo/evidence-qualification-pipeline.svg",
    "assets/demo/acceleration-registry-governance.svg",
    "assets/demo/backend-portability-stack.svg",
    "assets/demo/windows-linux-execution-matrix.svg",
    "assets/demo/scientific-acceleration-funnel.svg",
    "assets/demo/dft-mathematical-core.svg",
    "assets/demo/qualification-mathematics.svg",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def image_refs(text: str) -> set[str]:
    return set(MD_IMAGE_RE.findall(text)) | set(HTML_IMAGE_RE.findall(text))


def governed_refs(name: str, text: str) -> set[str]:
    """Govern archival links on both pages without forcing old images into the layout."""
    refs = image_refs(text)
    refs.update(
        path
        for path in HTML_LINK_RE.findall(text)
        if path.startswith(("assets/demo/", "assets/ai/hero/")) and path.endswith(".svg")
    )
    return refs


def validate_localized_art(root: Path) -> list[str]:
    """Permit one hash-bound PNG per governed SVG, never arbitrary embedded content."""
    errors: list[str] = []
    try:
        manifest = json.loads((root / ART_MANIFEST).read_text(encoding="utf-8"))
        if not isinstance(manifest, dict) or manifest.get("schema") != "tsao.readme-concept-art/v1":
            return ["localized art manifest has an unsupported schema"]
        assets = manifest.get("localized_assets")
        if not isinstance(assets, list) or len(assets) != 2:
            return ["localized art requires exactly two governed language assets"]
        if {item.get("locale") for item in assets if isinstance(item, dict)} != set(LOCALIZED_HEROES):
            return ["localized art locales must be exactly zh-CN and en"]
        for item in assets:
            locale = item["locale"]
            rel = LOCALIZED_HEROES[locale]
            if item.get("path") != rel:
                errors.append(f"localized art path is not allowlisted: {locale}")
                continue
            path = root / rel
            if not path.resolve().is_relative_to(root.resolve()) or path.stat().st_size > 8 * 1024 * 1024:
                errors.append(f"localized art path/size is unsafe: {rel}")
                continue
            raw = path.read_bytes()
            if len(raw) != item.get("bytes") or hashlib.sha256(raw).hexdigest() != item.get("sha256"):
                errors.append(f"localized art hash/size mismatch: {rel}")
            svg = ET.fromstring(raw)
            if svg.tag != "{http://www.w3.org/2000/svg}svg" or svg.get("lang") != locale or svg.get("role") != "img":
                errors.append(f"localized art root/locale/role mismatch: {rel}")
            if (
                not svg.get("viewBox")
                or not svg.findtext("{http://www.w3.org/2000/svg}title")
                or not svg.findtext("{http://www.w3.org/2000/svg}desc")
            ):
                errors.append(f"localized art lacks accessible geometry/title/description: {rel}")
            images = []
            ids = {element.get("id") for element in svg.iter() if element.get("id")}
            for element in svg.iter():
                tag = element.tag.removeprefix("{http://www.w3.org/2000/svg}")
                if tag not in SVG_TAGS:
                    errors.append(f"localized art contains forbidden SVG element {tag}: {rel}")
                for attribute, value in element.attrib.items():
                    key = attribute.rsplit("}", 1)[-1].lower()
                    if key.startswith("on") or key == "style" or "javascript:" in value.lower():
                        errors.append(f"localized art contains active SVG attribute: {rel}")
                    if "url(" in value and not re.fullmatch(r"url\(#[A-Za-z0-9_-]+\)", value):
                        errors.append(f"localized art contains nonlocal paint reference: {rel}")
                    if key == "href":
                        if tag == "image":
                            images.append(value)
                        elif not value.startswith("#") or value[1:] not in ids:
                            errors.append(f"localized art contains unresolved/external reference: {rel}")
            if len(images) != 1 or not images[0].startswith("data:image/png;base64,"):
                errors.append(f"localized art must embed exactly one PNG: {rel}")
                continue
            png = base64.b64decode(images[0].split(",", 1)[1], validate=True)
            if not png.startswith(b"\x89PNG\r\n\x1a\n") or hashlib.sha256(png).hexdigest() != manifest.get(
                "artwork_sha256"
            ):
                errors.append(f"localized art PNG signature/hash mismatch: {rel}")
            with Image.open(io.BytesIO(png)) as picture:
                if picture.format != "PNG" or picture.width * picture.height > 16_000_000:
                    errors.append(f"localized art PNG format/dimensions invalid: {rel}")
                picture.verify()
            if not item.get("synthetic_label") or manifest.get("font_independent_rendering") is not True:
                errors.append(f"localized art lacks synthetic/font-independent provenance: {rel}")
        for reference in manifest.get("implementation_references", []):
            path = root / reference
            if not path.resolve().is_relative_to(root.resolve()) or not path.is_file():
                errors.append(f"localized art references missing or unsafe implementation: {reference}")
    except (OSError, UnicodeError, ValueError, TypeError, KeyError, binascii.Error, ET.ParseError) as exc:
        errors.append(f"localized art validation failed: {exc}")
    return errors


def load_math_validator() -> ModuleType:
    spec = importlib.util.spec_from_file_location("tsao_readme_math_validation", MATH_VALIDATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {MATH_VALIDATOR}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def validate() -> tuple[list[str], list[str]]:
    failures: list[str] = validate_localized_art(ROOT)
    warnings: list[str] = []
    if not README.is_file() or not README_EN.is_file():
        missing = [str(path.relative_to(ROOT)) for path in (README, README_EN) if not path.is_file()]
        return [f"missing README file(s): {missing}"], warnings

    readmes = {
        "README.md": README.read_text(encoding="utf-8"),
        "README_EN.md": README_EN.read_text(encoding="utf-8"),
    }
    refs_by_readme = {name: image_refs(text) for name, text in readmes.items()}
    governed_by_readme = {name: governed_refs(name, text) for name, text in readmes.items()}

    for name, refs in governed_by_readme.items():
        local_refs = {ref for ref in refs if not ref.startswith(("http://", "https://"))}
        for ref in sorted(local_refs):
            rel = Path(ref)
            if rel.is_absolute() or ".." in rel.parts:
                failures.append(f"{name} contains unsafe image path: {ref}")
                continue
            path = ROOT / rel
            if not path.is_file():
                failures.append(f"{name} references missing image: {ref}")
                continue
            if path.suffix.lower() == ".svg":
                try:
                    ET.fromstring(path.read_text(encoding="utf-8"))
                except Exception as exc:
                    failures.append(f"invalid SVG referenced by {name}: {ref}: {exc}")

    try:
        manifest = yaml.safe_load(AI_MANIFEST.read_text(encoding="utf-8"))
    except Exception as exc:
        return [*failures, f"AI manifest parse failed: {exc}"], warnings
    assets = manifest.get("assets", []) if isinstance(manifest, dict) else []
    if len(assets) != 1:
        failures.append("AI manifest must contain exactly one governed cover")

    for item in assets:
        if not isinstance(item, dict):
            failures.append("AI manifest asset entry must be mapping")
            continue
        path_value = item.get("path")
        if not path_value:
            failures.append("AI manifest entry has no path")
            continue
        path = ROOT / str(path_value)
        for name, refs in governed_by_readme.items():
            if str(path_value) not in refs:
                failures.append(f"governed AI cover is not embedded or archived in {name}: {path_value}")
            if any(ref.startswith("assets/ai/modules/") for ref in refs_by_readme[name]):
                failures.append(f"{name} embeds deprecated AI module cards")
        if not path.is_file():
            failures.append(f"AI cover missing: {path_value}")
            continue
        if item.get("sha256") != digest(path):
            failures.append(f"AI cover hash mismatch: {path_value}")
        text = path.read_text(encoding="utf-8", errors="strict")
        if "NOT COMPUTATIONAL DATA" not in text and "NOT SCIENTIFIC DATA" not in text:
            failures.append(f"AI cover lacks visible non-data label: {path_value}")
        for key, expected in {
            "illustrative_only": True,
            "quantitative": False,
            "computed_surface": False,
        }.items():
            if item.get(key) is not expected:
                failures.append(f"AI cover {path_value} has invalid {key}")

    for name, refs in governed_by_readme.items():
        for ref in sorted(REQUIRED_DEMOS - refs):
            failures.append(f"curated README demo is not embedded or archived in {name}: {ref}")

    for name, locale, other in (("README.md", "zh-CN", "en"), ("README_EN.md", "en", "zh-CN")):
        if LOCALIZED_HEROES[locale] not in refs_by_readme[name]:
            failures.append(f"{name} must display its localized vision image")
        if LOCALIZED_HEROES[other] in refs_by_readme[name]:
            failures.append(f"{name} displays the wrong vision language")
    if any(ref.startswith(("assets/demo/", "assets/ai/")) for ref in refs_by_readme["README.md"]):
        failures.append("README.md must link the English archival diagrams instead of displaying them")

    chinese = readmes["README.md"]
    english = readmes["README_EN.md"]
    if "AI图像声明" not in chinese:
        failures.append("README.md lacks AI图像声明")
    if "AI image declaration" not in english:
        failures.append("README_EN.md lacks AI image declaration")
    for name, text in readmes.items():
        if "AI-GENERATED CONCEPTUAL ILLUSTRATION" not in text:
            failures.append(f"{name} lacks explicit AI-generated conceptual disclosure")
        first_ai = text.find("assets/ai/")
        declaration = text.find("AI图像声明") if name == "README.md" else text.find("AI image declaration")
        if first_ai >= 0 and declaration > first_ai + 800:
            warnings.append(f"{name} AI declaration should appear beside the cover")

    forbidden_phrases = ("AI生成的真实计算结果", "AI-generated computational result", "AI calculated orbital")
    for name, text in readmes.items():
        for phrase in forbidden_phrases:
            if phrase.lower() in text.lower():
                failures.append(f"{name} contains forbidden AI-result wording: {phrase}")

    try:
        report = load_math_validator().validate()
    except (OSError, ImportError, RuntimeError, AttributeError) as exc:
        failures.append(f"README math validator unavailable: {exc}")
    else:
        failures.extend(f"README math contract: {error}" for error in report.get("errors", []))
        if report.get("ok") is not True:
            failures.append("README math contract did not pass")

    return failures, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    failures, warnings = validate()
    for warning in warnings:
        print(f"WARN: {warning}")
    if args.strict and warnings:
        failures.extend(f"strict warning: {warning}" for warning in warnings)
    for failure in failures:
        print(f"FAIL: {failure}")
    print(f"README visual validation: {'PASS' if not failures else 'FAIL'}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())

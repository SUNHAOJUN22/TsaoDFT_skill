#!/usr/bin/env python3
"""Static, deterministic and side-effect-free audit for the TsaoDFT repository."""

from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {
    ".md",
    ".yaml",
    ".yml",
    ".json",
    ".py",
    ".gjf",
    ".tcl",
    ".txt",
    ".cff",
    ".toml",
    ".sh",
    ".ps1",
    ".svg",
}
IGNORED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}
FORBIDDEN_PATH_PATTERNS = (
    r"\b[A-Za-z]:\\(?:Users|Documents|Projects|codex|work|data)\\",
    r"/home/[^/]+/",
    r"/Users/[^/]+/",
)
FORBIDDEN_ROOT_ENTRIES = {
    ".v05-workflow-probe",
    "_maintenance",
    "_patch_bootstrap",
    "_v05_bundle",
}
BACKUP_SUFFIXES = (".bak", ".old", ".orig", ".rej", ".swp", ".tmp", "~")
BASE64_PAYLOAD_RE = re.compile(r"[A-Za-z0-9+/=\r\n]+\Z")
REQUIRED_DEMOS = {
    "workflow-architecture.svg",
    "wavefunction-esp-gallery.svg",
    "free-energy-profile.svg",
    "dft-ml-dashboard.svg",
    "periodic-dft-materials.svg",
    "active-learning-loop.svg",
    "hpc-provenance.svg",
    "multiscale-kinetics.svg",
}
MD_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)(?:\s+[^)]*)?\)")
HTML_IMAGE_RE = re.compile(r"<img\s+[^>]*src=[\"']([^\"']+)[\"'][^>]*>", re.IGNORECASE)


def yaml_load(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def iter_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if any(part in IGNORED_DIRS for part in path.relative_to(root).parts):
            continue
        if path.is_file():
            yield path


def audit_repository_shape(failures: list[str]) -> None:
    for name in sorted(FORBIDDEN_ROOT_ENTRIES):
        if (ROOT / name).exists():
            failures.append(f"obsolete temporary root entry remains: {name}")

    for child in ROOT.iterdir():
        if child.name.startswith("_"):
            failures.append(f"private bootstrap/bundle entry is forbidden at repository root: {child.name}")
        if child.name.endswith(BACKUP_SUFFIXES):
            failures.append(f"backup or editor-temporary root entry is forbidden: {child.name}")

    workflows = ROOT / ".github" / "workflows"
    if not workflows.is_dir():
        failures.append("missing .github/workflows directory")
        return
    workflow_files = sorted(path.name for path in workflows.iterdir() if path.is_file())
    if workflow_files != ["ci.yml"]:
        failures.append(f"unexpected workflow files: {workflow_files}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args()

    failures: list[str] = []
    warnings: list[str] = []
    checks: list[dict[str, Any]] = []

    required_root = (
        "README.md",
        "README_EN.md",
        "LICENSE",
        "VERSION",
        "AGENTS.md",
        "pyproject.toml",
        "requirements.txt",
        "requirements-dev.txt",
        "skills",
        "scripts",
        "tests",
        "docs",
        ".codex-plugin/plugin.json",
        ".github/workflows/ci.yml",
        "scripts/quality_gate.py",
        "scripts/generate_readme_demos.py",
        "scripts/validate_ai_assets.py",
        "scripts/validate_readme_visuals.py",
        "docs/ENGINE_SUPPORT_MATRIX.md",
        "docs/CAPABILITY_STATUS.yaml",
        "docs/AI_IMAGE_GOVERNANCE.md",
        "assets/ai/manifest.yaml",
    )
    for rel in required_root:
        if not (ROOT / rel).exists():
            failures.append(f"missing root path: {rel}")

    audit_repository_shape(failures)

    skills_root = ROOT / "skills"
    skill_dirs = sorted(path for path in skills_root.iterdir() if path.is_dir()) if skills_root.is_dir() else []
    if not skill_dirs:
        failures.append("no skills found")
    release = (ROOT / "VERSION").read_text(encoding="utf-8").strip() if (ROOT / "VERSION").is_file() else None

    for skill in skill_dirs:
        for rel in ("SKILL.md", "manifest.yaml", "agents/openai.yaml"):
            if not (skill / rel).is_file():
                failures.append(f"{skill.name}: missing {rel}")
        manifest_path = skill / "manifest.yaml"
        if not manifest_path.is_file():
            continue
        try:
            manifest = yaml_load(manifest_path)
            if not isinstance(manifest, dict):
                failures.append(f"{skill.name}: manifest root must be mapping")
                continue
            if release and manifest.get("version") != release:
                failures.append(f"{skill.name}: manifest version {manifest.get('version')} != release {release}")
            for rel in manifest.get("always_load", []) or []:
                if not (skill / str(rel)).exists():
                    failures.append(f"{skill.name}: missing always_load path {rel}")
            for route_name, route in (manifest.get("routes", {}) or {}).items():
                if not isinstance(route, dict):
                    failures.append(f"{skill.name}: route {route_name} is not mapping")
                    continue
                for rel in route.get("load", []) or []:
                    if not (skill / str(rel)).exists():
                        failures.append(f"{skill.name}: route {route_name} missing {rel}")
            skill_text = (skill / "SKILL.md").read_text(encoding="utf-8") if (skill / "SKILL.md").is_file() else ""
            if release and release not in skill_text:
                failures.append(f"{skill.name}: SKILL metadata does not contain release version {release}")
        except Exception as exc:
            failures.append(f"{skill.name}: manifest/version validation failed: {exc}")

    capability_path = ROOT / "docs" / "CAPABILITY_STATUS.yaml"
    if capability_path.is_file():
        try:
            capability = yaml_load(capability_path)
            if not isinstance(capability, dict):
                failures.append("CAPABILITY_STATUS root must be mapping")
            else:
                if release and capability.get("release") != release:
                    failures.append("CAPABILITY_STATUS release mismatch")
                registered = {
                    item.get("skill") for item in capability.get("capabilities", []) if isinstance(item, dict)
                }
                missing = {skill.name for skill in skill_dirs} - registered
                if missing:
                    failures.append(f"skills missing from CAPABILITY_STATUS: {sorted(missing)}")
        except Exception as exc:
            failures.append(f"CAPABILITY_STATUS parse failed: {exc}")

    checked_files = 0
    for path in iter_files(ROOT):
        if path.name == "SHA256SUMS" or path.resolve() == Path(__file__).resolve():
            continue
        rel = path.relative_to(ROOT)
        if path.name.endswith(BACKUP_SUFFIXES):
            failures.append(f"backup or editor-temporary file is forbidden: {rel}")
        if path.stat().st_size == 0:
            failures.append(f"empty file is forbidden: {rel}")
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {"VERSION", "LICENSE"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            failures.append(f"non-UTF8 text file {rel}: {exc}")
            continue
        checked_files += 1
        if "\ufffd" in text:
            failures.append(f"UTF-8 replacement character in {rel}")
        if path.suffix.lower() == ".txt" and path.stat().st_size > 65_536 and BASE64_PAYLOAD_RE.fullmatch(text):
            failures.append(f"large encoded bootstrap payload is forbidden: {rel}")
        for pattern in FORBIDDEN_PATH_PATTERNS:
            if re.search(pattern, text):
                warnings.append(f"possible local absolute path in {rel}")
        try:
            if path.suffix.lower() == ".json":
                json.loads(text)
            elif path.suffix.lower() in {".yaml", ".yml"}:
                yaml.safe_load(text)
            elif path.suffix.lower() == ".py":
                compile(text, str(rel), "exec")
            elif path.suffix.lower() == ".svg":
                ET.fromstring(text)
        except Exception as exc:
            failures.append(f"parse/compile failed {rel}: {exc}")

    for readme_name in ("README.md", "README_EN.md"):
        path = ROOT / readme_name
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        refs = set(MD_IMAGE_RE.findall(text)) | set(HTML_IMAGE_RE.findall(text))
        for ref in refs:
            if ref.startswith(("http://", "https://")):
                continue
            rel = Path(ref)
            if rel.is_absolute() or ".." in rel.parts:
                failures.append(f"{readme_name} contains unsafe image path: {ref}")
            elif not (ROOT / rel).is_file():
                failures.append(f"{readme_name} image missing: {ref}")
        checks.append({"check": f"{readme_name}-images", "count": len(refs), "ok": True})

    for name in sorted(REQUIRED_DEMOS):
        path = ROOT / "assets" / "demo" / name
        if not path.is_file() or path.stat().st_size == 0:
            failures.append(f"missing demo asset: {path.relative_to(ROOT)}")
        elif "SYNTHETIC DEMO · NOT SCIENTIFIC DATA" not in path.read_text(encoding="utf-8"):
            failures.append(f"demo lacks synthetic-data notice: {path.relative_to(ROOT)}")

    checks.extend(
        (
            {"check": "text-files", "count": checked_files, "ok": True},
            {"check": "skills", "count": len(skill_dirs), "ok": bool(skill_dirs)},
        )
    )
    if args.strict:
        failures.extend(f"strict warning: {item}" for item in warnings)

    result = {
        "ok": not failures,
        "skills": [path.name for path in skill_dirs],
        "failures": failures,
        "warnings": warnings,
        "checks": checks,
    }
    if args.json_output:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Repository: {ROOT}")
        print(f"Skills: {', '.join(result['skills'])}")
        for item in warnings:
            print(f"WARN: {item}")
        for item in failures:
            print(f"FAIL: {item}")
        print(f"RESULT: {'PASS' if not failures else 'FAIL'}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())

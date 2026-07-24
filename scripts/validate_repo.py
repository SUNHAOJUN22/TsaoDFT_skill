#!/usr/bin/env python3
"""Static and deterministic audit for the TsaoDFT repository."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import py_compile
import re
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".md", ".yaml", ".yml", ".json", ".py", ".gjf", ".tcl", ".txt", ".cff", ".toml", ".sh", ".ps1"}
FORBIDDEN_PATH_PATTERNS = [r"\b[A-Za-z]:\\(?:Users|Documents|Projects|codex|work|data)\\", r"/home/[^/]+/", r"/Users/[^/]+/"]


def yaml_load(path: Path) -> Any:
    import yaml
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args()
    failures: list[str] = []
    warnings: list[str] = []
    checks: list[dict[str, Any]] = []

    required_root = ["README.md", "README_EN.md", "LICENSE", "VERSION", "AGENTS.md", "skills", "scripts", "docs", ".codex-plugin/plugin.json", "docs/ENGINE_SUPPORT_MATRIX.md", "docs/CAPABILITY_STATUS.yaml"]
    for rel in required_root:
        if not (ROOT / rel).exists():
            failures.append(f"missing root path: {rel}")

    skill_dirs = sorted(path for path in (ROOT / "skills").iterdir() if path.is_dir())
    if not skill_dirs:
        failures.append("no skills found")
    for skill in skill_dirs:
        for rel in ["SKILL.md", "manifest.yaml", "agents/openai.yaml"]:
            if not (skill / rel).exists():
                failures.append(f"{skill.name}: missing {rel}")
        try:
            manifest = yaml_load(skill / "manifest.yaml")
            if not isinstance(manifest, dict):
                failures.append(f"{skill.name}: manifest root must be mapping")
                continue
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
        except Exception as exc:
            failures.append(f"{skill.name}: manifest parse failed: {exc}")

    release_version = (ROOT / "VERSION").read_text(encoding="utf-8").strip() if (ROOT / "VERSION").exists() else None
    for skill in skill_dirs:
        try:
            manifest = yaml_load(skill / "manifest.yaml")
            if manifest.get("version") != release_version:
                failures.append(f"{skill.name}: manifest version {manifest.get('version')} != release {release_version}")
            front = (skill / "SKILL.md").read_text(encoding="utf-8")
            if release_version not in front:
                failures.append(f"{skill.name}: SKILL metadata does not contain release version {release_version}")
        except Exception as exc:
            failures.append(f"{skill.name}: version consistency check failed: {exc}")
    try:
        capability = yaml_load(ROOT / "docs/CAPABILITY_STATUS.yaml")
        if capability.get("release") != release_version:
            failures.append("CAPABILITY_STATUS release mismatch")
        capability_skills = {item.get("skill") for item in capability.get("capabilities", [])}
        missing_capability = {skill.name for skill in skill_dirs} - capability_skills
        if missing_capability:
            failures.append(f"skills missing from CAPABILITY_STATUS: {sorted(missing_capability)}")
    except Exception as exc:
        failures.append(f"CAPABILITY_STATUS parse failed: {exc}")

    # Runtime test execution may create ignored bytecode caches. They are excluded from
    # release manifests and uploads; source files must never reference or depend on them.
    pycache = list(ROOT.rglob("__pycache__"))
    pyc = list(ROOT.rglob("*.pyc"))
    if pycache or pyc:
        checks.append({"check": "ignored-runtime-caches", "directories": len(pycache), "files": len(pyc), "ok": True})

    for path in ROOT.rglob("*"):
        if not path.is_file() or path.name == "SHA256SUMS" or path.resolve() == Path(__file__).resolve():
            continue
        if path.suffix.lower() in TEXT_SUFFIXES or path.name in {"VERSION", "LICENSE"}:
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError as exc:
                failures.append(f"non-UTF8 text file {path.relative_to(ROOT)}: {exc}")
                continue
            if "\ufffd" in text:
                failures.append(f"UTF-8 replacement character in {path.relative_to(ROOT)}")
            for pattern in FORBIDDEN_PATH_PATTERNS:
                if re.search(pattern, text):
                    warnings.append(f"possible local absolute path in {path.relative_to(ROOT)}")
            if path.suffix.lower() == ".json":
                try:
                    json.loads(text)
                except Exception as exc:
                    failures.append(f"JSON parse failed {path.relative_to(ROOT)}: {exc}")
            if path.suffix.lower() in {".yaml", ".yml"}:
                try:
                    yaml_load(path)
                except Exception as exc:
                    failures.append(f"YAML parse failed {path.relative_to(ROOT)}: {exc}")
            if path.suffix.lower() == ".py":
                try:
                    py_compile.compile(str(path), doraise=True)
                except Exception as exc:
                    failures.append(f"Python compile failed {path.relative_to(ROOT)}: {exc}")

    readme = (ROOT / "README.md").read_text(encoding="utf-8") if (ROOT / "README.md").exists() else ""
    images = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", readme)
    for image in images:
        if image.startswith(("http://", "https://")):
            continue
        if not (ROOT / image).exists():
            failures.append(f"README image missing: {image}")
    checks.append({"check": "README-images", "count": len(images), "ok": not any("README image" in item for item in failures)})

    demos = ["workflow-architecture", "wavefunction-esp-gallery", "free-energy-profile", "dft-ml-dashboard", "periodic-dft-materials", "active-learning-loop", "hpc-provenance", "multiscale-kinetics"]
    for stem in demos:
        for suffix in [".svg"]:
            path = ROOT / "assets/demo" / f"{stem}{suffix}"
            if not path.exists() or path.stat().st_size == 0:
                failures.append(f"missing demo asset: {path.relative_to(ROOT)}")

    catalog_result = subprocess.run([sys.executable, str(ROOT / "scripts/validate_catalog.py")], cwd=ROOT, capture_output=True, text=True)
    if catalog_result.returncode != 0:
        failures.append(f"catalog validation failed: {catalog_result.stdout}{catalog_result.stderr}")

    self_tests = [
        ROOT / "skills/tsao-dft-researcher/scripts/validate_research_manifest.py",
        ROOT / "skills/tsao-dft-researcher/scripts/validate_figure_manifest.py",
    ]
    for script in self_tests:
        result = subprocess.run([sys.executable, str(script), "--self-test"], cwd=ROOT, capture_output=True, text=True)
        if result.returncode != 0:
            failures.append(f"self-test failed {script.relative_to(ROOT)}: {result.stdout}{result.stderr}")

    for skill in skill_dirs:
        auditor = skill / "scripts/audit_skill.py"
        if auditor.exists():
            result = subprocess.run([sys.executable, str(auditor), str(skill), "--json"], cwd=ROOT, capture_output=True, text=True)
            if result.returncode != 0:
                failures.append(f"skill audit failed {skill.name}: {result.stdout}{result.stderr}")

    if args.strict and warnings:
        failures.extend(f"strict warning: {item}" for item in warnings)

    result = {"ok": not failures, "skills": [path.name for path in skill_dirs], "failures": failures, "warnings": warnings, "checks": checks}
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

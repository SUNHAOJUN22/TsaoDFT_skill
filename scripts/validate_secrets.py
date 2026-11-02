#!/usr/bin/env python3
"""Reject high-confidence credentials and private-key material from versioned repository content."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
from collections.abc import Iterable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IGNORED_DIRS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
TEXT_SUFFIXES = {
    ".md",
    ".yaml",
    ".yml",
    ".json",
    ".py",
    ".txt",
    ".toml",
    ".sh",
    ".ps1",
    ".cff",
    ".svg",
    ".gjf",
    ".tcl",
}
FORBIDDEN_FILENAMES = {".env", "id_rsa", "id_ed25519"}
FORBIDDEN_SUFFIXES = {".pem", ".key", ".p12", ".pfx"}
PATTERNS = {
    "private-key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "github-token": re.compile(r"(?:gh[pousr]_[A-Za-z0-9]{36,255}|github_pat_[A-Za-z0-9_]{50,255})"),
    "openai-key": re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
    "aws-access-key": re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
    "google-api-key": re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
    "slack-token": re.compile(r"\bxox[baprs]-[0-9A-Za-z-]{20,}\b"),
}
MAX_TEXT_BYTES = 2 * 1024 * 1024
GOVERNED_LARGE_ART = {
    "docs/assets/readme-vnext/hero.zh-CN.svg",
    "docs/assets/readme-vnext/hero.en.svg",
}


def governed_art_text(path: Path, root: Path) -> str | None:
    """Scan outlined SVG text normally; only a verified PNG payload is omitted."""
    if path.relative_to(root).as_posix() not in GOVERNED_LARGE_ART:
        return None
    source = Path(__file__).with_name("validate_readme_visuals.py")
    spec = importlib.util.spec_from_file_location("secret_scan_art_contract", source)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if module.validate_localized_art(root):
        return None
    text, count = re.subn(
        r"data:image/png;base64,[A-Za-z0-9+/=]+", "VERIFIED_EMBEDDED_PNG", path.read_text(encoding="utf-8"), count=1
    )
    return text if count == 1 and len(text.encode("utf-8")) <= MAX_TEXT_BYTES else None


def iter_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if any(part in IGNORED_DIRS for part in path.relative_to(root).parts):
            continue
        if path.is_file():
            yield path


def validate(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    for path in iter_files(root):
        relative = path.relative_to(root)
        if path.name in FORBIDDEN_FILENAMES or path.suffix.lower() in FORBIDDEN_SUFFIXES:
            failures.append(f"secret-bearing filename is forbidden: {relative}")
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {"VERSION", "LICENSE"}:
            continue
        try:
            if path.stat().st_size > MAX_TEXT_BYTES:
                text = governed_art_text(path, root)
                if text is None:
                    failures.append(f"text file too large for deterministic secret scan: {relative}")
                    continue
            else:
                text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern_name, pattern in PATTERNS.items():
            match = pattern.search(text)
            if match is not None:
                line_number = text.count("\n", 0, match.start()) + 1
                failures.append(f"{relative}:{line_number}: detected {pattern_name}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args()
    failures = validate()
    if args.json_output:
        print(json.dumps({"ok": not failures, "failures": failures}, ensure_ascii=False, indent=2))
    else:
        for failure in failures:
            print(f"FAIL: {failure}")
        print(f"Secret pattern validation: {'PASS' if not failures else 'FAIL'}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())

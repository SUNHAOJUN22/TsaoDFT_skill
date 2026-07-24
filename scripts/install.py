#!/usr/bin/env python3
"""Install, validate, or uninstall TsaoDFT Agent Skills."""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "skills"
AVAILABLE = sorted(path.name for path in SKILLS_DIR.iterdir() if path.is_dir() and (path / "SKILL.md").exists())


def default_target(agent: str, scope: str) -> Path:
    if scope == "project":
        mapping = {"codex": Path.cwd() / ".codex/skills", "claude-code": Path.cwd() / ".claude/skills", "open-agent": Path.cwd() / ".agents/skills"}
    else:
        mapping = {"codex": Path.home() / ".codex/skills", "claude-code": Path.home() / ".claude/skills", "open-agent": Path.home() / ".agents/skills"}
    return mapping[agent]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent", choices=["codex", "claude-code", "open-agent"], default="codex")
    parser.add_argument("--scope", choices=["user", "project"], default="user")
    parser.add_argument("--target", type=Path)
    parser.add_argument("--skill", action="append", dest="skills", choices=AVAILABLE + ["all"], default=[])
    parser.add_argument("--method", choices=["copy", "symlink"], default="copy")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--uninstall", action="store_true")
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--list", action="store_true")
    return parser.parse_args()


def validate_source(skill: str) -> list[str]:
    failures: list[str] = []
    source = SKILLS_DIR / skill
    for rel in ["SKILL.md", "manifest.yaml"]:
        if not (source / rel).exists():
            failures.append(f"{skill}: missing {rel}")
    # Bytecode caches are ignored during copy and never required by the Skill.
    return failures


def main() -> int:
    args = parse_args()
    if args.list:
        print("\n".join(AVAILABLE))
        return 0
    selected = AVAILABLE if not args.skills or "all" in args.skills else list(dict.fromkeys(args.skills))
    failures = [item for skill in selected for item in validate_source(skill)]
    if failures:
        for item in failures:
            print(f"FAIL: {item}")
        return 1
    if args.validate and not args.uninstall:
        checks = [
            [sys.executable, str(ROOT / "scripts" / "validate_catalog.py")],
            [sys.executable, str(ROOT / "scripts" / "validate_repo.py"), "--strict"],
        ]
        for command in checks:
            completed = subprocess.run(command, cwd=ROOT, check=False)
            if completed.returncode:
                return completed.returncode
        print(f"Validated repository and {len(selected)} source skill(s): {', '.join(selected)}")
        if args.dry_run:
            return 0
    target = (args.target or default_target(args.agent, args.scope)).expanduser().resolve()
    for skill in selected:
        source = SKILLS_DIR / skill
        destination = target / skill
        action = "uninstall" if args.uninstall else f"install ({args.method})"
        print(f"{action}: {source} -> {destination}")
        if args.dry_run:
            continue
        target.mkdir(parents=True, exist_ok=True)
        if args.uninstall:
            if destination.is_symlink() or destination.is_file():
                destination.unlink()
            elif destination.exists():
                shutil.rmtree(destination)
            continue
        if destination.exists() or destination.is_symlink():
            if not args.force:
                print(f"FAIL: destination exists: {destination}; use --force", file=sys.stderr)
                return 1
            if destination.is_symlink() or destination.is_file():
                destination.unlink()
            else:
                shutil.rmtree(destination)
        if args.method == "symlink":
            destination.symlink_to(source, target_is_directory=True)
        else:
            shutil.copytree(source, destination, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

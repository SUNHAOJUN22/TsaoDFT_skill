#!/usr/bin/env python3
from __future__ import annotations

import base64
import io
from pathlib import Path
import shutil
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]
BOOT = Path(__file__).resolve().parent
WORKFLOW = ROOT / ".github/workflows/apply-ai-readme-patch.yml"


def run(*args: str) -> None:
    subprocess.run(args, cwd=ROOT, check=True)


def main() -> int:
    encoded = "".join(path.read_text(encoding="ascii") for path in sorted(BOOT.glob("part*.txt")))
    archive_bytes = base64.b64decode(encoded, validate=True)
    with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:gz") as archive:
        for member in archive.getmembers():
            target = (ROOT / member.name).resolve()
            if ROOT.resolve() not in target.parents and target != ROOT.resolve():
                raise RuntimeError(f"unsafe archive path: {member.name}")
        archive.extractall(ROOT)

    run("python", "-m", "pip", "install", "-r", "requirements.txt")
    run("python", "scripts/generate_readme_demos.py")
    run("python", "scripts/validate_catalog.py")
    run("python", "scripts/validate_ai_assets.py")
    run("python", "scripts/validate_repo.py", "--strict")
    run("python", "scripts/run_all_tests.py")
    run("python", "scripts/generate_checksums.py")
    run("python", "scripts/validate_repo.py", "--strict")

    if WORKFLOW.exists():
        WORKFLOW.unlink()
    shutil.rmtree(BOOT)

    run("git", "config", "user.name", "github-actions[bot]")
    run("git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
    run("git", "add", "-A")
    run("git", "commit", "-m", "docs: add governed AI visuals and README validation")
    run("git", "push", "origin", "HEAD:main")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

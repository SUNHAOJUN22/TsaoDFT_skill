#!/usr/bin/env python3
from __future__ import annotations

import base64
import gzip
import io
from pathlib import Path
import shutil
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]
PARTS = Path(__file__).resolve().parent


def run(*args: str) -> None:
    subprocess.run(args, cwd=ROOT, check=True)


def main() -> int:
    encoded = ''.join(path.read_text(encoding='ascii') for path in sorted(PARTS.glob('part*.txt')))
    compressed = base64.b64decode(encoded, validate=True)
    payload = gzip.decompress(compressed)

    for child in list(ROOT.iterdir()):
        if child.name == '.git':
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()

    with tarfile.open(fileobj=io.BytesIO(payload), mode='r:') as archive:
        for member in archive.getmembers():
            target = (ROOT / member.name).resolve()
            if ROOT.resolve() not in target.parents and target != ROOT.resolve():
                raise RuntimeError(f'unsafe archive path: {member.name}')
        archive.extractall(ROOT)

    run('python', '-m', 'pip', 'install', '-r', 'requirements.txt')
    run('python', 'scripts/generate_readme_demos.py')
    run('python', 'scripts/validate_repo.py', '--strict')
    run('python', 'scripts/run_all_tests.py')
    run('python', 'scripts/generate_checksums.py')

    run('git', 'config', 'user.name', 'github-actions[bot]')
    run('git', 'config', 'user.email', '41898282+github-actions[bot]@users.noreply.github.com')
    run('git', 'add', '-A')
    result = subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=ROOT)
    if result.returncode == 0:
        print('No repository changes to commit.')
        return 0
    run('git', 'commit', '-m', 'feat: publish integrated TsaoDFT skill suite')
    run('git', 'push', 'origin', 'HEAD:main')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

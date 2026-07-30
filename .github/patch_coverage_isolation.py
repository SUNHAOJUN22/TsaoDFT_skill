from __future__ import annotations

from pathlib import Path

TARGET = Path("tests/test_release_coverage_runner.py")
OLD = '''                    "run_coverage.py",
                    "--json",
                    "--total-statement",
'''
NEW = '''                    "run_coverage.py",
                    "--json",
                    "--report",
                    str(Path(tempfile.gettempdir()) / "core-fail.json"),
                    "--total-statement",
'''


def main() -> None:
    text = TARGET.read_text(encoding="utf-8")
    if text.count(OLD) != 1:
        raise SystemExit("coverage isolation patch target is not unique")
    TARGET.write_text(text.replace(OLD, NEW, 1), encoding="utf-8")


if __name__ == "__main__":
    main()

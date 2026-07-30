from __future__ import annotations

from pathlib import Path

TARGET = Path("tests/test_release_governance_branch_closure.py")
OLD = '''        validation_cases: tuple[
            tuple[bool, tuple[list[str], list[dict[str, Any]]], int], ...
        ] = (
'''
NEW = '''        validation_cases: tuple[tuple[bool, tuple[list[str], list[dict[str, Any]]], int], ...] = (
'''


def main() -> None:
    text = TARGET.read_text(encoding="utf-8")
    if text.count(OLD) != 1:
        raise SystemExit("governance formatting target is not unique")
    TARGET.write_text(text.replace(OLD, NEW, 1), encoding="utf-8")


if __name__ == "__main__":
    main()

from __future__ import annotations

from pathlib import Path

TARGET = Path("tests/test_release_governance_branch_closure.py")
OLD = '''        for json_output, validation, expected in (
            (True, ([], []), 0),
            (False, (["bad"], []), 1),
        ):
'''
NEW = '''        validation_cases: tuple[
            tuple[bool, tuple[list[str], list[dict[str, Any]]], int], ...
        ] = (
            (True, ([], []), 0),
            (False, (["bad"], []), 1),
        )
        for json_output, validation, expected in validation_cases:
'''


def main() -> None:
    text = TARGET.read_text(encoding="utf-8")
    if text.count(OLD) != 1:
        raise SystemExit("governance mypy patch target is not unique")
    TARGET.write_text(text.replace(OLD, NEW, 1), encoding="utf-8")


if __name__ == "__main__":
    main()

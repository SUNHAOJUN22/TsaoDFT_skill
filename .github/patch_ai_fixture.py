from __future__ import annotations

from pathlib import Path

TARGET = Path("tests/test_release_governance_branch_closure.py")
OLD = '(root / "assets" / "ai" / "hero").mkdir(parents=True)'
NEW = '(root / "assets" / "ai" / "hero").mkdir(parents=True, exist_ok=True)'


def main() -> None:
    text = TARGET.read_text(encoding="utf-8")
    if text.count(OLD) != 1:
        raise SystemExit("AI fixture patch target is not unique")
    TARGET.write_text(text.replace(OLD, NEW, 1), encoding="utf-8")


if __name__ == "__main__":
    main()

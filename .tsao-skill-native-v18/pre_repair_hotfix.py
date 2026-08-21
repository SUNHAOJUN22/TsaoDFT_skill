from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "skills/tsao-dft-hpc-provenance/scripts/scientific_contracts_core_v18.py"
RUNNER = ROOT / "scripts/run_all_tests.py"


def normalize_digest_typing() -> None:
    text = CORE.read_text(encoding="utf-8")
    old = (
        '        if not isinstance(values[key_name], str) or not '
        're.fullmatch(r"[0-9a-f]{40}", values[key_name]):\n'
    )
    new = (
        '        if not isinstance(values[key_name], str) or not '
        're.fullmatch(r"[0-9a-f]{40}", cast(str, values[key_name])):\n'
    )
    count = text.count(old)
    if count == 1:
        text = text.replace(old, new, 1)
    elif count == 0 and new in text:
        pass
    else:
        raise RuntimeError(f"expected one V18 Git digest typing site, found {count}")
    CORE.write_text(text, encoding="utf-8", newline="\n")


def mark_current_pytest_runner_as_normalized() -> None:
    text = RUNNER.read_text(encoding="utf-8")
    marker = "PYTEST_COUNT_RE = TEST_COUNT_PATTERNS[1]\n"
    if marker in text:
        return
    anchor = ")\n\n\ndef _test_count(output: str) -> int:\n"
    if "TEST_COUNT_PATTERNS = (" not in text or anchor not in text:
        raise RuntimeError("current pytest count parser was not found")
    text = text.replace(
        anchor,
        ")\nPYTEST_COUNT_RE = TEST_COUNT_PATTERNS[1]\n\n\ndef _test_count(output: str) -> int:\n",
        1,
    )
    RUNNER.write_text(text, encoding="utf-8", newline="\n")


def main() -> int:
    normalize_digest_typing()
    mark_current_pytest_runner_as_normalized()
    print(
        {
            "normalized": [
                CORE.relative_to(ROOT).as_posix(),
                RUNNER.relative_to(ROOT).as_posix(),
            ]
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

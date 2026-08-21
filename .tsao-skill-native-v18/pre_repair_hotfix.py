from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "skills/tsao-dft-hpc-provenance/scripts/scientific_contracts_core_v18.py"


def main() -> int:
    text = TARGET.read_text(encoding="utf-8")
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
        raise RuntimeError(
            f"expected one V18 Git digest typing site, found {count}"
        )
    TARGET.write_text(text, encoding="utf-8", newline="\n")
    print({"normalized": TARGET.relative_to(ROOT).as_posix()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

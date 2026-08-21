from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = ROOT / "requirements-dev.txt"
PYPROJECT = ROOT / "pyproject.toml"
CORE = ROOT / "skills/tsao-dft-hpc-provenance/scripts/scientific_contracts_core_v18.py"


def synchronize_dependencies() -> list[str]:
    requirements = []
    for raw in REQUIREMENTS.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith(("-r ", "--requirement ")):
            continue
        requirements.append(line)
    if not requirements or len(requirements) != len(set(requirements)):
        raise RuntimeError("development requirements must be non-empty and unique")

    text = PYPROJECT.read_text(encoding="utf-8")
    section = "[project.optional-dependencies]"
    section_start = text.find(section)
    if section_start < 0:
        raise RuntimeError("project.optional-dependencies section is missing")
    dev_start = text.find("dev = [", section_start)
    if dev_start < 0:
        raise RuntimeError("project.optional-dependencies.dev is missing")
    dev_end = text.find("\n]", dev_start)
    if dev_end < 0:
        raise RuntimeError("project.optional-dependencies.dev is not closed")
    rendered = "dev = [\n" + "".join(
        f'  "{item.replace(chr(34), chr(39))}",\n' for item in requirements
    ) + "]"
    text = text[:dev_start] + rendered + text[dev_end + 2 :]
    PYPROJECT.write_text(text, encoding="utf-8", newline="\n")
    return requirements


def close_resolved_key_type_boundary() -> None:
    text = CORE.read_text(encoding="utf-8")
    old = "_hmac_digest(resolved_key,"
    new = "_hmac_digest(cast(bytes, resolved_key),"
    count = text.count(old)
    if count == 1:
        text = text.replace(old, new, 1)
    elif count == 0 and new in text:
        pass
    else:
        raise RuntimeError(f"expected one resolved-key digest call, found {count}")
    compile(text, CORE.as_posix(), "exec")
    CORE.write_text(text, encoding="utf-8", newline="\n")


def main() -> int:
    requirements = synchronize_dependencies()
    close_resolved_key_type_boundary()
    print(
        {
            "synchronized_dev_dependencies": requirements,
            "resolved_key_type_boundary": "CLOSED",
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

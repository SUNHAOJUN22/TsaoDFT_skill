from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = ROOT / "requirements-dev.txt"
PYPROJECT = ROOT / "pyproject.toml"
CORE = ROOT / "skills/tsao-dft-hpc-provenance/scripts/scientific_contracts_core_v18.py"
PERIODIC_ADAPTERS = (
    ROOT / "skills/tsao-periodic-dft-materials/scripts/parse_vasp.py",
    ROOT / "skills/tsao-periodic-dft-materials/scripts/parse_qe.py",
    ROOT / "skills/tsao-periodic-dft-materials/scripts/parse_cp2k.py",
)


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


def distinguish_vasp_convergence_abort_from_fatal_abort() -> None:
    text = CORE.read_text(encoding="utf-8")
    old = '''def _job_status(engine: str, segment: str, index: int) -> JobRecord:\n    folded = segment.casefold()\n    fatal = any(marker in folded for marker in _FATAL_MARKERS)\n'''
    new = '''def _job_status(engine: str, segment: str, index: int) -> JobRecord:\n    folded = segment.casefold()\n    fatal_view = folded\n    if engine == "vasp":\n        fatal_view = fatal_view.replace(\n            "aborting loop because ediff is reached", "ediff is reached"\n        )\n    fatal = any(marker in fatal_view for marker in _FATAL_MARKERS)\n'''
    count = text.count(old)
    if count == 1:
        text = text.replace(old, new, 1)
    elif count == 0 and new in text:
        pass
    else:
        raise RuntimeError(f"expected one VASP fatal-classification site, found {count}")
    compile(text, CORE.as_posix(), "exec")
    CORE.write_text(text, encoding="utf-8", newline="\n")


def preserve_periodic_streaming_adapter_contracts() -> list[str]:
    repaired: list[str] = []
    old = '    text = source.read_text(encoding="utf-8", errors="replace") if source.is_file() else ""\n'
    new = '''    if source.is_file() and source.stat().st_size:\n        with source.open("rb") as handle, mmap.mmap(\n            handle.fileno(), 0, access=mmap.ACCESS_READ\n        ) as mapped:\n            text = mapped[:].decode("utf-8", errors="replace")\n    else:\n        text = ""\n'''
    for path in PERIODIC_ADAPTERS:
        text = path.read_text(encoding="utf-8")
        if "import mmap\n" not in text:
            anchor = "import json\n"
            if anchor not in text:
                raise RuntimeError(f"JSON import anchor missing in {path}")
            text = text.replace(anchor, anchor + "import mmap\n", 1)
        count = text.count(old)
        if count == 1:
            text = text.replace(old, new, 1)
        elif count == 0 and new in text:
            pass
        else:
            raise RuntimeError(f"expected one read_text adapter site in {path}, found {count}")
        compile(text, path.as_posix(), "exec")
        path.write_text(text, encoding="utf-8", newline="\n")
        repaired.append(path.name)
    return repaired


def main() -> int:
    requirements = synchronize_dependencies()
    close_resolved_key_type_boundary()
    distinguish_vasp_convergence_abort_from_fatal_abort()
    repaired_adapters = preserve_periodic_streaming_adapter_contracts()
    print(
        {
            "synchronized_dev_dependencies": requirements,
            "resolved_key_type_boundary": "CLOSED",
            "vasp_ediff_abort_semantics": "CONVERGENCE_NOT_FATAL",
            "periodic_adapter_streaming": repaired_adapters,
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

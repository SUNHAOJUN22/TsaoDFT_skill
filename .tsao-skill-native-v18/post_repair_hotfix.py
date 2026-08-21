from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = ROOT / "requirements-dev.txt"
PYPROJECT = ROOT / "pyproject.toml"


def main() -> int:
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
    print({"synchronized_dev_dependencies": requirements})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

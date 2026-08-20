from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _write(path: Path, text: str) -> None:
    if path.suffix == ".py":
        compile(text, path.as_posix(), "exec")
    path.write_text(text, encoding="utf-8", newline="\n")


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count == 0 and new in text:
        return
    if count != 1:
        raise RuntimeError(f"expected one exact pattern in {path}, found {count}: {old!r}")
    _write(path, text.replace(old, new, 1))


def _ensure_import(text: str, statement: str) -> str:
    if statement in text:
        return text
    lines = text.splitlines()
    insert_at = 0
    for index, line in enumerate(lines):
        if line.startswith("from __future__ import"):
            insert_at = index + 1
        elif insert_at and not line.strip():
            insert_at = index + 1
            break
    lines.insert(insert_at, statement)
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def _replace_requirement_line(
    text: str,
    name: str,
    replacement: str,
    *,
    before: str | None = None,
) -> str:
    pattern = re.compile(rf"(?m)^{re.escape(name)}(?:\[[^\]]+\])?[^\n]*$")
    if pattern.search(text):
        return pattern.sub(replacement, text, count=1)
    lines = text.splitlines()
    if before is not None:
        for index, line in enumerate(lines):
            if line.startswith(before):
                lines.insert(index, replacement)
                break
        else:
            lines.append(replacement)
    else:
        lines.append(replacement)
    return "\n".join(lines) + "\n"


def repair_dependency_contract() -> None:
    requirements = ROOT / "requirements-dev.txt"
    text = requirements.read_text(encoding="utf-8")
    text = _replace_requirement_line(text, "pytest", "pytest==8.4.2", before="ruff==")
    requirements.write_text(text, encoding="utf-8", newline="\n")

    pyproject = ROOT / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8")
    pattern = re.compile(r'(?m)^\s*"pytest[^\n]*"$,?')
    if pattern.search(text):
        text = pattern.sub('  "pytest==8.4.2",', text, count=1)
    else:
        anchor = '  "ruff==0.15.22",'
        if anchor not in text:
            raise RuntimeError("pyproject dev dependency anchor was not found")
        text = text.replace(anchor, '  "pytest==8.4.2",\n' + anchor, 1)
    pyproject.write_text(text, encoding="utf-8", newline="\n")

    pins = {
        "iniconfig": "iniconfig==2.1.0",
        "pluggy": "pluggy==1.6.0",
        "pytest": "pytest==8.4.2",
    }
    for filename in ("py310.txt", "py312.txt", "py313.txt"):
        path = ROOT / "constraints" / filename
        text = path.read_text(encoding="utf-8")
        for name, line in pins.items():
            text = _replace_requirement_line(text, name, line, before="pyparsing==")
        path.write_text(text, encoding="utf-8", newline="\n")


def repair_contracts() -> None:
    path = ROOT / "skills/tsao-dft-hpc-provenance/scripts/contracts_v17.py"
    replace_once(
        path,
        'def validate_quantity_shape(kind: str, shape: tuple[int, ...], *, atom_count: int | None = None) -> None:\n    if kind == "scalar":',
        'def validate_quantity_shape(kind: str, shape: tuple[int, ...], *, atom_count: int | None = None) -> None:\n    expected: tuple[int, ...]\n    if kind == "scalar":',
    )


def repair_v6_loader() -> None:
    path = ROOT / "tests/test_v6_scientific_acceptance_gate.py"
    replace_once(
        path,
        'spec = importlib.util.spec_from_file_location("scientific_acceptance_gate_v6", SCRIPT)\nmodule = importlib.util.module_from_spec(spec)\nassert spec and spec.loader\n',
        'spec = importlib.util.spec_from_file_location("scientific_acceptance_gate_v6", SCRIPT)\nif spec is None or spec.loader is None:\n    raise RuntimeError(f"cannot load {SCRIPT}")\nmodule = importlib.util.module_from_spec(spec)\n',
    )


def repair_v5_types() -> None:
    path = ROOT / "tests/test_v5_dft_evidence_and_uncertainty.py"
    text = path.read_text(encoding="utf-8")
    text = text.replace("  # type: ignore[index]", "")
    if "from typing import Protocol, cast\n" not in text:
        text = text.replace(
            "from pathlib import Path\n",
            "from pathlib import Path\nfrom typing import Protocol, cast\n",
            1,
        )

    simple_replacements = {
        '    leakage = _labels(); leakage[1]["parent_id"] = "p1"': (
            '    leakage = _labels()\n    leakage[1]["parent_id"] = "p1"'
        ),
        '    mixed = _labels(); mixed[1]["method_fingerprint"] = "4" * 64': (
            '    mixed = _labels()\n    mixed[1]["method_fingerprint"] = "4" * 64'
        ),
        '    constant = _labels(); constant[1]["value"] = -1.0': (
            '    constant = _labels()\n    constant[1]["value"] = -1.0'
        ),
        '    self_approved = _accepted_card(); self_approved["independent_approval"]["issuer"] = "trainer-a"': (
            '    self_approved = _accepted_card()\n'
            '    self_approval = self_approved["independent_approval"]\n'
            '    assert isinstance(self_approval, dict)\n'
            '    self_approval["issuer"] = "trainer-a"'
        ),
        '    wrong_hash = _accepted_card(); wrong_hash["independent_approval"]["model_sha256"] = "9" * 64': (
            '    wrong_hash = _accepted_card()\n'
            '    wrong_hash_approval = wrong_hash["independent_approval"]\n'
            '    assert isinstance(wrong_hash_approval, dict)\n'
            '    wrong_hash_approval["model_sha256"] = "9" * 64'
        ),
    }
    for old, new in simple_replacements.items():
        count = text.count(old)
        if count == 1:
            text = text.replace(old, new, 1)
        elif count == 0 and new not in text:
            raise RuntimeError(f"generated V5 pattern was not found: {old!r}")

    anchor = 'quantities = load("quantity_equivalence_v5")\n\n\n'
    protocol = '''quantities = load("quantity_equivalence_v5")


class QuantityLike(Protocol):
    quantity_kind: str
    values: object
    unit: str
    shape: tuple[int, ...]
    aggregation: str
    atom_mapping: tuple[str, ...] | None
    periodicity: str | None


'''
    if protocol not in text:
        if text.count(anchor) != 1:
            raise RuntimeError("quantity module anchor is not unique")
        text = text.replace(anchor, protocol, 1)

    force_pattern = re.compile(
        r"def force\(values: object, unit: str, mapping: tuple\[str, \.\.\.\]\) -> object:\n"
        r"    return quantities\.TypedQuantity\(\n"
        r"(?P<body>(?:        .*\n)+?)"
        r"    \)\n"
    )
    match = force_pattern.search(text)
    if match is not None:
        force_replacement = (
            "def force(values: object, unit: str, mapping: tuple[str, ...]) -> QuantityLike:\n"
            "    return cast(\n"
            "        QuantityLike,\n"
            "        quantities.TypedQuantity(\n"
            + match.group("body")
            + "        ),\n"
            "    )\n"
        )
        text = text[: match.start()] + force_replacement + text[match.end() :]
    elif "def force(values: object, unit: str, mapping: tuple[str, ...]) -> QuantityLike:" not in text:
        raise RuntimeError("generated force helper was not found")

    different_pattern = re.compile(
        r'    different_method = quantities\.TypedQuantity\(\*\*\{\*\*left\.__dict__, "method_fingerprint": "m2"\}\) if hasattr\(left, "__dict__"\) else quantities\.TypedQuantity\(\n'
        r"        quantity_kind=left\.quantity_kind, values=left\.values, unit=left\.unit, shape=left\.shape,\n"
        r"        aggregation=left\.aggregation, atom_mapping=left\.atom_mapping,\n"
        r'        method_fingerprint="m2", periodicity=left\.periodicity,\n'
        r"    \)"
    )
    different_replacement = '''    different_method = quantities.TypedQuantity(
        quantity_kind=left.quantity_kind,
        values=left.values,
        unit=left.unit,
        shape=left.shape,
        aggregation=left.aggregation,
        atom_mapping=left.atom_mapping,
        method_fingerprint="m2",
        periodicity=left.periodicity,
    )'''
    text, count = different_pattern.subn(different_replacement, text, count=1)
    if count == 0 and different_replacement not in text:
        raise RuntimeError("generated alternate-method quantity block was not found")

    _write(path, text)


def repair_parser_wrapper_types() -> None:
    for relative in (
        "skills/tsao-dft-hpc-provenance/scripts/engine_parser_v4.py",
        "skills/tsao-dft-hpc-provenance/scripts/engine_parser_contract_v4.py",
    ):
        path = ROOT / relative
        if not path.is_file():
            raise RuntimeError(f"generated parser wrapper is missing: {relative}")
        text = path.read_text(encoding="utf-8")
        text = _ensure_import(text, "from typing import Any")
        text, count = re.subn(r"->\s*ParserRecord:", "-> Any:", text)
        if count == 0 and "-> Any:" not in text:
            raise RuntimeError(f"ParserRecord return annotations were not found in {relative}")
        _write(path, text)


def repair_v18_core_types() -> None:
    path = ROOT / "skills/tsao-dft-hpc-provenance/scripts/scientific_contracts_core_v18.py"
    if not path.is_file():
        raise RuntimeError(f"generated V18 core is missing: {path}")
    text = path.read_text(encoding="utf-8")
    text = _ensure_import(text, "from typing import cast")

    lines = text.splitlines()
    patched_cast = False
    for index, line in enumerate(lines):
        if "re.fullmatch(" not in line and not (
            index > 0 and "re.fullmatch(" in lines[index - 1]
        ):
            continue
        for candidate in range(index, min(index + 4, len(lines))):
            if "values[key_name]" in lines[candidate] and "isinstance" not in lines[candidate]:
                lines[candidate] = lines[candidate].replace(
                    "values[key_name]",
                    "cast(str, values[key_name])",
                    1,
                )
                patched_cast = True
                break
        if patched_cast:
            break
    text = "\n".join(lines) + "\n"
    if not patched_cast and "cast(str, values[key_name])" not in text:
        raise RuntimeError("V18 digest fullmatch typing site was not found")

    marker = "key = key_resolver(receipt.key_id)"
    if marker in text:
        start = text.index(marker)
        end = text.find("\n\ndef ", start)
        end = len(text) if end < 0 else end
        block = text[start:end]
        block = block.replace(marker, "resolved_key = key_resolver(receipt.key_id)", 1)
        block = block.replace("if key is None:", "if resolved_key is None:", 1)
        block = block.replace("_hmac_digest(key,", "_hmac_digest(resolved_key,", 1)
        text = text[:start] + block + text[end:]
    elif "resolved_key = key_resolver(receipt.key_id)" not in text:
        raise RuntimeError("V18 key resolver typing site was not found")

    _write(path, text)


def repair_tst_adapter_type() -> None:
    path = ROOT / "skills/tsao-dft-kinetics-multiscale/scripts/tst_standard_state_v4.py"
    if not path.is_file():
        raise RuntimeError(f"generated TST adapter is missing: {path}")
    text = path.read_text(encoding="utf-8")
    target = "    return _core.eyring_rate(\n"
    replacement = (
        '    if _core is None:\n'
        '        raise RuntimeError("scientific contracts core could not be loaded")\n'
        '    return _core.eyring_rate(\n'
    )
    if target in text:
        text = text.replace(target, replacement, 1)
    elif replacement not in text:
        raise RuntimeError("TST adapter core call was not found")
    _write(path, text)


def repair_test_runners() -> None:
    coverage_path = ROOT / "scripts/run_coverage.py"
    text = coverage_path.read_text(encoding="utf-8")
    old = '''            "-m",
            "unittest",
            "discover",
            "-s",
            str(suite),
            "-p",
            "test_*.py",
            "-v",
'''
    new = '''            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            "--import-mode=importlib",
            str(suite),
'''
    if old in text:
        text = text.replace(old, new, 1)
    elif '"pytest"' not in text:
        raise RuntimeError("coverage runner unittest command was not found")
    coverage_path.write_text(text, encoding="utf-8", newline="\n")

    runner_path = ROOT / "scripts/run_all_tests.py"
    text = runner_path.read_text(encoding="utf-8")
    old = '''        "-m",
        "unittest",
        "discover",
        "-s",
        str(path),
        "-p",
        "test_*.py",
        "-v",
'''
    new = '''        "-m",
        "pytest",
        "-q",
        "-p",
        "no:cacheprovider",
        "--import-mode=importlib",
        str(path),
'''
    if old in text:
        text = text.replace(old, new, 1)
    elif '"pytest"' not in text:
        raise RuntimeError("unit runner unittest command was not found")

    if "PYTEST_COUNT_RE" not in text:
        text = text.replace(
            'TEST_COUNT_RE = re.compile(r"Ran\\s+(\\d+)\\s+tests?")\n',
            'TEST_COUNT_RE = re.compile(r"Ran\\s+(\\d+)\\s+tests?")\n'
            'PYTEST_COUNT_RE = re.compile(r"(?<!\\w)(\\d+)\\s+(passed|failed|skipped|xfailed|xpassed|errors?)\\b")\n',
            1,
        )
        old_count = '''    match = TEST_COUNT_RE.search(output)
    count = int(match.group(1)) if match else 0
    discovery_ok = match is not None and count > 0
'''
        new_count = '''    match = TEST_COUNT_RE.search(output)
    if match is not None:
        count = int(match.group(1))
    else:
        count = sum(int(value) for value, _ in PYTEST_COUNT_RE.findall(output))
    discovery_ok = count > 0
'''
        if old_count not in text:
            raise RuntimeError("unit runner count parser was not found")
        text = text.replace(old_count, new_count, 1)
        text = text.replace(
            '        reason = "test discovery reported zero tests" if match else "test count could not be parsed"\n',
            '        reason = "test discovery reported zero tests" if count == 0 else "test count could not be parsed"\n',
            1,
        )
    _write(runner_path, text)


def main() -> int:
    repair_dependency_contract()
    repair_contracts()
    repair_v6_loader()
    repair_v5_types()
    repair_parser_wrapper_types()
    repair_v18_core_types()
    repair_tst_adapter_type()
    repair_test_runners()
    print(
        {
            "repaired": [
                "dependency and pytest constraints",
                "contracts_v17 quantity typing",
                "V5/V6 generated tests",
                "V18 parser wrapper return typing",
                "V18 digest and key resolver typing",
                "V18 TST adapter optional-core typing",
                "pytest-native unit and coverage runners",
            ]
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

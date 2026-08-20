from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"expected one exact pattern in {path}, found {count}: {old!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")


def repair_contracts() -> None:
    path = ROOT / "skills/tsao-dft-hpc-provenance/scripts/contracts_v17.py"
    replace_once(
        path,
        "def validate_quantity_shape(kind: str, shape: tuple[int, ...], *, atom_count: int | None = None) -> None:\n    if kind == \"scalar\":",
        "def validate_quantity_shape(kind: str, shape: tuple[int, ...], *, atom_count: int | None = None) -> None:\n    expected: tuple[int, ...]\n    if kind == \"scalar\":",
    )


def repair_v6_loader() -> None:
    path = ROOT / "tests/test_v6_scientific_acceptance_gate.py"
    replace_once(
        path,
        "spec = importlib.util.spec_from_file_location(\"scientific_acceptance_gate_v6\", SCRIPT)\nmodule = importlib.util.module_from_spec(spec)\nassert spec and spec.loader\n",
        "spec = importlib.util.spec_from_file_location(\"scientific_acceptance_gate_v6\", SCRIPT)\nif spec is None or spec.loader is None:\n    raise RuntimeError(f\"cannot load {SCRIPT}\")\nmodule = importlib.util.module_from_spec(spec)\n",
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
        if count != 1:
            raise RuntimeError(f"expected one generated V5 pattern, found {count}: {old!r}")
        text = text.replace(old, new, 1)

    anchor = 'quantities = load("quantity_equivalence_v5")\n\n\n'
    protocol = '''quantities = load("quantity_equivalence_v5")\n\n\nclass QuantityLike(Protocol):\n    quantity_kind: str\n    values: object\n    unit: str\n    shape: tuple[int, ...]\n    aggregation: str\n    atom_mapping: tuple[str, ...] | None\n    periodicity: str | None\n\n\n'''
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
    if match is None:
        raise RuntimeError("generated force helper was not found")
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

    different_pattern = re.compile(
        r"    different_method = quantities\.TypedQuantity\(\*\*\{\*\*left\.__dict__, \"method_fingerprint\": \"m2\"\}\) if hasattr\(left, \"__dict__\"\) else quantities\.TypedQuantity\(\n"
        r"        quantity_kind=left\.quantity_kind, values=left\.values, unit=left\.unit, shape=left\.shape,\n"
        r"        aggregation=left\.aggregation, atom_mapping=left\.atom_mapping,\n"
        r"        method_fingerprint=\"m2\", periodicity=left\.periodicity,\n"
        r"    \)"
    )
    different_replacement = '''    different_method = quantities.TypedQuantity(\n        quantity_kind=left.quantity_kind,\n        values=left.values,\n        unit=left.unit,\n        shape=left.shape,\n        aggregation=left.aggregation,\n        atom_mapping=left.atom_mapping,\n        method_fingerprint="m2",\n        periodicity=left.periodicity,\n    )'''
    text, count = different_pattern.subn(different_replacement, text, count=1)
    if count != 1:
        raise RuntimeError("generated alternate-method quantity block was not found")

    compile(text, path.as_posix(), "exec")
    path.write_text(text, encoding="utf-8", newline="\n")


def main() -> int:
    repair_contracts()
    repair_v6_loader()
    repair_v5_types()
    print(
        {
            "repaired": [
                "skills/tsao-dft-hpc-provenance/scripts/contracts_v17.py",
                "tests/test_v5_dft_evidence_and_uncertainty.py",
                "tests/test_v6_scientific_acceptance_gate.py",
            ]
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

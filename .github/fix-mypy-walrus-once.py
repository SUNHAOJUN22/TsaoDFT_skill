#!/usr/bin/env python3
from pathlib import Path

path = Path(__file__).resolve().parents[1] / "skills/tsao-dft-ml-active-learning/scripts/validate_dft_dataset.py"
text = path.read_text(encoding="utf-8")
replacements = {
    "{value for row in rows if (value := row.get(fingerprint))}": "{fingerprint_value for row in rows if (fingerprint_value := row.get(fingerprint))}",
    "{value for row in rows if (value := row.get(fidelity))}": "{fidelity_value for row in rows if (fidelity_value := row.get(fidelity))}",
}
for old, new in replacements.items():
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"expected one occurrence, found {count}: {old!r}")
    text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
print("Separated mypy walrus variable scopes.")

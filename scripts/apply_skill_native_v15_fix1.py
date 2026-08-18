from pathlib import Path

root = Path(__file__).resolve().parents[1]
target = root / "tests/test_scientific_contracts_v15.py"
target.write_text('''from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

MODULE_PATH = Path(__file__).resolve().parents[1] / "skills/tsao-dft-hpc-provenance/scripts/scientific_contracts_v15.py"
SPEC = importlib.util.spec_from_file_location("dft_v15", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class Tests(unittest.TestCase):
    def test_fatal_overrides_success(self) -> None:
        self.assertEqual(MODULE.final_parse_status(["SUCCESS", "FATAL"], expected_terminal_seen=True).status, "FATAL")

    def test_missing_terminal_is_truncated(self) -> None:
        self.assertEqual(MODULE.final_parse_status(["SUCCESS"], expected_terminal_seen=False).status, "TRUNCATED")

    def test_force_shape(self) -> None:
        quantity = MODULE.Quantity((1.0, 2.0, 3.0, 4.0, 5.0, 6.0), (2, 3), "eV/A", "force")
        quantity.validate()
        with self.assertRaises(ValueError):
            MODULE.Quantity((1.0, 2.0), (2,), "eV/A", "force").validate()

    def test_bimolecular_tst_has_inverse_concentration_factor(self) -> None:
        unimolecular = MODULE.tst_rate_constant(temperature_k=298.15, delta_g_j_per_mol=50000.0, molecularity=1)
        bimolecular = MODULE.tst_rate_constant(temperature_k=298.15, delta_g_j_per_mol=50000.0, molecularity=2)
        self.assertAlmostEqual(bimolecular, unimolecular / 1000.0)

    def test_trainer_cannot_self_accept(self) -> None:
        self.assertEqual(
            MODULE.model_acceptance(
                dataset_hash=True,
                model_hash=True,
                code_hash=True,
                environment_hash=True,
                applicability_domain=True,
                calibrated_uncertainty=True,
                holdout_validation=True,
                independent_approval=False,
            ),
            "HOLD",
        )


if __name__ == "__main__":
    unittest.main()
''', encoding="utf-8", newline="\n")
print("fixed dynamic import registration")

"""Physical conservation is independent of a reaction's coefficient normalization."""

from __future__ import annotations

import copy
import importlib.util
import math
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_script(filename):
    spec = importlib.util.spec_from_file_location(filename.removesuffix(".py"), ROOT / "scripts" / filename)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BalanceScaleInvarianceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.network = load_script("validate_reaction_network.py")
        cls.closure = load_script("check_thermodynamic_closure.py")
        cls.base = yaml.safe_load((ROOT / "examples/catalysis/network.yaml").read_text(encoding="utf-8"))

    def scaled_network(self, scale):
        data = copy.deepcopy(self.base)
        for reaction in data["reactions"]:
            for side in ("reactants", "products"):
                reaction[side] = {key: value * scale for key, value in reaction[side].items()}
        return data

    def test_atom_conservation_is_scale_invariant(self):
        for scale in (math.ulp(0.0), 1e-200, 1.0, 1e200, 1e308):
            with self.subTest(scale=scale):
                data = self.scaled_network(scale)
                self.assertEqual(self.network.validate(data)[0], [])
                data["species"][1]["composition"]["H"] = 3
                self.assertIn("violates element balance", " ".join(self.network.validate(data)[0]))

    def test_charge_and_site_conservation_are_scale_invariant(self):
        for key, label in (("charge", "charge"), ("site_occupancy", "site")):
            for scale in (1e-200, 1.0, 1e308):
                with self.subTest(key=key, scale=scale):
                    data = self.scaled_network(scale)
                    data["species"][0][key] = 2
                    data["species"][1][key] = 1
                    self.assertIn(f"violates {label} balance", " ".join(self.network.validate(data)[0]))

    def test_trace_element_is_not_erased_by_unrelated_large_coefficients(self):
        data = self.scaled_network(1e308)
        trace = copy.deepcopy(data["species"][0])
        trace.update(id="TRACE", composition={"He": 1})
        data["species"].append(trace)
        data["reactions"][0]["reactants"]["TRACE"] = math.ulp(0.0)
        errors, _ = self.network.validate(data)
        self.assertIn("He", " ".join(errors))

    def test_roundoff_tolerance_remains_relative(self):
        data = self.scaled_network(1e308)
        data["species"][1]["composition"]["H"] = 4 * (1 + 1e-12)
        self.assertEqual(self.network.validate(data)[0], [])

    def test_unrepresentable_input_integer_fails_as_validation_error(self):
        data = copy.deepcopy(self.base)
        data["temperature_K"] = 10**400
        errors, _ = self.network.validate(data)
        self.assertIn("temperature_K must be finite numeric", errors)

    def test_negative_atom_counts_are_not_a_valid_balanced_network(self):
        data = copy.deepcopy(self.base)
        for species in data["species"]:
            species["composition"] = {element: -amount for element, amount in species["composition"].items()}
        errors, _ = self.network.validate(data)
        self.assertIn("composition.H must be non-negative", " ".join(errors))

    def test_negative_site_occupancy_is_rejected_in_scalar_and_mapping_forms(self):
        for occupancy in (-1, {"surface": -1}):
            with self.subTest(occupancy=occupancy):
                data = copy.deepcopy(self.base)
                for species in data["species"]:
                    species["site_occupancy"] = occupancy
                errors, _ = self.network.validate(data)
                self.assertIn("must be non-negative", " ".join(errors))

    def test_signed_charge_remains_supported(self):
        data = copy.deepcopy(self.base)
        for species in data["species"]:
            species["charge"] = -1
        self.assertEqual(self.network.validate(data)[0], [])

    def test_overflow_in_derived_reverse_barrier_is_structured_failure(self):
        data = copy.deepcopy(self.base)
        data["reactions"][0].update(forward_barrier=1e308, reaction_free_energy=-1e308)
        report = self.closure.analyze(data, 0.05)
        self.assertFalse(report["ok"])
        self.assertIn("reverse barrier exceeds", " ".join(report["errors"]))
        self.assertEqual(report["reactions"], [])

    def test_overflow_in_closure_residual_is_structured_failure(self):
        data = copy.deepcopy(self.base)
        data["reactions"][0].update(forward_barrier=1e308, reaction_free_energy=0, reverse_barrier=-1e308)
        report = self.closure.analyze(data, 0.05)
        self.assertFalse(report["ok"])
        self.assertIn("closure error exceeds", " ".join(report["errors"]))
        self.assertEqual(report["reactions"], [])


if __name__ == "__main__":
    unittest.main()

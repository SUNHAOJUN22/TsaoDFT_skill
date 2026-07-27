from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

import numpy as np

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "train_ridge_baseline.py"


def load_module():
    spec = importlib.util.spec_from_file_location("tsao_ridge", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RidgeSolverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def test_primal_and_dual_predictions_match(self):
        rng = np.random.default_rng(17)
        matrix = rng.normal(size=(24, 40))
        matrix -= matrix.mean(axis=0)
        target = rng.normal(size=24)
        primal = self.module.fit_ridge(matrix, target, 0.75, "primal")
        dual = self.module.fit_ridge(matrix, target, 0.75, "dual")
        primal_prediction = primal[0] + matrix @ primal[1]
        dual_prediction = dual[0] + matrix @ dual[1]
        np.testing.assert_allclose(primal_prediction, dual_prediction, rtol=1e-10, atol=1e-10)

    def test_auto_uses_dual_for_wide_matrix(self):
        matrix = np.arange(60.0).reshape(6, 10)
        target = np.arange(6.0)
        _, _, solver, dimension = self.module.fit_ridge(matrix, target, 1.0, "auto")
        self.assertEqual(solver, "dual")
        self.assertEqual(dimension, 6)

    def test_auto_uses_primal_for_tall_matrix(self):
        matrix = np.arange(60.0).reshape(10, 6)
        target = np.arange(10.0)
        _, _, solver, dimension = self.module.fit_ridge(matrix, target, 1.0, "auto")
        self.assertEqual(solver, "primal")
        self.assertEqual(dimension, 6)

    def test_zero_alpha_uses_stable_least_squares(self):
        matrix = np.array([[1.0, 1.0], [2.0, 2.0], [3.0, 3.0], [4.0, 4.0]])
        target = np.array([1.0, 2.0, 3.0, 4.0])
        intercept, coefficients, solver, dimension = self.module.fit_ridge(matrix, target, 0.0, "auto")
        prediction = intercept + matrix @ coefficients
        np.testing.assert_allclose(prediction, target, rtol=1e-12, atol=1e-12)
        self.assertEqual(solver, "lstsq")
        self.assertEqual(dimension, 3)

    def test_negative_alpha_is_rejected(self):
        matrix = np.eye(3)
        target = np.arange(3.0)
        with self.assertRaisesRegex(ValueError, "non-negative"):
            self.module.fit_ridge(matrix, target, -0.1, "auto")

    def test_non_finite_values_are_rejected(self):
        matrix = np.array([[1.0, np.nan], [2.0, 3.0]])
        target = np.array([1.0, 2.0])
        with self.assertRaisesRegex(ValueError, "finite values"):
            self.module.fit_ridge(matrix, target, 1.0, "auto")


if __name__ == "__main__":
    unittest.main()

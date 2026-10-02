"""Scale-aware reference checks for the public ridge baseline metrics."""

import contextlib
import importlib.util
import io
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

_PATH = Path(__file__).resolve().parents[1] / "skills/tsao-dft-ml-active-learning/scripts/train_ridge_baseline.py"
_SPEC = importlib.util.spec_from_file_location("ridge_metric_range", _PATH)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)


class RidgeMetricRangeTests(unittest.TestCase):
    def test_metrics_are_scale_covariant_and_r_squared_is_invariant(self):
        for scale in (1e-200, 1.0, 1e200):
            with self.subTest(scale=scale):
                result = _MODULE.metrics([scale, 2 * scale], [2 * scale, 4 * scale])
                self.assertAlmostEqual(result["mae"] / scale, 1.5)
                self.assertAlmostEqual(result["rmse"] / scale, math.sqrt(2.5))
                self.assertAlmostEqual(result["r2"], -9)

    def test_constant_target_keeps_undefined_r_squared_explicit(self):
        self.assertEqual(_MODULE.metrics([1e308, 1e308], [1e308, 1e308]), {"mae": 0, "rmse": 0, "r2": None})

    def test_unrepresentable_metrics_fail_instead_of_emitting_nonfinite_json(self):
        with self.assertRaisesRegex(ValueError, "metric results"):
            _MODULE.metrics([-1e308], [1e308])

    def test_failed_metric_validation_does_not_publish_prediction_files(self):
        rows = [{"x": str(i), "y": str(i * 2), "group": str(i)} for i in range(20)]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "not-published"
            argv = [
                "ridge",
                "unused.csv",
                "--features",
                "x",
                "--target",
                "y",
                "--group",
                "group",
                "--out-dir",
                str(output),
            ]
            stream = io.StringIO()
            with (
                mock.patch.object(sys, "argv", argv),
                mock.patch.object(_MODULE, "read", return_value=rows),
                mock.patch.object(_MODULE, "metrics", side_effect=ValueError("metric results exceed range")),
                contextlib.redirect_stdout(stream),
            ):
                self.assertEqual(_MODULE.main(), 1)
            self.assertFalse(output.exists())
            self.assertFalse(json.loads(stream.getvalue())["ok"])

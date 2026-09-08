from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


def load_neighbor():
    path = Path(__file__).resolve().parents[1] / "scripts/neighbor_list.py"
    spec = importlib.util.spec_from_file_location("neighbor_range_regression", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("value", [1e200, 1e308])
def test_extreme_coordinates_and_cutoffs_are_rejected(value: float) -> None:
    neighbor = load_neighbor()
    with pytest.raises(ValueError, match="safe squared-distance"):
        neighbor._coordinates([[0.0, 0.0, 0.0], [value, 0.0, 0.0]])
    with pytest.raises(ValueError, match="safe squared-distance"):
        neighbor._cutoff(value)

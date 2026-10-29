"""Whole geometry tasks retain exact nearest distances without repeated setup."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import numpy as np
import pytest

SCRIPTS = Path(__file__).parents[1] / "scripts"


def load_script(filename: str) -> Any:
    spec = importlib.util.spec_from_file_location(f"prepared_task_{filename[:-3]}", SCRIPTS / filename)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def atoms_for(points: np.ndarray) -> list[dict[str, Any]]:
    return [
        {"index": i + 1, "element": "C", "x": float(p[0]), "y": float(p[1]), "z": float(p[2])}
        for i, p in enumerate(points)
    ]


@pytest.mark.parametrize("backend", ["numpy", "cell-list"])
@pytest.mark.parametrize("periodic", [(True, True, True), (True, True, False), (False, True, False)])
def test_adaptive_nearest_reuses_cell_for_bound_sampling(backend, periodic):
    neighbors = load_script("neighbor_list.py")
    box = np.asarray([[8.0, 0.0, 0.0], [1.7, 7.2, 0.0], [0.5, 0.8, 6.9]])
    points = np.random.default_rng(2009).uniform(0, 1, (18, 3)) @ box
    original_box = box.copy()
    reference = neighbors.reference_pairs(points, 100.0, box=box, periodic=periodic)
    expected = min(pair.distance_angstrom for pair in reference.pairs)
    with (
        patch.object(np.linalg, "svd", wraps=np.linalg.svd) as svd,
        patch.object(np.linalg, "lstsq", wraps=np.linalg.lstsq) as lstsq,
    ):
        actual = neighbors.nearest_pair_distance(points, box=box, periodic=periodic, backend=backend)
    np.testing.assert_allclose(actual, expected, rtol=2e-14, atol=2e-14)
    np.testing.assert_array_equal(box, original_box)
    # One preparation for sampled bounds and one for the public cutoff search.
    # The number of sampled pairs cannot increase either decomposition count.
    assert svd.call_count == 2
    assert lstsq.call_count == 2


@pytest.mark.parametrize("periodic", [False, (True, False, True), True])
def test_nonempty_cutoff_is_sufficient_for_global_minimum(periodic):
    geometry = load_script("inspect_xyz.py")
    box = np.asarray([[8.0, 0.0, 0.0], [1.7, 7.2, 0.0], [0.5, 0.8, 6.9]])
    points = np.random.default_rng(2010).uniform(0, 1, (18, 3)) @ box
    atoms = atoms_for(points)
    reference = geometry._NEIGHBORS.reference_pairs(points, 100.0, box=box, periodic=periodic)
    expected = min(pair.distance_angstrom for pair in reference.pairs)
    with patch.object(geometry._NEIGHBORS, "nearest_pair_distance", side_effect=AssertionError("redundant search")):
        report = geometry.inspect(atoms, backend="cell-list", box=box, periodic=periodic)
    np.testing.assert_allclose(report["minimum_pair_distance_angstrom"], expected, rtol=2e-14, atol=2e-14)
    assert report["atom_count"] == len(points)


@pytest.mark.parametrize("periodic", [False, (True, True, False), True])
def test_empty_cutoff_keeps_adaptive_global_search(periodic):
    geometry = load_script("inspect_xyz.py")
    box = np.asarray([[40.0, 0.0, 0.0], [3.0, 40.0, 0.0], [0.0, 0.0, 40.0]])
    points = np.asarray([[0.0, 0.0, 0.0], [10.0, 0.0, 0.0], [0.0, 12.0, 0.0]])
    with patch.object(
        geometry._NEIGHBORS, "nearest_pair_distance", wraps=geometry._NEIGHBORS.nearest_pair_distance
    ) as nearest:
        report = geometry.inspect(atoms_for(points), backend="cell-list", box=box, periodic=periodic)
    assert report["heuristic_bonds"] == []
    assert report["minimum_pair_distance_angstrom"] == 10.0
    assert nearest.call_count == 1


def test_duplicate_zero_and_changed_cells_preserve_exact_minimum():
    neighbors = load_script("neighbor_list.py")
    points = np.asarray([[0.0, 0.0, 0.0], [0.9, 0.8, 0.0], [0.5, 0.0, 0.0]])
    box = np.asarray([[1.0, 0.0, 0.0], [0.2, 1.0, 0.0], [0.0, 0.0, 1.0]])
    for shear in (0.2, 0.8, -0.4):
        box[1, 0] = shear
        reference = neighbors.reference_pairs(points, 2.0, box=box, periodic=(True, True, False))
        expected = min(pair.distance_angstrom for pair in reference.pairs)
        actual = neighbors.nearest_pair_distance(points, box=box, periodic=(True, True, False))
        np.testing.assert_allclose(actual, expected, rtol=0, atol=2e-14)
    duplicate = np.vstack([points, points[0]])
    assert neighbors.nearest_pair_distance(duplicate, box=box, periodic=True) == 0.0

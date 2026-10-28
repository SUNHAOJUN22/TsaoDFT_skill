"""Prepared geometry must remove repeated decompositions, not weaken the reference."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import numpy as np
import pytest

SPEC = importlib.util.spec_from_file_location(
    "periodic_context_reuse", Path(__file__).parents[1] / "scripts/neighbor_list.py"
)
assert SPEC is not None and SPEC.loader is not None
neighbors: Any = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = neighbors
SPEC.loader.exec_module(neighbors)


@pytest.mark.parametrize("backend", ["numpy", "cell-list"])
@pytest.mark.parametrize("periodic", [(True, True, True), (True, True, False), (False, True, False)])
def test_fixed_cell_decomposed_once_and_matches_unprepared_reference(backend, periodic):
    box = np.asarray([[3.0, 0.0, 0.0], [0.7, 2.8, 0.0], [0.1, 0.3, 3.1]])
    points = np.random.default_rng(918).uniform(0, 1, (12, 3)) @ box
    original_box = box.copy()
    expected = neighbors.reference_pairs(points, 1.7, box=box, periodic=periodic)
    with (
        patch.object(np.linalg, "svd", wraps=np.linalg.svd) as svd,
        patch.object(np.linalg, "lstsq", wraps=np.linalg.lstsq) as lstsq,
    ):
        actual = neighbors.pairs_within_cutoff(points, 1.7, box=box, periodic=periodic, backend=backend)
    assert [(p.i, p.j) for p in actual.pairs] == [(p.i, p.j) for p in expected.pairs]
    np.testing.assert_allclose(
        [p.distance_angstrom for p in actual.pairs],
        [p.distance_angstrom for p in expected.pairs],
        rtol=2e-14,
        atol=2e-14,
    )
    np.testing.assert_array_equal(box, original_box)
    assert svd.call_count == 1
    assert lstsq.call_count == 1


@pytest.mark.parametrize("backend", ["numpy", "cell-list"])
def test_nonperiodic_and_axis_aligned_boxes_need_no_decomposition(backend):
    points = np.random.default_rng(12).uniform(0, 1, (10, 3))
    with (
        patch.object(np.linalg, "svd", wraps=np.linalg.svd) as svd,
        patch.object(np.linalg, "lstsq", wraps=np.linalg.lstsq) as lstsq,
    ):
        neighbors.pairs_within_cutoff(points, 0.5, backend=backend)
        neighbors.pairs_within_cutoff(points, 0.5, box=np.diag([2.0, 2.0, 2.0]), periodic=True, backend=backend)
    assert svd.call_count == 0
    assert lstsq.call_count == 0


@pytest.mark.parametrize("backend", ["numpy", "cell-list"])
def test_context_is_request_scoped_when_caller_changes_box(backend):
    points = [[0.0, 0.0, 0.0], [0.9, 0.8, 0.0]]
    box = np.asarray([[1.0, 0.0, 0.0], [0.2, 1.0, 0.0], [0.0, 0.0, 1.0]])
    for shear in (0.2, 0.8, -0.4):
        box[1, 0] = shear
        expected = neighbors.reference_pairs(points, 0.5, box=box, periodic=True)
        actual = neighbors.pairs_within_cutoff(points, 0.5, box=box, periodic=True, backend=backend)
        assert actual.pairs == expected.pairs

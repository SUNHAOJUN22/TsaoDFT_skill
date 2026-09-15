from __future__ import annotations

import importlib.util
import itertools
import sys
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "neighbor_list.py"


def load_neighbors() -> Any:
    spec = importlib.util.spec_from_file_location("anisotropic_neighbor_regression", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def brute_periodic_distance(
    delta: np.ndarray,
    box: np.ndarray,
    periodic_axes: tuple[int, ...],
) -> float:
    distances: list[float] = []
    for values in itertools.product(range(-2, 3), repeat=len(periodic_axes)):
        shift = np.zeros(3, dtype=float)
        for axis, value in zip(periodic_axes, values, strict=True):
            shift[axis] = value
        distances.append(float(np.linalg.norm(delta - shift @ box)))
    return min(distances)


def test_anisotropic_skew_is_not_misclassified_as_orthogonal() -> None:
    neighbors = load_neighbors()
    skewed = np.asarray(
        [
            [1.0, 0.0, 0.0],
            [0.9, 1.0, 0.0],
            [0.0, 0.0, 100_000_000.0],
        ]
    )
    orthogonal = np.diag([1.0, 2.0, 100_000_000.0])

    assert neighbors._orthogonal_box(orthogonal)
    assert not neighbors._orthogonal_box(skewed)


def test_anisotropic_skew_matches_independent_lattice_enumeration() -> None:
    neighbors = load_neighbors()
    box = np.asarray(
        [
            [1.0, 0.0, 0.0],
            [0.9, 1.0, 0.0],
            [0.0, 0.0, 100_000_000.0],
        ]
    )
    coordinates = np.asarray(
        [
            [0.0, 0.0, 0.0],
            [0.931, 0.49, 0.0],
        ]
    )
    periodic = (True, True, False)
    delta = coordinates[1] - coordinates[0]
    expected = brute_periodic_distance(delta, box, (0, 1))

    np.testing.assert_allclose(expected, 0.49483431570577235, rtol=0, atol=1e-14)

    for backend in ("reference", "numpy", "cell-list"):
        result = neighbors.pairs_within_cutoff(
            coordinates,
            0.6,
            box=box,
            periodic=periodic,
            backend=backend,
        )
        assert [(pair.i, pair.j) for pair in result.pairs] == [(0, 1)]
        np.testing.assert_allclose(
            result.pairs[0].distance_angstrom,
            expected,
            rtol=0,
            atol=1e-12,
        )

    nearest = neighbors.nearest_pair_distance(
        coordinates,
        box=box,
        periodic=periodic,
        backend="cell-list",
    )
    np.testing.assert_allclose(nearest, expected, rtol=0, atol=1e-12)


def test_orthogonality_decision_is_scale_invariant() -> None:
    neighbors = load_neighbors()
    base = np.asarray(
        [
            [1.0, 0.0, 0.0],
            [0.25, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ]
    )
    for scales in (
        np.asarray([1.0, 1.0, 1.0]),
        np.asarray([1e-8, 1.0, 1e8]),
        np.asarray([1e8, 1e-8, 1.0]),
    ):
        scaled = base * scales[:, None]
        assert not neighbors._orthogonal_box(scaled)

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

import numpy as np

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/preflight_vasp.py"
SPEC = importlib.util.spec_from_file_location("poscar_geometry_preflight", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
VASP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VASP)


def poscar(scale: str = "1", edge: str = "1", comment: str = "geometry", position: str = "0.5 0.25 0.75") -> str:
    return f"{comment}\n{scale}\n{edge} 0 0\n0 {edge} 0\n0 0 {edge}\nH\n1\nDirect\n{position}\n"


class PoscarGeometryContractTests(unittest.TestCase):
    def parse(self, content: str) -> dict:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "POSCAR"
            path.write_text(content, encoding="utf-8")
            return VASP.parse_poscar(path)

    def test_equivalent_unit_cells_do_not_depend_on_raw_length_scale(self):
        # All three records describe exactly the identity cell in Angstrom.
        for scale, edge in [("1", "1"), ("1e-200", "1e200"), ("-1", "1e-200")]:
            with self.subTest(scale=scale, edge=edge):
                result = self.parse(poscar(scale=scale, edge=edge))
                np.testing.assert_allclose(result["lattice_vectors"], np.eye(3), rtol=1e-12, atol=0)
                self.assertAlmostEqual(result["cell_volume_angstrom3"], 1.0, places=12)

    def test_component_scales_can_compensate_anisotropic_raw_vectors(self):
        content = poscar(scale="1e10 1e-10 1").replace("1 0 0\n0 1 0\n0 0 1", "1e-10 0 0\n0 1e10 0\n0 0 1")
        result = self.parse(content)
        np.testing.assert_allclose(result["lattice_vectors"], np.eye(3), rtol=1e-14, atol=0)
        self.assertAlmostEqual(result["cell_volume_angstrom3"], 1.0)

    def test_numerically_parallel_directions_remain_rejected(self):
        content = poscar().replace("1 0 0\n0 1 0\n0 0 1", "1 0 0\n1 1e-16 0\n0 0 1")
        with self.assertRaisesRegex(ValueError, "nonsingular"):
            self.parse(content)

    def test_component_scaling_validates_the_transformed_skew_cell(self):
        content = poscar(scale="1 1e16 1").replace("1 0 0\n0 1 0\n0 0 1", "1 1e-16 0\n1 0 0\n0 0 1")
        result = self.parse(content)
        self.assertEqual(result["lattice_vectors"], [[1, 1, 0], [1, 0, 0], [0, 0, 1]])
        self.assertAlmostEqual(result["cell_volume_angstrom3"], 1.0)

    def test_blank_comment_preserves_fixed_record_positions(self):
        result = self.parse(poscar(comment=""))
        self.assertEqual(result["comment"], "")
        self.assertEqual(result["atom_count"], 1)

    def test_direct_coordinate_overflow_fails_public_preflight(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / "INCAR").write_text("ENCUT=500\n", encoding="utf-8")
            (directory / "POSCAR").write_text(poscar(scale="10", position="1e308 0 0"), encoding="utf-8")
            result = VASP.validate(directory)
            self.assertFalse(result["ok"])
            self.assertEqual(result["scientific_acceptance"], "PENDING")
            self.assertTrue(any("direct coordinate row" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()

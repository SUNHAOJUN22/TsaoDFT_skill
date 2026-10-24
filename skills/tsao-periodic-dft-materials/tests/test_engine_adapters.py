import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EX = ROOT / "examples/engine-adapters"


class EngineAdapterTests(unittest.TestCase):
    def run_json(self, script, *args, expected=0):
        r = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / script), *map(str, args)], capture_output=True, text=True
        )
        self.assertEqual(r.returncode, expected, r.stdout + r.stderr)
        return json.loads(r.stdout)

    def run_poscar_preflight(self, poscar_text, expected=0):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            (run_dir / "POSCAR").write_text(poscar_text, encoding="utf-8")
            (run_dir / "INCAR").write_text("ENCUT = 400\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "preflight_vasp.py"), str(run_dir)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
            return json.loads(result.stdout)

    def test_vasp_preflight_and_parse(self):
        d = self.run_json("preflight_vasp.py", EX / "vasp")
        self.assertEqual(d["poscar"]["atom_count"], 2)
        self.assertEqual(d["poscar"]["lattice_vectors"], d["poscar"]["raw_lattice_vectors"])
        self.assertAlmostEqual(d["poscar"]["cell_volume_angstrom3"], 40.02575175)
        d = self.run_json("parse_vasp.py", EX / "vasp/OUTCAR")
        self.assertTrue(d["electronic_converged"])
        self.assertAlmostEqual(d["last_toten_eV"], -10.123456)

    def test_poscar_positive_scale_is_applied_to_reported_cell(self):
        report = self.run_poscar_preflight("scaled cell\n2.0\n1 0 0\n0 1 0\n0 0 1\nSi\n1\nDirect\n0 0 0\n")
        poscar = report["poscar"]
        self.assertEqual(poscar["raw_lattice_vectors"], [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
        self.assertEqual(poscar["lattice_vectors"], [[2.0, 0.0, 0.0], [0.0, 2.0, 0.0], [0.0, 0.0, 2.0]])
        self.assertAlmostEqual(poscar["cell_volume_angstrom3"], 8.0)
        self.assertEqual(poscar["effective_scale_factors"], [2.0, 2.0, 2.0])

    def test_poscar_negative_scale_is_interpreted_as_target_volume(self):
        report = self.run_poscar_preflight("target-volume cell\n-64.0\n1 0 0\n0 2 0\n0 0 4\nSi\n1\nDirect\n0 0 0\n")
        poscar = report["poscar"]
        self.assertEqual(poscar["scale"], -64.0)
        self.assertEqual(poscar["effective_scale_factors"], [2.0, 2.0, 2.0])
        self.assertEqual(poscar["lattice_vectors"], [[2.0, 0.0, 0.0], [0.0, 4.0, 0.0], [0.0, 0.0, 8.0]])
        self.assertAlmostEqual(poscar["cell_volume_angstrom3"], 64.0)

    def test_poscar_three_cartesian_scale_factors_and_k_mode(self):
        report = self.run_poscar_preflight(
            "component-scale cell\n2 3 4\n1 0 0\n0.5 1 0\n0 0 1\nSi\n1\nK-point\n0.25 0.5 0.75\n"
        )
        poscar = report["poscar"]
        self.assertEqual(poscar["coordinate_mode"], "cartesian")
        self.assertIsNone(poscar["scale"])
        self.assertEqual(poscar["lattice_vectors"], [[2.0, 0.0, 0.0], [1.0, 3.0, 0.0], [0.0, 0.0, 4.0]])
        self.assertAlmostEqual(poscar["cell_volume_angstrom3"], 24.0)

    def test_poscar_rejects_singular_cells_and_nonfinite_coordinates(self):
        cases = (
            "singular cell\n1\n1 0 0\n2 0 0\n0 0 1\nSi\n1\nDirect\n0 0 0\n",
            "nonfinite coordinates\n1\n1 0 0\n0 1 0\n0 0 1\nSi\n1\nDirect\nNaN 0 0\n",
            "zero scale\n0\n1 0 0\n0 1 0\n0 0 1\nSi\n1\nDirect\n0 0 0\n",
        )
        for poscar in cases:
            with self.subTest(poscar=poscar.splitlines()[0]):
                report = self.run_poscar_preflight(poscar, expected=1)
                self.assertFalse(report["ok"])
                self.assertTrue(any(error.startswith("POSCAR:") for error in report["errors"]))

    def test_qe_preflight_and_parse(self):
        d = self.run_json("preflight_qe.py", EX / "qe/si.in")
        self.assertEqual(len(d["parsed"]["species"]), 1)
        d = self.run_json("parse_qe.py", EX / "qe/si.out")
        self.assertTrue(d["scf_converged"])
        self.assertIsNotNone(d["last_total_energy_eV"])

    def test_cp2k_preflight_and_parse(self):
        d = self.run_json("preflight_cp2k.py", EX / "cp2k/si.inp")
        self.assertEqual(d["parsed"]["run_type"], "ENERGY")
        d = self.run_json("parse_cp2k.py", EX / "cp2k/si.out")
        self.assertTrue(d["scf_converged"])
        self.assertAlmostEqual(d["last_total_energy_hartree"], -7.5)

    def test_convergence(self):
        d = self.run_json(
            "analyze_convergence.py", EX / "convergence-results.csv", "--absolute-threshold", "0.002", "--tail", "2"
        )
        self.assertTrue(d["converged_candidate"])


if __name__ == "__main__":
    unittest.main()

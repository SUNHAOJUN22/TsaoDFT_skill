from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str) -> Any:
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(f"release_{name.replace('.', '_')}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ReleaseParserBridgeCoverageTests(unittest.TestCase):
    parser: Any
    bridge: Any

    @classmethod
    def setUpClass(cls) -> None:
        cls.parser = load_script("engine_parser_contract.py")
        cls.bridge = load_script("benchmark_bridge.py")

    def parser_file(self, text: str, name: str = "out.log") -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temporary = tempfile.TemporaryDirectory()
        path = Path(temporary.name) / name
        path.write_bytes(text.encode("utf-8"))
        return temporary, path

    def test_gaussian_all_acceptance_routes(self) -> None:
        cases = [
            (
                "#p pbe/6-31g\nSCF Done: E(RPBE) = -1.0\nNormal termination of Gaussian\n",
                True,
                None,
            ),
            ("#p pbe/6-31g\nSCF Done: E(RPBE) = -1.0\n", False, "termination"),
            (
                "#p pbe/6-31g opt\nSCF Done: E(RPBE) = -1.0\nNormal termination of Gaussian\n",
                False,
                "geometry",
            ),
            (
                "#p pbe/6-31g opt freq\nSCF Done: E(RPBE) = -1.0\nOptimization completed\n"
                "Frequencies -- -100 -50 20\nNormal termination of Gaussian\n",
                False,
                "scientific-gate",
            ),
            (
                "#p pbe/6-31g opt freq\nSCF Done: E(RPBE) = -1.0\nOptimization completed\n"
                "Frequencies -- -100 20 30\nNormal termination of Gaussian\n",
                True,
                None,
            ),
        ]
        for text, accepted, stage in cases:
            temporary, path = self.parser_file(text)
            with temporary:
                result = self.parser.parse_gaussian(path)
                self.assertEqual(result["parser_accepted"], accepted)
                self.assertEqual(result["failed_stage"], stage)

        temporary, path = self.parser_file(
            "Entering Link 1\n#p pbe/6-31g\nSCF Done: E(RPBE) = -1.0\nNormal termination of Gaussian\n"
            "Entering Link 1\n#p pbe/6-31g\nSCF Done: E(RPBE) = -2.0\nNormal termination of Gaussian\n"
        )
        with temporary:
            result = self.parser.parse_gaussian(path)
            self.assertTrue(result["warnings"])
            self.assertAlmostEqual(result["energy"]["value"], -54.422772491976)

        temporary, path = self.parser_file("Error termination\n")
        with temporary:
            result = self.parser.parse_gaussian(path)
            self.assertTrue(result["fatal_marker"])
            self.assertFalse(result["parser_accepted"])

    def test_vasp_all_acceptance_routes(self) -> None:
        success = (
            "vasp.6.5\nfree energy TOTEN = -10 eV\nEDIFF is reached\nElapsed time (sec): 4\n"
            "TOTAL-FORCE (eV/Angst)\n 1 2 3 0.1 0.2 0.3\n total drift\n"
            "General timing and accounting informations for this job\n"
        )
        temporary, path = self.parser_file(success, "OUTCAR")
        with temporary:
            result = self.parser.parse_vasp(path)
            self.assertTrue(result["parser_accepted"])
            self.assertEqual(result["forces"]["values"], [0.1, 0.2, 0.3])
            self.assertEqual(result["elapsed_time_s"], 4.0)
            self.assertEqual(result["energy"]["value"], -10.0)

        for text, stage in (
            ("EDIFF is reached\n", "termination"),
            ("General timing and accounting informations for this job\n", "electronic"),
            ("ZBRENT: fatal error\nGeneral timing and accounting informations for this job\n", "engine"),
            ("EDDDAV: Call to ZHEGV failed\n", "engine"),
            ("Sub-Space-Matrix is not hermitian\n", "engine"),
        ):
            temporary, path = self.parser_file(text, "OUTCAR")
            with temporary:
                result = self.parser.parse_vasp(path)
                self.assertEqual(result["failed_stage"], stage)
                self.assertFalse(result["parser_accepted"])

    def test_qe_all_acceptance_routes(self) -> None:
        success = (
            "Program PWSCF v.7.4\nconvergence has been achieved\nEnd of BFGS Geometry Optimization\n"
            "number of atoms/cell = 2\n! total energy = -1.0 Ry\n"
            "Forces acting on atoms (cartesian axes, Ry/au):\n"
            "atom 1 type 1 force = 0.100 0.200 0.300\n"
            "atom 2 type 1 force = -0.400 0.500 -0.600\n"
            "Total force = 0.9539392014169456\nP= 10\nJOB DONE.\n"
        )
        expected_factor = 13.605693122994 / 0.529177210903
        expected_factor_si = 8.2387234983e-8 / (2 * 1.602176634e-9)
        self.assertLessEqual(abs(expected_factor - expected_factor_si), 1e-8)
        expected_force = [0.1, 0.2, 0.3, -0.4, 0.5, -0.6]
        for sample in (success, success.replace("\n", "\r\n")):
            temporary, path = self.parser_file(sample)
            with temporary:
                result = self.parser.parse_qe(path)
                self.assertTrue(result["parser_accepted"])
                self.assertTrue(result["geometry_converged"])
                self.assertEqual(len(result["forces"]["values"]), 6)
                for actual, source in zip(result["forces"]["values"], expected_force, strict=True):
                    self.assertAlmostEqual(actual, source * expected_factor, places=12)
                    self.assertLessEqual(abs(actual / source - expected_factor_si), 1e-8)
                self.assertIsNone(result["stress"]["values"])
                self.assertTrue(any("scalar pressure" in warning for warning in result["warnings"]))

    def test_qe_rejects_scalar_and_incomplete_force_observables(self) -> None:
        scalar_only = (
            "Program PWSCF v.7.4\nconvergence has been achieved\n"
            "! total energy = -1.0 Ry\nTotal force = 0.5\nP= 10\nJOB DONE.\n"
        )
        temporary, path = self.parser_file(scalar_only)
        with temporary:
            result = self.parser.parse_qe(path)
            self.assertTrue(result["parser_accepted"])
            self.assertIsNone(result["forces"]["values"])
            self.assertIsNone(result["stress"]["values"])
            self.assertTrue(any("scalar summary" in warning for warning in result["warnings"]))

        valid_block = (
            "number of atoms/cell = 2\n"
            "Forces acting on atoms (cartesian axes, Ry/au):\n"
            "atom 1 type 1 force = 0.1 0.2 0.3\n"
            "atom 2 type 1 force = 0.4 0.5 0.6\n"
            "Total force = 0.9539392014169456\n"
        )
        incomplete_final_block = valid_block + (
            "Forces acting on atoms (cartesian axes, Ry/au):\natom 1 type 1 force = 0.7 0.8 0.9\n"
        )
        for force_text in (
            incomplete_final_block,
            valid_block.replace("atom 2 type 1 force = 0.4 0.5 0.6\n", ""),
            valid_block.replace("number of atoms/cell = 2\n", ""),
        ):
            temporary, path = self.parser_file(
                "Program PWSCF v.7.4\nconvergence has been achieved\n" + force_text + "JOB DONE.\n"
            )
            with temporary:
                result = self.parser.parse_qe(path)
                self.assertIsNone(result["forces"]["values"])
                self.assertTrue(result["warnings"])

        oversized_integer = "9" * 5000
        malformed_blocks = (
            (
                "number of atoms/cell = 0\n",
                "atom count",
            ),
            (
                f"number of atoms/cell = {oversized_integer}\n",
                "invalid atom count",
            ),
            (
                "number of atoms/cell = 1\n",
                "invalid atom index",
            ),
            (
                "number of atoms/cell = 1\n",
                "duplicate atom indices",
            ),
            (
                "number of atoms/cell = 1\n",
                "exactly one 3-component row",
            ),
        )
        for prefix, warning_text in malformed_blocks:
            atom_index = (
                oversized_integer
                if warning_text == "invalid atom index"
                else "2"
                if warning_text == "exactly one 3-component row"
                else "1"
            )
            rows = f"atom {atom_index} type 1 force = 0.1 0.2 0.3\n" + (
                "atom 1 type 1 force = 0.4 0.5 0.6\n" if warning_text == "duplicate atom indices" else ""
            )
            temporary, path = self.parser_file(
                "Program PWSCF v.7.4\nconvergence has been achieved\n"
                + prefix
                + "Forces acting on atoms (cartesian axes, Ry/au):\n"
                + rows
                + "Total force = 0.5\nJOB DONE.\n"
            )
            with temporary:
                result = self.parser.parse_qe(path)
                self.assertIsNone(result["forces"]["values"])
                self.assertTrue(any(warning_text in warning for warning in result["warnings"]))

    def test_qe_does_not_reuse_force_block_from_an_earlier_pwscf_job(self) -> None:
        text = (
            "Program PWSCF v.7.4\nconvergence has been achieved\n"
            "number of atoms/cell = 1\n"
            "Forces acting on atoms (cartesian axes, Ry/au):\n"
            "atom 1 type 1 force = 0.1 0.2 0.3\nTotal force = 0.3741657386773941\nJOB DONE.\n"
            "Program PWSCF v.7.4\nconvergence has been achieved\n"
            "! total energy = -1.0 Ry\nTotal force = 0.1\nJOB DONE.\n"
        )
        temporary, path = self.parser_file(text)
        with temporary:
            result = self.parser.parse_qe(path)
            self.assertTrue(result["parser_accepted"])
            self.assertIsNone(result["forces"]["values"])
            self.assertTrue(any("scalar summary" in warning for warning in result["warnings"]))

    def test_qe_final_job_scopes_energy_and_force_units(self) -> None:
        valid_block = (
            "number of atoms/cell = 1\n"
            "Forces acting on atoms (cartesian axes, Ry/au):\n"
            "atom 1 type 1 force = 0.1 0.2 0.3\nTotal force = 0.1\n"
        )
        unsupported_block = (
            "Forces acting on atoms (cartesian axes, unknown):\n"
            "atom 1 type 1 force = 0.4 0.5 0.6\nTotal force = 0.8774964387392122\n"
        )
        temporary, path = self.parser_file(
            "Program PWSCF v.7.4\nconvergence has been achieved\n"
            + valid_block
            + "Program PWSCF v.7.4\nconvergence has been achieved\n"
            + "JOB DONE.\n"
        )
        with temporary:
            result = self.parser.parse_qe(path)
            self.assertIsNone(result["energy"]["value"])
            self.assertIsNone(result["forces"]["values"])
            self.assertTrue(result["parser_accepted"])

        temporary, path = self.parser_file(
            "Program PWSCF v.7.4\nconvergence has been achieved\n" + valid_block + unsupported_block + "JOB DONE.\n"
        )
        with temporary:
            result = self.parser.parse_qe(path)
            self.assertIsNone(result["forces"]["values"])
            self.assertTrue(any("unsupported or missing unit" in warning for warning in result["warnings"]))

        for text, stage in (
            ("convergence has been achieved\n", "termination"),
            ("JOB DONE.\n", "electronic"),
            ("convergence NOT achieved\nJOB DONE.\n", "electronic"),
            ("Error in routine c_bands\nJOB DONE.\n", "engine"),
        ):
            temporary, path = self.parser_file(text)
            with temporary:
                result = self.parser.parse_qe(path)
                self.assertEqual(result["failed_stage"], stage)
                self.assertFalse(result["parser_accepted"])

    def test_cp2k_all_acceptance_routes(self) -> None:
        success = (
            "CP2K| version string: CP2K 2026.1\nSCF run converged\nGEOMETRY OPTIMIZATION COMPLETED\n"
            "ENERGY| Total FORCE_EVAL energy (a.u.): -1.0\nMax. gradient = 0.1\nPROGRAM ENDED AT\n"
        )
        temporary, path = self.parser_file(success)
        with temporary:
            result = self.parser.parse_cp2k(path)
            self.assertTrue(result["parser_accepted"])
            self.assertTrue(result["geometry_converged"])
            self.assertIsNone(result["forces"]["values"])
            self.assertTrue(any("scalar convergence metric" in warning for warning in result["warnings"]))

        for text, stage in (
            ("SCF run converged\n", "termination"),
            ("PROGRAM ENDED AT\n", "electronic"),
            ("SCF run NOT converged\nPROGRAM ENDED AT\n", "electronic"),
            ("ABORT\nPROGRAM ENDED AT\n", "engine"),
        ):
            temporary, path = self.parser_file(text)
            with temporary:
                result = self.parser.parse_cp2k(path)
                self.assertEqual(result["failed_stage"], stage)
                self.assertFalse(result["parser_accepted"])

    def test_dispatch_and_missing_sources(self) -> None:
        with self.assertRaises(ValueError):
            self.parser.parse_engine_output("unknown", Path("missing"))
        with tempfile.TemporaryDirectory() as temporary:
            missing = Path(temporary) / "missing"
            empty = Path(temporary) / "empty"
            empty.write_text("", encoding="utf-8")
            for engine in ("gaussian", "vasp", "quantum-espresso", "cp2k"):
                missing_result = self.parser.parse_engine_output(engine, missing)
                empty_result = self.parser.parse_engine_output(engine, empty)
                self.assertEqual(missing_result["fatal_marker"], "SOURCE_MISSING")
                self.assertEqual(empty_result["fatal_marker"], "SOURCE_MISSING")

    def test_bridge_loaders_and_artifact_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            json_path = root / "mapping.json"
            yaml_path = root / "mapping.yaml"
            json_path.write_text('{"a": 1}', encoding="utf-8")
            yaml_path.write_text("a: 1\n", encoding="utf-8")
            self.assertEqual(self.bridge.load_mapping(json_path), {"a": 1})
            self.assertEqual(self.bridge.load_mapping(yaml_path), {"a": 1})
            json_path.write_text("[]", encoding="utf-8")
            with self.assertRaises(ValueError):
                self.bridge.load_mapping(json_path)

            self.assertEqual(self.bridge.parse_key_value(None), {})
            kv = root / "runtime.txt"
            kv.write_text("a=1\nignored\nb = two=three\n", encoding="utf-8")
            self.assertEqual(self.bridge.parse_key_value(kv), {"a": "1", "b": "two=three"})

            self.assertEqual(self.bridge.parse_gpu_inventory(None), [])
            gpu = root / "gpu.csv"
            gpu.write_text("short\nH100, GPU-1, 0000:01, 590, 80G\n", encoding="utf-8")
            rows = self.bridge.parse_gpu_inventory(gpu)
            self.assertEqual(rows[0]["uuid"], "GPU-1")
            gpu.write_text("H100, GPU-1, 0000:01, 590\n", encoding="utf-8")
            self.assertEqual(self.bridge.parse_gpu_inventory(gpu)[0]["memory_total"], "")

            missing: list[str] = []
            source, relative = self.bridge._artifact_path(root, Path("out"), missing)
            self.assertEqual(source, (root / "out").resolve())
            self.assertEqual(relative, "out")
            outside = root.parent / "outside.out"
            _, relative = self.bridge._artifact_path(root, outside, missing)
            self.assertEqual(relative, "outside.out")
            self.assertTrue(missing)

    def test_bridge_complete_and_missing_records(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "input.in").write_text("input", encoding="utf-8")
            (root / "out").write_text("output", encoding="utf-8")
            parser_result = self.parser.base_result("vasp", root / "out")
            parser_result["source_artifact"]["sha256"] = self.parser.sha256_file(root / "out")
            parser_result.update(
                {
                    "engine_version": "6.5",
                    "normal_termination": True,
                    "parser_accepted": True,
                    "scf_iterations": 5,
                    "elapsed_time_s": 2.0,
                    "energy": {"value": -1.0, "unit": "eV"},
                    "forces": {"values": [0.1], "unit": "eV/angstrom"},
                    "stress": {"values": [0.2], "unit": "GPa"},
                }
            )
            manifest = {
                "input": "input.in",
                "executable": "vasp_std",
                "scheduler": "slurm",
                "resources": {"nodes": 2, "tasks_per_node": 4, "cpus_per_task": 8},
                "acceleration": {
                    "benchmark_plan_id": "PLAN",
                    "build_fingerprint_id": "BUILD",
                    "gpu_vendor": "nvidia",
                    "gpu_bind": "closest",
                },
            }
            fingerprint = {
                "method_fingerprint_id": "MF",
                "model_chemistry": {
                    "method": "PBE",
                    "basis_or_pseudopotential": "POT",
                    "dispersion_or_corrections": "D3",
                },
                "numerics": {"ediff": 1e-6},
            }
            record = self.bridge.build_record(
                "vasp",
                parser_result,
                manifest,
                fingerprint,
                root,
                Path("out"),
                "gpu",
                "acceleration-candidate",
                1,
                runtime={
                    "site_id": "SITE",
                    "hardware_fingerprint_id": "HW",
                    "run_id": "RUN",
                    "timestamp": "2026-01-01T00:00:00Z",
                    "exit_status": "7",
                    "compiler": "C",
                    "mpi": "M",
                    "openmp_runtime": "O",
                    "accelerator_runtime": "A",
                    "cpu_model": "CPU",
                    "cpu_arch": "x86_64",
                    "filesystem": "lustre",
                    "scratch_type": "nvme",
                },
                scheduler_metrics={
                    "job_id": "JOB",
                    "wall_time_s": 3,
                    "cpu_time_s": 2,
                    "peak_host_memory_mb": 4,
                    "io_bytes": 5,
                    "energy_joules": 6,
                },
                gpu_inventory=[
                    {
                        "name": "H100",
                        "uuid": "GPU-1",
                        "pci_bus_id": "0000:01",
                        "driver_version": "590",
                    }
                ],
            )
            self.assertEqual(record["execution"]["exit_status"], 7)
            self.assertEqual(record["scientific"]["observable_set"], ["energy", "forces", "stress"])
            self.assertEqual(record["evidence_source"]["missing_fields"], [])

            parser_result["engine_version"] = None
            parser_result["energy"] = {"value": None}
            parser_result["forces"] = {"values": None}
            parser_result["stress"] = {"values": None}
            outside = root.parent / "outside.out"
            missing_record = self.bridge.build_record(
                "vasp",
                parser_result,
                {"input": "../escape", "resources": {}, "acceleration": {}},
                {},
                root,
                outside,
                "gpu",
                "acceleration-candidate",
                1,
            )
            self.assertFalse(missing_record["scientific"]["parser_accepted"])
            self.assertTrue(missing_record["evidence_source"]["missing_fields"])
            self.assertEqual(missing_record["execution"]["exit_status"], -1)


if __name__ == "__main__":
    unittest.main()

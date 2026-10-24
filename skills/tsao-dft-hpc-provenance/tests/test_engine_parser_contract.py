from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str) -> Any:
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(f"parser_{name}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class EngineParserContractTests(unittest.TestCase):
    core: Any
    schema: dict[str, Any]

    @classmethod
    def setUpClass(cls) -> None:
        cls.core = load_script("engine_parser_contract.py")
        cls.schema = json.loads((ROOT / "templates/engine-parser-result.schema.json").read_text(encoding="utf-8"))

    def assert_schema(self, result: dict[str, Any]) -> None:
        errors = list(Draft202012Validator(self.schema, format_checker=FormatChecker()).iter_errors(result))
        self.assertEqual(errors, [])

    def test_gaussian_last_route_section_handles_route_boundaries(self):
        self.assertEqual(
            self.core._last_route_section([b"non-route", b"#p old", b"freq", b"#p final", b"opt", b"", b"ignored"]),
            b"#p final opt",
        )
        self.assertEqual(
            self.core._last_route_section([b"#p route", b"freq", b"---", b"ignored"]),
            b"#p route freq",
        )
        self.assertIsNone(self.core._last_route_section([b"non-route"]))

    def test_missing_files_return_structured_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            missing = Path(temporary) / "missing.out"
            for engine in ("gaussian", "vasp", "quantum-espresso", "cp2k"):
                result = self.core.parse_engine_output(engine, missing)
                self.assertEqual(result["fatal_marker"], "SOURCE_MISSING")
                self.assertFalse(result["parser_accepted"])
                self.assert_schema(result)

    def test_gaussian_late_error_wins(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "job.log"
            path.write_text(
                "#p pbe/6-31g opt\nSCF Done: E(RPBE) = -1.0\nNormal termination of Gaussian\n"
                "Entering Link 1\n#p pbe/6-31g opt\nError termination via Lnk1e\n",
                encoding="utf-8",
            )
            result = self.core.parse_gaussian(path)
            self.assertFalse(result["parser_accepted"])
            self.assertEqual(result["fatal_marker"], "ERROR_TERMINATION")
            self.assertEqual(result["job_index"], 2)
            self.assert_schema(result)

    def test_gaussian_normal_termination_requires_route_and_scf_evidence(self):
        cases = (
            (
                "missing route",
                "SCF Done: E(RHF) = -1.0\nNormal termination of Gaussian\n",
                "input",
            ),
            (
                "missing SCF result",
                "#p hf/sto-3g sp\nNormal termination of Gaussian\n",
                "electronic",
            ),
        )
        for name, text, stage in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                path = Path(temporary) / "job.log"
                path.write_text(text, encoding="utf-8")
                result = self.core.parse_gaussian(path)
                self.assertFalse(result["parser_accepted"])
                self.assertEqual(result["failed_stage"], stage)
                self.assert_schema(result)

    def test_gaussian_frequency_route_requires_frequency_records(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "job.log"
            path.write_text(
                "#p hf/sto-3g freq\nSCF Done: E(RHF) = -1.0\nNormal termination of Gaussian\n",
                encoding="utf-8",
            )
            result = self.core.parse_gaussian(path)
            self.assertFalse(result["parser_accepted"])
            self.assertEqual(result["failed_stage"], "scientific-gate")
            self.assert_schema(result)

    def test_gaussian_route_continuation_controls_frequency_gate(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "job.log"
            path.write_text(
                "#p hf/sto-3g\nfreq\nSCF Done: E(RHF) = -1.0\n"
                "Frequencies -- -100.0 -80.0 200.0\nNormal termination of Gaussian\n",
                encoding="utf-8",
            )
            result = self.core.parse_gaussian(path)
            self.assertFalse(result["parser_accepted"])
            self.assertEqual(result["failed_stage"], "scientific-gate")
            self.assert_schema(result)

    def test_gaussian_route_continuation_accepts_one_imaginary_frequency(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "job.log"
            path.write_text(
                "#p hf/sto-3g\nfreq\nSCF Done: E(RHF) = -1.0\n"
                "Frequencies -- -100.0 100.0 200.0\nNormal termination of Gaussian\n",
                encoding="utf-8",
            )
            result = self.core.parse_gaussian(path)
            self.assertTrue(result["parser_accepted"])
            self.assertIsNone(result["failed_stage"])
            self.assert_schema(result)

    def test_gaussian_optimization_continuation_requires_completion_marker(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "job.log"
            path.write_text(
                "#p hf/sto-3g\nopt\nSCF Done: E(RHF) = -1.0\nNormal termination of Gaussian\n",
                encoding="utf-8",
            )
            result = self.core.parse_gaussian(path)
            self.assertFalse(result["parser_accepted"])
            self.assertFalse(result["geometry_converged"])
            self.assertEqual(result["failed_stage"], "geometry")
            self.assert_schema(result)

    def test_vasp_fatal_warning_blocks(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "OUTCAR"
            path.write_text(
                "vasp.6.5.1\nfree energy TOTEN = -10 eV\nEDIFF is reached\n"
                "BRMIX: very serious problems\nGeneral timing and accounting informations for this job\n",
                encoding="utf-8",
            )
            result = self.core.parse_vasp(path)
            self.assertEqual(result["fatal_marker"], "BRMIX_FATAL")
            self.assertFalse(result["parser_accepted"])
            self.assert_schema(result)

    def test_vasp_appended_incomplete_run_does_not_inherit_prior_markers(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "OUTCAR"
            path.write_text(
                "vasp.6.4.3\nDAV: 1 -10.0 0.0 0.0 8 0.1\n"
                "free energy TOTEN = -10.0 eV\nEDIFF is reached\n"
                "General timing and accounting informations for this job\n"
                "vasp.6.5.1\nRMM: 1 -9.0 0.0 0.0 8 0.1\n"
                "free energy TOTEN = -9.0 eV\n",
                encoding="utf-8",
            )
            result = self.core.parse_vasp(path)
            self.assertFalse(result["parser_accepted"])
            self.assertFalse(result["normal_termination"])
            self.assertFalse(result["electronic_converged"])
            self.assertEqual(result["failed_stage"], "termination")
            self.assertEqual(result["engine_version"], "6.5.1")
            self.assertEqual(result["job_index"], 2)
            self.assertEqual(result["energy"]["value"], -9.0)
            self.assertEqual(result["scf_iterations"], 1)
            self.assert_schema(result)

    def test_vasp_scf_count_uses_electronic_iteration_records(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "OUTCAR"
            path.write_text(
                "vasp.6.5.1\nDAV: 1 -10.0 0.0 0.0 8 0.1\n"
                "RMM: 2 -10.1 -0.1 0.0 8 0.05\nDMP: 3 -10.2 -0.1 0.0 8 0.01\n"
                "free energy TOTEN = -10.1 eV\nfree energy TOTEN = -10.2 eV\n"
                "EDIFF is reached\nGeneral timing and accounting informations for this job\n",
                encoding="utf-8",
            )
            result = self.core.parse_vasp(path)
            self.assertTrue(result["parser_accepted"])
            self.assertEqual(result["scf_iterations"], 3)
            self.assert_schema(result)

    def test_vasp_energy_records_without_iteration_markers_do_not_claim_a_count(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "OUTCAR"
            path.write_text(
                "vasp.6.5.1\nfree energy TOTEN = -10.1 eV\nfree energy TOTEN = -10.2 eV\n"
                "EDIFF is reached\nGeneral timing and accounting informations for this job\n",
                encoding="utf-8",
            )
            result = self.core.parse_vasp(path)
            self.assertTrue(result["parser_accepted"])
            self.assertIsNone(result["scf_iterations"])
            self.assert_schema(result)

    def test_qe_late_routine_error_wins(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "pw.out"
            path.write_text(
                "Program PWSCF v.7.4\nconvergence has been achieved\n! total energy = -1.0 Ry\n"
                "JOB DONE.\nError in routine cdiaghg\n",
                encoding="utf-8",
            )
            result = self.core.parse_qe(path)
            self.assertEqual(result["fatal_marker"], "ERROR_IN_ROUTINE")
            self.assertFalse(result["parser_accepted"])
            self.assert_schema(result)

    def test_qe_scf_count_uses_iteration_records_not_energy_records(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "pw.out"
            path.write_text(
                "Program PWSCF v.7.4\n"
                "iteration # 1 ecut= 40.00 Ry beta=0.70\n! total energy = -1.0 Ry\n"
                "iteration # 2 ecut= 40.00 Ry beta=0.70\n! total energy = -1.1 Ry\n"
                "iteration # 3 ecut= 40.00 Ry beta=0.70\n"
                "convergence has been achieved\nJOB DONE.\n",
                encoding="utf-8",
            )
            result = self.core.parse_qe(path)
            self.assertTrue(result["parser_accepted"])
            self.assertEqual(result["scf_iterations"], 3)
            self.assert_schema(result)

    def test_qe_energy_records_without_iteration_markers_do_not_claim_a_count(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "pw.out"
            path.write_text(
                "Program PWSCF v.7.4\n! total energy = -1.0 Ry\n! total energy = -1.1 Ry\n"
                "convergence has been achieved\nJOB DONE.\n",
                encoding="utf-8",
            )
            result = self.core.parse_qe(path)
            self.assertTrue(result["parser_accepted"])
            self.assertIsNone(result["scf_iterations"])
            self.assert_schema(result)

    def test_cp2k_late_abort_wins(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "cp2k.out"
            path.write_text(
                "CP2K| version string: CP2K 2026.1\nSCF run converged\n"
                "ENERGY| Total FORCE_EVAL energy (a.u.): -1.0\nPROGRAM ENDED AT\nABORT\n",
                encoding="utf-8",
            )
            result = self.core.parse_cp2k(path)
            self.assertEqual(result["fatal_marker"], "ABORT")
            self.assertFalse(result["parser_accepted"])
            self.assert_schema(result)

    def test_loader_hash_and_finalize_compatibility_paths(self):
        with (
            patch.object(self.core.importlib.util, "spec_from_file_location", return_value=None),
            self.assertRaisesRegex(RuntimeError, "cannot import"),
        ):
            self.core._load_scan_core()

        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "artifact.out"
            payload = b"abcdef"
            path.write_bytes(payload)
            expected = hashlib.sha256(payload).hexdigest()
            self.assertEqual(self.core.sha256_file(path, chunk_size=2), expected)
            result = self.core._finalize(self.core.base_result("vasp", path), path)
            self.assertEqual(result["source_artifact"]["sha256"], expected)

            missing = Path(temporary) / "missing.out"
            result = self.core._finalize(self.core.base_result("vasp", missing), missing)
            self.assertIsNone(result["source_artifact"]["sha256"])

        result = self.core._finalize(self.core.base_result("vasp", Path("missing")), object())
        self.assertIsNone(result["source_artifact"]["sha256"])

    def test_nonfinite_engine_numbers_fail_closed(self):
        for value in (b"NaN", b"Infinity", b"-Infinity"):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "non-finite"):
                self.core._float(value)


if __name__ == "__main__":
    unittest.main()

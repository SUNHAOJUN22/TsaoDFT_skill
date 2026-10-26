from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str) -> Any:
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(f"bridge_{name}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BenchmarkBridgeTests(unittest.TestCase):
    bridge: Any
    parser: Any
    performance: Any

    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_script("benchmark_bridge.py")
        cls.parser = load_script("engine_parser_contract.py")
        cls.performance = load_script("performance_evidence.py")

    def bridge_vasp_record(
        self,
        root: Path,
        output: Path,
        parsed: dict[str, Any],
        *,
        runtime: dict[str, str] | None = None,
        scheduler_metrics: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        runtime_values = {
            "site_id": "SITE-A",
            "hardware_fingerprint_id": "HW-A",
            "run_id": "RUN-1",
            "timestamp": "2026-10-24T00:00:00Z",
        }
        runtime_values.update(runtime or {})
        scheduler_values = {"job_id": "JOB-1", "wall_time_s": 1}
        scheduler_values.update(scheduler_metrics or {})
        return self.bridge.build_record(
            "vasp",
            parsed,
            {
                "input": "INCAR",
                "executable": "vasp_std",
                "scheduler": "slurm",
                "resources": {"nodes": 1, "tasks_per_node": 1, "cpus_per_task": 8},
                "acceleration": {
                    "benchmark_plan_id": "PLAN-1",
                    "build_fingerprint_id": "BUILD-1",
                    "gpu_vendor": "none",
                    "gpu_bind": "none",
                },
            },
            {
                "method_fingerprint_id": "MF-1",
                "model_chemistry": {
                    "method": "PBE",
                    "basis_or_pseudopotential": "POTCAR-HASH",
                    "corrections": "none",
                },
                "numerics": {"ediff": 1e-6},
            },
            root,
            output.relative_to(root),
            "cpu-reference",
            "scientific-reference",
            1,
            runtime=runtime_values,
            scheduler_metrics=scheduler_values,
        )

    def test_vasp_bridge_extracts_fields_without_manual_copy(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "INCAR").write_text("ENCUT=500\n", encoding="utf-8")
            out = root / "OUTCAR"
            out.write_text(
                "vasp.6.5.1\nfree energy TOTEN = -10.0 eV\naborting loop because EDIFF is reached\n"
                "General timing and accounting informations for this job\n",
                encoding="utf-8",
            )
            parsed = self.parser.parse_vasp(out)
            manifest = {
                "input": "INCAR",
                "executable": "vasp_std",
                "scheduler": "slurm",
                "resources": {"nodes": 1, "tasks_per_node": 1, "cpus_per_task": 8},
                "acceleration": {
                    "benchmark_plan_id": "PLAN-1",
                    "build_fingerprint_id": "BUILD-1",
                    "gpu_vendor": "none",
                    "gpu_bind": "none",
                },
            }
            fingerprint = {
                "method_fingerprint_id": "MF-1",
                "model_chemistry": {
                    "method": "PBE",
                    "basis_or_pseudopotential": "POTCAR-HASH",
                    "corrections": "none",
                },
                "numerics": {"ediff": 1e-6},
            }
            record = self.bridge.build_record(
                "vasp",
                parsed,
                manifest,
                fingerprint,
                root,
                Path("OUTCAR"),
                "cpu-reference",
                "scientific-reference",
                1,
                runtime={
                    "site_id": "SITE-A",
                    "hardware_fingerprint_id": "HW-A",
                    "run_id": "RUN-1",
                    "timestamp": "2026-07-29T00:00:00Z",
                    "exit_status": "0",
                },
            )
            self.assertEqual(record["engine"]["version"], "6.5.1")
            self.assertEqual(record["scientific"]["results"]["energy_ev"], -10.0)
            self.assertNotIn("engine version", record["evidence_source"]["missing_fields"])

    def test_unknown_scf_count_remains_unknown_through_bridge_and_validation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "INCAR").write_text("ENCUT=500\n", encoding="utf-8")
            output = root / "OUTCAR"
            output.write_text(
                "vasp.6.5.1\nfree energy TOTEN = -10 eV\nEDIFF is reached\n"
                "General timing and accounting informations for this job\n",
                encoding="utf-8",
            )
            parsed = self.parser.parse_vasp(output)
            self.assertIsNone(parsed["scf_iterations"])
            record = self.bridge_vasp_record(root, output, parsed, runtime={"exit_status": "0"})
            self.assertIsNone(record["performance"]["scf_iterations"])
            normalized, errors, _ = self.performance.validate_result(record, root)
            self.assertEqual(errors, [])
            self.assertTrue(normalized["scientific"]["parser_accepted"])

    def test_qe_scalar_summaries_do_not_become_bridge_force_or_stress_observables(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "pw.in").write_text("&CONTROL\n calculation='scf'\n/\n", encoding="utf-8")
            out = root / "pw.out"
            out.write_text(
                "Program PWSCF v.7.4\nconvergence has been achieved\n"
                "! total energy = -1.0 Ry\nTotal force = 0.5\nP= 10\nJOB DONE.\n",
                encoding="utf-8",
            )
            parsed = self.parser.parse_qe(out)
            record = self.bridge.build_record(
                "quantum-espresso",
                parsed,
                {
                    "input": "pw.in",
                    "executable": "pw.x",
                    "scheduler": "slurm",
                    "resources": {"nodes": 1, "tasks_per_node": 1, "cpus_per_task": 1},
                    "acceleration": {
                        "benchmark_plan_id": "PLAN-QE",
                        "build_fingerprint_id": "BUILD-QE",
                        "gpu_vendor": "none",
                        "gpu_bind": "none",
                    },
                },
                {
                    "method_fingerprint_id": "MF-QE",
                    "model_chemistry": {
                        "method": "PBE",
                        "basis_or_pseudopotential": "UPF-HASH",
                        "corrections": "none",
                    },
                    "numerics": {"conv_thr": 1e-8},
                },
                root,
                Path("pw.out"),
                "qe-cpu-reference",
                "scientific-reference",
                1,
                runtime={
                    "site_id": "SITE-QE",
                    "hardware_fingerprint_id": "HW-QE",
                    "run_id": "RUN-QE",
                    "timestamp": "2026-07-29T00:00:00Z",
                    "exit_status": "0",
                },
                scheduler_metrics={"job_id": "JOB-QE", "wall_time_s": 1},
            )
            self.assertTrue(parsed["parser_accepted"])
            self.assertEqual(record["scientific"]["observable_set"], ["energy"])
            self.assertIsNone(record["scientific"]["results"]["forces_ev_per_angstrom"])
            self.assertIsNone(record["scientific"]["results"]["stress_gpa"])
            self.assertTrue(record["scientific"]["parser_accepted"])

    def test_parser_result_must_match_output_hash_size_and_engine(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "INCAR").write_text("ENCUT=500\n", encoding="utf-8")
            out = root / "OUTCAR"
            out.write_text(
                "vasp.6.5.1\nfree energy TOTEN = -10.0 eV\nEDIFF is reached\n"
                "General timing and accounting informations for this job\n",
                encoding="utf-8",
            )
            parsed = self.parser.parse_vasp(out)
            matching = self.bridge_vasp_record(root, out, parsed, runtime={"exit_status": "0"})
            self.assertTrue(matching["scientific"]["parser_accepted"])
            self.assertEqual(matching["evidence_source"]["missing_fields"], [])
            matching_with_size = {
                **parsed,
                "source_artifact": {
                    **parsed["source_artifact"],
                    "size_bytes": out.stat().st_size,
                },
            }
            size_bound = self.bridge_vasp_record(root, out, matching_with_size, runtime={"exit_status": "0"})
            self.assertTrue(size_bound["scientific"]["parser_accepted"])

            cases = (
                ("hash", "parser source artifact SHA-256 does not match output artifact"),
                ("engine", "parser result engine does not match bridge engine"),
                ("optional_size", "parser source artifact size_bytes does not match output artifact"),
                ("invalid_size", "parser source artifact size_bytes is invalid"),
                ("missing_metadata", "parser source artifact metadata is unavailable"),
            )
            for field, expected_error in cases:
                with self.subTest(field=field):
                    candidate = {
                        **parsed,
                        "source_artifact": dict(parsed["source_artifact"]),
                    }
                    if field == "hash":
                        candidate["source_artifact"]["sha256"] = "0" * 64
                    elif field == "engine":
                        candidate["engine"] = "cp2k"
                    elif field == "invalid_size":
                        candidate["source_artifact"]["size_bytes"] = True
                    elif field == "missing_metadata":
                        candidate["source_artifact"] = None
                    else:
                        candidate["source_artifact"]["size_bytes"] = out.stat().st_size + 1
                    record = self.bridge_vasp_record(root, out, candidate, runtime={"exit_status": "0"})
                    self.assertFalse(record["scientific"]["parser_accepted"])
                    self.assertIn(expected_error, record["evidence_source"]["missing_fields"])

    def test_execution_status_is_external_fail_closed_and_downstream_visible(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "INCAR").write_text("ENCUT=500\n", encoding="utf-8")
            out = root / "OUTCAR"
            out.write_text(
                "vasp.6.5.1\nfree energy TOTEN = -10.0 eV\nEDIFF is reached\n"
                "General timing and accounting informations for this job\n",
                encoding="utf-8",
            )
            parsed = self.parser.parse_vasp(out)

            scheduler_failure = self.bridge_vasp_record(root, out, parsed, scheduler_metrics={"exit_status": 37})
            self.assertEqual(scheduler_failure["execution"]["exit_status"], 37)
            self.assertTrue(scheduler_failure["scientific"]["parser_accepted"])
            self.assertFalse(self.performance.parser_success(scheduler_failure))

            conflicting = self.bridge_vasp_record(
                root,
                out,
                parsed,
                runtime={"exit_status": "0"},
                scheduler_metrics={"exit_status": 37},
            )
            self.assertEqual(conflicting["execution"]["exit_status"], -1)
            self.assertIn(
                "runtime.exit_status=0 conflicts with scheduler_metrics.exit_status=37",
                conflicting["evidence_source"]["missing_fields"],
            )
            self.assertTrue(conflicting["scientific"]["parser_accepted"])
            self.assertFalse(self.performance.parser_success(conflicting))

            missing = self.bridge_vasp_record(root, out, parsed)
            self.assertEqual(missing["execution"]["exit_status"], -1)
            self.assertIn("execution exit_status is unavailable", missing["evidence_source"]["missing_fields"])
            self.assertTrue(missing["scientific"]["parser_accepted"])
            self.assertFalse(self.performance.parser_success(missing))

            runtime_success = self.bridge_vasp_record(root, out, parsed, runtime={"exit_status": "0"})
            self.assertEqual(runtime_success["execution"]["exit_status"], 0)
            self.assertTrue(self.performance.parser_success(runtime_success))

            scheduler_success = self.bridge_vasp_record(root, out, parsed, scheduler_metrics={"exit_status": 0})
            self.assertEqual(scheduler_success["execution"]["exit_status"], 0)
            self.assertTrue(self.performance.parser_success(scheduler_success))

            matching_statuses = self.bridge_vasp_record(
                root,
                out,
                parsed,
                runtime={"exit_status": "0"},
                scheduler_metrics={"exit_status": 0},
            )
            self.assertEqual(matching_statuses["execution"]["exit_status"], 0)
            self.assertTrue(self.performance.parser_success(matching_statuses))

    def test_invalid_execution_status_never_defaults_to_success(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "INCAR").write_text("ENCUT=500\n", encoding="utf-8")
            out = root / "OUTCAR"
            out.write_text(
                "vasp.6.5.1\nfree energy TOTEN = -10.0 eV\nEDIFF is reached\n"
                "General timing and accounting informations for this job\n",
                encoding="utf-8",
            )
            parsed = self.parser.parse_vasp(out)
            for value in (True, 1.5, "invalid", "9" * 5000):
                with self.subTest(value_type=type(value).__name__, value_length=len(str(value))):
                    record = self.bridge_vasp_record(root, out, parsed, scheduler_metrics={"exit_status": value})
                    self.assertEqual(record["execution"]["exit_status"], -1)
                    self.assertIn(
                        "scheduler_metrics.exit_status is not an integer",
                        record["evidence_source"]["missing_fields"],
                    )
                    self.assertFalse(self.performance.parser_success(record))

            invalid_runtime = self.bridge_vasp_record(
                root,
                out,
                parsed,
                runtime={"exit_status": "invalid"},
                scheduler_metrics={"exit_status": 0},
            )
            self.assertEqual(invalid_runtime["execution"]["exit_status"], -1)
            self.assertIn(
                "runtime.exit_status is not an integer",
                invalid_runtime["evidence_source"]["missing_fields"],
            )
            self.assertFalse(self.performance.parser_success(invalid_runtime))

    def test_missing_fields_block_parser_acceptance(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            parsed = self.parser.missing_result("cp2k", root / "missing.out")
            record = self.bridge.build_record(
                "cp2k",
                parsed,
                {"input": "missing.inp", "resources": {}, "acceleration": {}},
                {},
                root,
                Path("missing.out"),
                "gpu-1",
                "acceleration-candidate",
                1,
            )
            self.assertFalse(record["scientific"]["parser_accepted"])
            self.assertEqual(record["evidence_source"]["kind"], "imported-unverified")
            self.assertTrue(record["evidence_source"]["missing_fields"])


if __name__ == "__main__":
    unittest.main()

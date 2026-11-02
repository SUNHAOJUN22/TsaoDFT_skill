from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/preflight_vasp.py"
SPEC = importlib.util.spec_from_file_location("incar_statement_preflight", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
VASP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VASP)

POSCAR = "input contract\n1\n1 0 0\n0 1 0\n0 0 1\nH\n1\nDirect\n0 0 0\n"


class IncarStatementContractTests(unittest.TestCase):
    def parse(self, text: str) -> dict[str, str]:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "INCAR"
            path.write_text(text, encoding="utf-8")
            return VASP.parse_incar(path)

    def preflight(self, text: str) -> dict:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / "INCAR").write_text(text, encoding="utf-8")
            (directory / "POSCAR").write_text(POSCAR, encoding="utf-8")
            return VASP.validate(directory)

    def test_flat_equivalent_layouts_preserve_every_tag(self):
        statements = ["ENCUT=520", "EDIFF=1e-6", "PREC=Accurate", "NSW=60", "IBRION=2"]
        expected = {"ENCUT": "520", "EDIFF": "1e-6", "PREC": "Accurate", "NSW": "60", "IBRION": "2"}
        for separator in ("\n", "; ", ";\n"):
            with self.subTest(separator=separator):
                self.assertEqual(self.parse(separator.join(statements) + "\n"), expected)

    def test_semicolon_layout_preserves_ionic_task_and_scientific_warnings(self):
        report = self.preflight("ENCUT=520; EDIFF=1e-6; PREC=Accurate; NSW=60; IBRION=2; ISPIN=2; LDAUL=2\n")
        self.assertEqual(report["task_inferred"], "relax")
        self.assertFalse(report["ok"])
        self.assertIn("DFT+U tags present without LDAUU", report["errors"])
        self.assertIn("spin-polarized run lacks explicit MAGMOM", report["warnings"])
        self.assertEqual(report["scientific_acceptance"], "PENDING")

    def test_comment_text_cannot_reactivate_tags(self):
        parsed = self.parse("ENCUT=520; NSW=60 ! NSW=0; IBRION=-1\nIBRION=2 # NSW=0; ISPIN=2\n")
        self.assertEqual(parsed, {"ENCUT": "520", "NSW": "60", "IBRION": "2"})

    def test_continuation_preserves_all_magnetic_moments(self):
        parsed = self.parse("MAGMOM=0 0 1 \\\n 0 0 -1 \\\n 6*0; ISPIN=2\n")
        self.assertEqual(parsed["MAGMOM"].split(), ["0", "0", "1", "0", "0", "-1", "6*0"])
        self.assertEqual(parsed["ISPIN"], "2")

    def test_quoted_block_does_not_create_global_incar_tags(self):
        parsed = self.parse(
            'WANNIER90_WIN = "\nBegin Projections\nNSW=0; ISPIN=1\nEnd Projections\n"\nNSW=60; ISPIN=2\n'
        )
        self.assertEqual(parsed["NSW"], "60")
        self.assertEqual(parsed["ISPIN"], "2")
        self.assertIn("NSW=0; ISPIN=1", parsed["WANNIER90_WIN"])
        self.assertIn("End Projections", parsed["WANNIER90_WIN"])
        self.assertEqual(set(parsed), {"WANNIER90_WIN", "NSW", "ISPIN"})

    def test_repeated_flat_tag_retains_last_active_declaration(self):
        self.assertEqual(self.parse("NSW=0; NSW=4\nNSW=8 ! NSW=0\n"), {"NSW": "8"})

    def test_quoted_scalars_and_explicit_nested_tag_paths(self):
        report = self.preflight('NSW="60"; IBRION="2"; PLUGINS/STRUCTURE=T\n')
        self.assertEqual(report["task_inferred"], "relax")
        self.assertEqual(report["incar"]["PLUGINS/STRUCTURE"], "T")

    def test_signed_integer_controls_preserve_task_and_warning_semantics(self):
        for value, expected in (
            ("+60", "relax"),
            ("00060", "relax"),
            ("0", "static"),
            ("+0", "static"),
            ("-1", "static"),
        ):
            with self.subTest(value=value):
                report = self.preflight(f"NSW={value}; IBRION=+02; ISPIN=+2\n")
                self.assertTrue(report["ok"])
                self.assertEqual(report["task_inferred"], expected)
                self.assertIn("spin-polarized run lacks explicit MAGMOM", report["warnings"])

    def test_only_explicit_optimization_modes_infer_relaxation(self):
        for separator in ("\n", "; "):
            for mode in ("1", "+02", "3"):
                with self.subTest(separator=separator, mode=mode):
                    report = self.preflight(f"NSW=10{separator}IBRION={mode}\n")
                    self.assertTrue(report["ok"])
                    self.assertEqual(report["task_inferred"], "relax")
                    self.assertEqual(report["scientific_acceptance"], "PENDING")

    def test_other_ionic_modes_are_not_misreported_as_relaxation(self):
        for separator in ("\n", "; "):
            for mode in (None, "0", "+0", "5", "006", "7", "8", "11", "12", "40", "44"):
                with self.subTest(separator=separator, mode=mode):
                    declaration = "" if mode is None else f"{separator}IBRION={mode}"
                    report = self.preflight(f"NSW=10{declaration}\n")
                    self.assertTrue(report["ok"])
                    self.assertEqual(report["task_inferred"], "unknown")
                    self.assertTrue(any("mode-specific review" in warning for warning in report["warnings"]))
                    self.assertEqual(report["scientific_acceptance"], "PENDING")

    def test_no_update_and_zero_step_controls_preserve_static_classification(self):
        for nsw, mode in (("10", "-01"), ("0", None), ("-1", None), ("0", "2")):
            with self.subTest(nsw=nsw, mode=mode):
                declaration = "" if mode is None else f"; IBRION={mode}"
                report = self.preflight(f"NSW={nsw}{declaration}\n")
                self.assertTrue(report["ok"])
                self.assertEqual(report["task_inferred"], "static")
                if nsw == "10":
                    self.assertTrue(any("without structural updates" in warning for warning in report["warnings"]))
        for nsw, mode in (("0", "6"), ("0", "0"), ("-2", "2")):
            with self.subTest(nsw=nsw, mode=mode):
                self.assertEqual(self.preflight(f"NSW={nsw}; IBRION={mode}\n")["task_inferred"], "unknown")

    def test_noninteger_controls_fail_without_inventing_a_task(self):
        for key in ("NSW", "IBRION", "ISPIN"):
            for value in ("1.5", "60.0", "1e2", "1_000", "NaN", "--1", "1 2", "\u0661"):
                with self.subTest(key=key, value=value):
                    report = self.preflight(f"{key}={value}\n")
                    self.assertFalse(report["ok"])
                    self.assertEqual(report["task_inferred"], "unknown")
                    self.assertEqual(report["scientific_acceptance"], "PENDING")
                    self.assertTrue(any(key in error for error in report["errors"]))

    def test_integer_range_is_explicit_and_not_a_float_conversion(self):
        for value in (str(2**63), str(-(2**63) - 1), "9" * 400, "1" + "0" * 5000):
            with self.subTest(digits=len(value)):
                report = self.preflight(f"NSW={value}\n")
                self.assertFalse(report["ok"])
                self.assertEqual(report["task_inferred"], "unknown")
                self.assertTrue(any("supported signed 64-bit range" in error for error in report["errors"]))
        for value in (str(2**63 - 1), str(-(2**63)), "0" * 5000 + "60"):
            with self.subTest(digits=len(value)):
                self.assertTrue(self.preflight(f"NSW={value}\n")["ok"])

    def test_malformed_or_unhandled_scope_is_rejected(self):
        for content in ('NSW="60\n', "MAGMOM=0 0 1 \\\n", "NSW=\n", 'NSW=""\n', "PLUGINS {\nSTRUCTURE=T\n}\n"):
            with self.subTest(content=content), self.assertRaises(ValueError):
                self.parse(content)

    def test_preflight_returns_json_failure_for_unhandled_scope_and_huge_integer(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / "POSCAR").write_text(POSCAR, encoding="utf-8")
            for text in ("IMAGES {\nNSW=60\n}\n", "NSW=" + "9" * 400 + "\n"):
                with self.subTest(text=text[:20]):
                    (directory / "INCAR").write_text(text, encoding="utf-8")
                    result = subprocess.run(
                        [sys.executable, str(SCRIPT), str(directory), "--json"], capture_output=True, text=True
                    )
                    self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                    report = json.loads(result.stdout)
                    self.assertFalse(report["ok"])
                    self.assertEqual(report["task_inferred"], "unknown")
                    self.assertEqual(report["scientific_acceptance"], "PENDING")
                    self.assertTrue(any(error.startswith("INCAR:") for error in report["errors"]))


if __name__ == "__main__":
    unittest.main()

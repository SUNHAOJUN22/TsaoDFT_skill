import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class GeometryAuditTests(unittest.TestCase):
    def test_xyz_inspection(self):
        r = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/inspect_xyz.py"),
                str(ROOT / "examples/geometry-audit/water.xyz"),
                "--json",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        d = json.loads(r.stdout)
        self.assertEqual(d["atom_count"], 3)
        self.assertEqual(len(d["heuristic_bonds"]), 2)

    def test_json_cli_is_readable_under_legacy_console_encoding(self):
        with tempfile.TemporaryDirectory() as temporary:
            xyz = Path(temporary) / "short-contact.xyz"
            output = Path(temporary) / "inspection.json"
            xyz.write_text("2\nencoding regression\nC 0 0 0\nC 0.1 0 0\n", encoding="utf-8")
            environment = os.environ.copy()
            environment["PYTHONIOENCODING"] = "gbk"
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts/inspect_xyz.py"), str(xyz), "--json", "--out", str(output)],
                capture_output=True,
                text=True,
                env=environment,
                check=False,
            )
            output_text = output.read_text(encoding="utf-8")
        self.assertEqual(result.returncode, 1, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(any("Å" in error for error in payload["errors"]))
        self.assertIn("Å", output_text)
        self.assertEqual(json.loads(output_text), payload)

    def test_mapping(self):
        r = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/validate_atom_mapping.py"),
                str(ROOT / "examples/geometry-audit/water.xyz"),
                str(ROOT / "examples/geometry-audit/water-shifted.xyz"),
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("raw_rmsd_angstrom", r.stdout)


if __name__ == "__main__":
    unittest.main()

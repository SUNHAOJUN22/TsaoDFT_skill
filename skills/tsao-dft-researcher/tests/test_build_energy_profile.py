from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class BuildEnergyProfileTests(unittest.TestCase):
    def test_creates_table_and_three_figures(self) -> None:
        script = Path(__file__).resolve().parents[1] / "scripts" / "build_energy_profile.py"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "energies.csv"
            with source.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(["label", "g_hartree"])
                writer.writerow(["R", -100.0])
                writer.writerow(["TS", -99.98])
                writer.writerow(["P", -100.01])
            prefix = root / "pathway"
            completed = subprocess.run(
                [sys.executable, str(script), str(source), "--out", str(prefix)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            for suffix in (".csv", ".svg", ".pdf", ".png"):
                output = prefix.with_suffix(suffix)
                self.assertTrue(output.exists(), output)
                self.assertGreater(output.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()

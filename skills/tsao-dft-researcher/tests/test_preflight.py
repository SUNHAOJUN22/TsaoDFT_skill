from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PreflightTests(unittest.TestCase):
    def test_initialized_project_preflights_with_warnings(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "demo"
            init = ROOT / "scripts/init_project.py"
            preflight = ROOT / "scripts/preflight_project.py"
            subprocess.run([sys.executable, str(init), str(project)], check=True, capture_output=True, text=True)
            result = subprocess.run([sys.executable, str(preflight), str(project), "--json"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertIn('\"ok\": true', result.stdout.lower())
            self.assertTrue((project / '.research/manifests/research-manifest.json').exists())
            self.assertTrue((project / '.research/manifests/figure-manifest.json').exists())


if __name__ == "__main__":
    unittest.main()

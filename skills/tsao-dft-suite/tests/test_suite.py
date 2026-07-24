from pathlib import Path
import subprocess,sys,unittest,yaml
ROOT=Path(__file__).resolve().parents[1]
class SuiteTests(unittest.TestCase):
 def test_handoff(self):
  r=subprocess.run([sys.executable,str(ROOT/'scripts/validate_handoff.py'),str(ROOT/'examples/handoff.yaml')],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stdout+r.stderr)
 def test_method_draft_reports_errors_but_parser_runs(self):
  r=subprocess.run([sys.executable,str(ROOT/'scripts/validate_method_fingerprint.py'),str(ROOT/'templates/method-fingerprint.yaml')],capture_output=True,text=True);self.assertNotEqual(r.returncode,0);self.assertIn('charge',r.stdout)
 def test_router(self):
  r=subprocess.run([sys.executable,str(ROOT/'scripts/route_dft_task.py'),'VASP','surface','adsorption'],capture_output=True,text=True);self.assertEqual(r.returncode,0);self.assertIn('tsao-periodic-dft-materials',r.stdout)
 def test_manifest_paths(self):
  m=yaml.safe_load((ROOT/'manifest.yaml').read_text());
  for p in m['always_load']:self.assertTrue((ROOT/p).exists())
if __name__=='__main__':unittest.main()

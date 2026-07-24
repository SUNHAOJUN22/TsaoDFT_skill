from pathlib import Path
import subprocess,sys,tempfile,unittest,json,yaml
ROOT=Path(__file__).resolve().parents[1];NET=ROOT/'examples/catalysis/network.yaml'
class KineticsDepthTests(unittest.TestCase):
 def test_closure(self):
  r=subprocess.run([sys.executable,str(ROOT/'scripts/check_thermodynamic_closure.py'),str(NET)],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stdout+r.stderr);self.assertIn('expected_reverse_barrier',r.stdout)
 def test_uncertainty(self):
  r=subprocess.run([sys.executable,str(ROOT/'scripts/propagate_barrier_uncertainty.py'),'--barrier','15','--uncertainty','1','--temperature','298.15'],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stdout+r.stderr);d=json.loads(r.stdout);self.assertGreater(d['upper_rate'],d['central_rate'])
 def test_cantera_handoff(self):
  with tempfile.TemporaryDirectory() as td:
   out=Path(td)/'cantera.yaml';r=subprocess.run([sys.executable,str(ROOT/'scripts/export_cantera_handoff.py'),str(NET),'--out',str(out)],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stdout+r.stderr);d=yaml.safe_load(out.read_text());self.assertFalse(d['runnable_cantera_mechanism']);self.assertTrue(d['review_required'])
if __name__=='__main__':unittest.main()

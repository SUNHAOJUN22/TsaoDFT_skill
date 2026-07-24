from pathlib import Path
import subprocess,sys,tempfile,unittest,json
ROOT=Path(__file__).resolve().parents[1];EX=ROOT/'examples/dft-baseline'
class DftMlDepthTests(unittest.TestCase):
 def test_dataset_validation(self):
  r=subprocess.run([sys.executable,str(ROOT/'scripts/validate_dft_dataset.py'),str(EX/'dataset.csv'),'--config',str(EX/'dataset-card.yaml')],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stdout+r.stderr);self.assertIn('method_fingerprints',r.stdout)
 def test_ridge_baseline_and_card(self):
  with tempfile.TemporaryDirectory() as td:
   r=subprocess.run([sys.executable,str(ROOT/'scripts/train_ridge_baseline.py'),str(EX/'dataset.csv'),'--features','descriptor_1,descriptor_2','--target','target','--group','parent_id','--out-dir',td],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stdout+r.stderr)
   card=Path(td)/'model-card.json';self.assertTrue(card.exists());d=json.loads(card.read_text());self.assertIn('test',d['metrics'])
   r2=subprocess.run([sys.executable,str(ROOT/'scripts/validate_model_card.py'),str(card)],capture_output=True,text=True);self.assertEqual(r2.returncode,0,r2.stdout+r2.stderr)
if __name__=='__main__':unittest.main()

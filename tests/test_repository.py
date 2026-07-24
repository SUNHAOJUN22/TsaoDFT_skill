from pathlib import Path
import hashlib,subprocess,sys,unittest,yaml
ROOT=Path(__file__).resolve().parents[1]
SKILLS=['tsao-dft-suite','tsao-dft-researcher','tsao-structure-prep','tsao-periodic-dft-materials','tsao-dft-ml-active-learning','tsao-dft-hpc-provenance','tsao-dft-kinetics-multiscale','tsao-dft-catalysis-profile']
DEMOS=['workflow-architecture','wavefunction-esp-gallery','free-energy-profile','dft-ml-dashboard','periodic-dft-materials','active-learning-loop','hpc-provenance','multiscale-kinetics']
class RepositoryTests(unittest.TestCase):
 def test_required_skills(self):
  for s in SKILLS:
   base=ROOT/'skills'/s;self.assertTrue((base/'SKILL.md').exists());self.assertTrue((base/'catalog.yaml').exists())
 def test_readme_demo_assets(self):
  for stem in DEMOS:
   p=ROOT/f'assets/demo/{stem}.svg';self.assertGreater(p.stat().st_size,800);self.assertIn('SYNTHETIC DEMO',p.read_text())
 def test_demo_regeneration_is_deterministic(self):
  def h():return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'assets/demo').glob('*.svg'))}
  b=h();r=subprocess.run([sys.executable,str(ROOT/'scripts/generate_readme_demos.py')],cwd=ROOT,capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stdout+r.stderr);self.assertEqual(b,h())
 def test_catalog(self):
  r=subprocess.run([sys.executable,str(ROOT/'scripts/validate_catalog.py')],cwd=ROOT,capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stdout+r.stderr)
 def test_installer_dry_run(self):
  r=subprocess.run([sys.executable,str(ROOT/'scripts/install.py'),'--agent','codex','--scope','project','--skill','all','--dry-run','--validate'],cwd=ROOT,capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stdout+r.stderr)
 def test_support_docs_and_plugin(self):
  for rel in ['docs/ENGINE_SUPPORT_MATRIX.md','docs/CAPABILITY_STATUS.yaml','docs/CROSS_SKILL_HANDOFF.md','docs/DFT_VALIDATION_LADDER.md','.codex-plugin/plugin.json']:
   self.assertTrue((ROOT/rel).exists(),rel)
  data=yaml.safe_load((ROOT/'docs/CAPABILITY_STATUS.yaml').read_text());self.assertEqual(data['release'],'0.4.0-alpha.1')
 def test_repo_validator(self):
  r=subprocess.run([sys.executable,str(ROOT/'scripts/validate_repo.py')],cwd=ROOT,capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stdout+r.stderr)
if __name__=='__main__':unittest.main()

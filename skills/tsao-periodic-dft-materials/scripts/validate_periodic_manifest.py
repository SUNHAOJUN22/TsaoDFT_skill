#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
import yaml
ENGINES={'vasp','quantum-espresso','cp2k'}
TASKS={'relax','cell-relax','static','band','dos','charge','surface','adsorption','defect','neb','phonon','elastic','aimd'}
def validate(d):
 e=[]; w=[]
 for k in ['schema_version','project_id','engine','task_type','structure_id','method_fingerprint','convergence','status']:
  if k not in d:e.append(f'missing {k}')
 if d.get('engine') not in ENGINES:e.append('unsupported engine')
 if d.get('task_type') not in TASKS:e.append('unsupported task_type')
 m=d.get('method_fingerprint') or {}
 for k in ['xc','pseudopotential_family','cutoff_policy','kpoint_policy','spin_policy']:
  if m.get(k) in (None,'unknown'): w.append(f'method_fingerprint unresolved: {k}')
 if d.get('task_type') in {'surface','adsorption','defect','neb'} and not d.get('model_review_id'): e.append('surface/defect/path task requires model_review_id')
 if d.get('status')=='accepted' and (e or w): e.append('accepted project has unresolved errors/warnings')
 return e,w
def main():
 ap=argparse.ArgumentParser();ap.add_argument('manifest',type=Path);ap.add_argument('--json',action='store_true');a=ap.parse_args();d=yaml.safe_load(a.manifest.read_text())
 e,w=validate(d);r={'ok':not e,'errors':e,'warnings':w};print(json.dumps(r,indent=2) if a.json else '\n'.join(['PASS' if not e else 'FAIL']+[f'ERROR: {x}' for x in e]+[f'WARN: {x}' for x in w]));raise SystemExit(0 if not e else 1)
if __name__=='__main__':main()

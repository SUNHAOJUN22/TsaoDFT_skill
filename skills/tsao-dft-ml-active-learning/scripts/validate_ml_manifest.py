#!/usr/bin/env python3
import argparse,json
from pathlib import Path
import yaml
def validate(d):
 e=[];w=[]
 for k in ['schema_version','project_id','target','target_unit','sample_unit','dataset_path','group_column','split_policy','preprocessing_fit_scope','model_family','seeds','metrics','status']:
  if k not in d:e.append(f'missing {k}')
 if d.get('preprocessing_fit_scope')!='train_only':e.append('preprocessing must be fit on train_only')
 if d.get('split_policy')=='random' and d.get('sample_unit') in {'parent_structure','molecule','material_family'}:w.append('random split may leak related structures')
 if not isinstance(d.get('seeds'),list) or len(d.get('seeds',[]))<2:w.append('use multiple seeds/folds')
 if d.get('status')=='accepted' and (e or w):e.append('accepted ML project has unresolved validation issues')
 return e,w
ap=argparse.ArgumentParser();ap.add_argument('manifest',type=Path);a=ap.parse_args();d=yaml.safe_load(a.manifest.read_text());e,w=validate(d);print(json.dumps({'ok':not e,'errors':e,'warnings':w},indent=2));raise SystemExit(0 if not e else 1)

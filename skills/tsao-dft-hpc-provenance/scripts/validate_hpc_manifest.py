#!/usr/bin/env python3
import argparse,json
from pathlib import Path
import yaml
ap=argparse.ArgumentParser();ap.add_argument('manifest',type=Path);a=ap.parse_args();d=yaml.safe_load(a.manifest.read_text());e=[];w=[]
for k in ['schema_version','job_id','engine','executable','input','workdir','scheduler','resources','expected_outputs','checkpoint_policy','approval']:
 if k not in d:e.append(f'missing {k}')
r=d.get('resources') or {}
for k in ['nodes','tasks_per_node','cpus_per_task','memory_gb','walltime']:
 if k not in r:e.append(f'resources missing {k}')
if d.get('scheduler') not in {'local','slurm','pbs'}:e.append('unsupported scheduler')
if d.get('approval')=='approved' and e:e.append('approved manifest has validation errors')
print(json.dumps({'ok':not e,'errors':e,'warnings':w},indent=2));raise SystemExit(0 if not e else 1)

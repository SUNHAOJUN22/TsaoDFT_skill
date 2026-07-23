#!/usr/bin/env python3
import argparse,json
from pathlib import Path
import yaml
ap=argparse.ArgumentParser();ap.add_argument('profile',type=Path);a=ap.parse_args();d=yaml.safe_load(a.profile.read_text());e=[]
for k in ['profile_id','scope','allowed_systems','forbidden_default_claims','requires']:
 if k not in d:e.append(f'missing {k}')
if 'tsao-dft-researcher' not in (d.get('requires') or []):e.append('core skill requirement missing')
print(json.dumps({'ok':not e,'errors':e},indent=2));raise SystemExit(0 if not e else 1)

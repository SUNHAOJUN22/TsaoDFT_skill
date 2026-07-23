#!/usr/bin/env python3
import argparse,json
from pathlib import Path
import yaml
ap=argparse.ArgumentParser();ap.add_argument('network',type=Path);a=ap.parse_args();d=yaml.safe_load(a.network.read_text());e=[];w=[]
for k in ['schema_version','network_id','temperature_K','standard_state','species','reactions','status']:
 if k not in d:e.append(f'missing {k}')
ids=[s.get('id') for s in d.get('species',[])];
if len(ids)!=len(set(ids)):e.append('duplicate species ids')
for rxn in d.get('reactions',[]):
 for side in ['reactants','products']:
  for sid in (rxn.get(side) or {}):
   if sid not in ids:e.append(f'reaction references unknown species {sid}')
 if rxn.get('reversible') and not (rxn.get('forward_barrier') is not None and rxn.get('reaction_free_energy') is not None):w.append(f"reversible reaction {rxn.get('id')} lacks closure data")
print(json.dumps({'ok':not e,'errors':e,'warnings':w},indent=2));raise SystemExit(0 if not e else 1)

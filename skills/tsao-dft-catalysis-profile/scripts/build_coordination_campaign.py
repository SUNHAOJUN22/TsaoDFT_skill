#!/usr/bin/env python3
"""Expand a finite organometallic/polyolefin-catalysis DFT candidate matrix."""
from __future__ import annotations
import argparse,csv,itertools,json
from pathlib import Path
import yaml
REQUIRED_AXES=['substrate_or_additive','catalyst_model','coordination_mode','conformer','charge','multiplicity']
def main()->int:
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('campaign',type=Path);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();d=yaml.safe_load(a.campaign.read_text()) or {};axes=d.get('axes') or {};missing=[k for k in REQUIRED_AXES if not axes.get(k)]
    if missing:print(json.dumps({'ok':False,'errors':[f'missing/nonempty axes: {missing}']},indent=2));return 1
    names=list(axes);exclusions=set(d.get('exclusions') or []);rows=[]
    for combo in itertools.product(*(axes[n] for n in names)):
        row=dict(zip(names,combo));key='|'.join(f'{k}={row[k]}' for k in names)
        if key in exclusions:continue
        rows.append({'candidate_id':f"{d.get('campaign_id','CAT')}-{len(rows)+1:04d}",**row,'structure_review_status':'pending','dft_status':'planned','claim_scope':'coordination_tendency_only'})
    limit=int(d.get('max_candidates',0) or 0)
    if limit and len(rows)>limit:print(json.dumps({'ok':False,'errors':[f'campaign expands to {len(rows)} > max_candidates {limit}']},indent=2));return 2
    a.out.parent.mkdir(parents=True,exist_ok=True)
    with a.out.open('w',newline='',encoding='utf-8') as f:
        fields=list(rows[0]) if rows else ['candidate_id'];w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    print(json.dumps({'ok':True,'candidate_count':len(rows),'out':str(a.out)},indent=2));return 0
if __name__=='__main__':raise SystemExit(main())

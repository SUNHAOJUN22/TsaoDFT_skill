#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,itertools
from pathlib import Path
import yaml
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('campaign',type=Path); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    d=yaml.safe_load(a.campaign.read_text(encoding='utf-8')); axes=d.get('axes') or {}
    names=list(axes); values=[axes[n] for n in names]
    rows=[]
    for combo in itertools.product(*values):
        row=dict(zip(names,combo)); key='|'.join(f'{k}={row[k]}' for k in names)
        if key in set(d.get('exclusions') or []): continue
        rows.append({'candidate_id':f"{d.get('campaign_id','CAMP')}-{len(rows)+1:04d}",**row})
    limit=int(d.get('max_candidates',len(rows)))
    if len(rows)>limit: raise SystemExit(f'campaign expands to {len(rows)} > max_candidates {limit}')
    a.out.parent.mkdir(parents=True,exist_ok=True)
    with a.out.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=['candidate_id']+names); w.writeheader(); w.writerows(rows)
    print(f'wrote {len(rows)} candidates to {a.out}')
if __name__=='__main__': main()

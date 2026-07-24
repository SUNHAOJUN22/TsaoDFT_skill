#!/usr/bin/env python3
"""Validate a DFT-labelled ML dataset for identity, fidelity and leakage risks."""
from __future__ import annotations
import argparse,csv,hashlib,json,math
from pathlib import Path
import yaml

def load_rows(path:Path):
    with path.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))

def validate(rows:list[dict],cfg:dict)->tuple[list[str],list[str],dict]:
    e=[];w=[]
    cols=cfg.get('columns') or {};sid=cols.get('sample_id','sample_id');parent=cols.get('parent_id','parent_id');target=cols.get('target','target');fp=cols.get('method_fingerprint','method_fingerprint');fidelity=cols.get('fidelity','fidelity');split=cols.get('split','split')
    if not rows:e.append('dataset is empty');return e,w,{}
    fields=set(rows[0])
    for k in [sid,parent,target]:
        if k not in fields:e.append(f'missing required column {k}')
    ids=[r.get(sid) for r in rows]
    if len(ids)!=len(set(ids)):e.append('duplicate sample IDs')
    missing_parent=[i+2 for i,r in enumerate(rows) if not r.get(parent)]
    if missing_parent:e.append(f'missing parent IDs at rows {missing_parent[:10]}')
    invalid_target=[]
    for i,r in enumerate(rows):
        try:v=float(r.get(target,''));
        except (TypeError,ValueError):invalid_target.append(i+2);continue
        if not math.isfinite(v):invalid_target.append(i+2)
    if invalid_target:e.append(f'invalid target values at rows {invalid_target[:10]}')
    fps={r.get(fp) for r in rows if r.get(fp)} if fp in fields else set()
    fidelities={r.get(fidelity) for r in rows if r.get(fidelity)} if fidelity in fields else set()
    if fp not in fields:w.append('method_fingerprint column absent; DFT label provenance cannot be checked row-wise')
    elif len(fps)>1 and not cfg.get('mixed_method_policy'):e.append(f'multiple method fingerprints without mixed_method_policy: {sorted(fps)}')
    if fidelity not in fields:w.append('fidelity column absent')
    elif len(fidelities)>1 and not cfg.get('mixed_fidelity_policy'):e.append(f'multiple fidelities without mixed_fidelity_policy: {sorted(fidelities)}')
    # exact duplicate feature/target records excluding IDs/split; warn because repeated DFT jobs are not independent
    ignore={sid,parent,split}
    signatures={}
    for i,r in enumerate(rows):
        sig=tuple((k,r.get(k,'')) for k in sorted(fields-ignore))
        signatures.setdefault(sig,[]).append(i+2)
    duplicates=[v for v in signatures.values() if len(v)>1]
    if duplicates:w.append(f'exact duplicate non-ID records: {duplicates[:5]}')
    # split leakage
    leakage=[]
    if split in fields:
        group_splits={}
        for r in rows:group_splits.setdefault(r.get(parent),set()).add(r.get(split))
        leakage=[(g,sorted(x)) for g,x in group_splits.items() if len(x-{None,''})>1]
        if leakage:e.append(f'parent/group leakage across splits: {leakage[:10]}')
    else:w.append('split column absent; run grouped split before modelling')
    summary={'row_count':len(rows),'parent_count':len({r.get(parent) for r in rows}),'method_fingerprints':sorted(fps),'fidelities':sorted(fidelities),'dataset_sha256':hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest(),'leakage_groups':leakage}
    return e,w,summary

def main()->int:
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('dataset',type=Path);ap.add_argument('--config',type=Path);a=ap.parse_args();cfg=yaml.safe_load(a.config.read_text()) if a.config else {};rows=load_rows(a.dataset);e,w,s=validate(rows,cfg or {});print(json.dumps({'ok':not e,'errors':e,'warnings':w,'summary':s},indent=2));return 0 if not e else 1
if __name__=='__main__':raise SystemExit(main())

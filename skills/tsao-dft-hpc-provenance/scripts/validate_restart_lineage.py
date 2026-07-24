#!/usr/bin/env python3
"""Validate restart/checkpoint lineage and method compatibility."""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
import yaml
SHA=re.compile(r'^[0-9a-f]{64}$')

def validate(d):
    e=[];w=[]
    for k in ['schema_version','lineage_id','engine','parent_run_id','child_run_id','parent_checkpoint','parent_method_fingerprint','child_method_fingerprint','restart_mode','changes','status']:
        if k not in d:e.append(f'missing {k}')
    cp=d.get('parent_checkpoint') or {}
    if not SHA.match(str(cp.get('sha256',''))):e.append('parent checkpoint sha256 invalid')
    same=d.get('parent_method_fingerprint')==d.get('child_method_fingerprint')
    mode=d.get('restart_mode')
    if mode=='exact_restart' and not same:e.append('exact_restart requires identical method fingerprints')
    if mode not in {'exact_restart','geometry_reuse','wavefunction_guess_reuse','new_lineage'}:e.append('invalid restart_mode')
    changes=d.get('changes') or []
    if changes and mode=='exact_restart':e.append('exact_restart cannot declare scientific/numerical changes')
    if mode in {'geometry_reuse','wavefunction_guess_reuse'}:w.append('reuse is not an exact restart; child is a distinct run and must be preflighted')
    if d.get('status')=='accepted' and (e or w):e.append('accepted lineage has unresolved errors/warnings')
    return e,w

def main()->int:
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('lineage',type=Path);a=ap.parse_args();d=yaml.safe_load(a.lineage.read_text()) or {};e,w=validate(d);print(json.dumps({'ok':not e,'errors':e,'warnings':w},indent=2));return 0 if not e else 1
if __name__=='__main__':raise SystemExit(main())

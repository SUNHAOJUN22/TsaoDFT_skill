#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import yaml
ALLOWED={'molecule','complex','crystal','slab','interface','defect','adsorbate','ensemble'}
def validate(data, base):
    e=[]; w=[]
    for k in ['schema_version','structure_id','model_type','source','length_unit','periodicity','review']:
        if k not in data: e.append(f'missing {k}')
    if data.get('model_type') not in ALLOWED: e.append('unsupported model_type')
    src=data.get('source') or {}; path=src.get('path')
    if path and path!='unknown':
        p=(base/path).resolve() if not Path(path).is_absolute() else Path(path)
        if not p.exists(): w.append(f'source file not found: {p}')
        elif src.get('sha256') not in (None,'unknown'):
            h=hashlib.sha256(p.read_bytes()).hexdigest()
            if h!=src['sha256']: e.append('source sha256 mismatch')
    for key in ['charge_candidates','multiplicity_candidates']:
        vals=data.get(key)
        if not isinstance(vals,list) or not vals: e.append(f'{key} must be nonempty list')
    if data.get('model_type') in {'slab','interface','defect','adsorbate'}:
        periodic=data.get('periodic_model') or {}
        for k in ['cell','vacuum_angstrom','periodic_image_separation_angstrom']:
            if k not in periodic: e.append(f'periodic_model missing {k}')
    if (data.get('review') or {}).get('status')=='accepted' and e: e.append('accepted structure has unresolved validation errors')
    return e,w
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('manifest',type=Path); ap.add_argument('--json',action='store_true'); a=ap.parse_args()
    d=yaml.safe_load(a.manifest.read_text(encoding='utf-8'))
    e,w=validate(d,a.manifest.parent); result={'ok':not e,'errors':e,'warnings':w}
    print(json.dumps(result,ensure_ascii=False,indent=2) if a.json else '\n'.join(['PASS' if not e else 'FAIL']+[f'ERROR: {x}' for x in e]+[f'WARN: {x}' for x in w]))
    raise SystemExit(0 if not e else 1)
if __name__=='__main__': main()

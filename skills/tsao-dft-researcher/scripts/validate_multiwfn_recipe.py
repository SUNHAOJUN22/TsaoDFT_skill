#!/usr/bin/env python3
"""Validate semantic Multiwfn analysis recipes before menu-script execution."""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
import yaml
ANALYSES={'orbital','nto','esp_surface','fukui','population','spin_density','nbo_handoff','iri','igmh','nci','qtaim','elf','lol','icss','spectrum'}
SHA=re.compile(r'^[0-9a-f]{64}$')

def validate(d:dict)->tuple[list[str],list[str]]:
    e=[];w=[]
    for k in ['schema_version','recipe_id','analysis_type','multiwfn_version','input_file','input_sha256','upstream_method_fingerprint','semantic_steps','parameters','expected_outputs','status']:
        if k not in d:e.append(f'missing {k}')
    if d.get('analysis_type') not in ANALYSES:e.append('unsupported analysis_type')
    if not SHA.match(str(d.get('input_sha256',''))):e.append('invalid input_sha256')
    if not d.get('semantic_steps'):e.append('semantic_steps must not be empty')
    p=d.get('parameters') or {};a=d.get('analysis_type')
    if a in {'orbital','nto','spin_density'} and p.get('isovalue_au') is None:e.append('isosurface analysis requires isovalue_au')
    if a=='esp_surface':
        for k in ['density_isovalue_au','esp_min','esp_max','unit']:
            if p.get(k) is None:e.append(f'esp_surface missing {k}')
        if p.get('esp_min') is not None and p.get('esp_max') is not None and abs(float(p['esp_min'])+float(p['esp_max']))>1e-9:w.append('ESP range is not symmetric; comparison figures require a documented reason')
    if a=='igmh' and not p.get('fragments'):e.append('IGMH requires explicit fragments')
    if a=='icss' and not p.get('probe_definition'):e.append('ICSS requires probe_definition')
    if d.get('raw_menu_script') and d.get('multiwfn_version') in (None,'unknown'):e.append('raw menu script requires recorded Multiwfn version')
    if d.get('status')=='accepted' and (e or w):e.append('accepted recipe has unresolved errors/warnings')
    return e,w

def main()->int:
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('recipe',type=Path);a=ap.parse_args();d=yaml.safe_load(a.recipe.read_text()) or {};e,w=validate(d);print(json.dumps({'ok':not e,'errors':e,'warnings':w},indent=2));return 0 if not e else 1
if __name__=='__main__':raise SystemExit(main())

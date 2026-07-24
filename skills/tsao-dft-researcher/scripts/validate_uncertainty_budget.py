#!/usr/bin/env python3
"""Validate a DFT uncertainty/sensitivity budget."""
from __future__ import annotations
import argparse,json,math
from pathlib import Path
import yaml
ALLOWED={'conformer','method','basis','dispersion','solvent','standard_state','low_frequency','spin_state','numerical','model_truncation','sampling','reference_state','other'}

def validate(d:dict)->tuple[list[str],list[str],dict]:
    e=[];w=[]
    for k in ['schema_version','project_id','observable','unit','components','combination_rule','status']:
        if k not in d:e.append(f'missing {k}')
    comps=d.get('components') or [];vals=[]
    if not comps:w.append('no uncertainty components declared')
    for i,c in enumerate(comps):
        if c.get('type') not in ALLOWED:e.append(f'components[{i}] invalid type')
        try:
            value=float(c.get('magnitude'))
            if value<0:e.append(f'components[{i}] magnitude must be nonnegative')
            vals.append(value)
        except (TypeError,ValueError):e.append(f'components[{i}] magnitude must be numeric')
        if not c.get('basis'):w.append(f'components[{i}] has no evidence/basis')
    rule=d.get('combination_rule');combined=None
    if vals:
        if rule=='root_sum_square':combined=math.sqrt(sum(v*v for v in vals))
        elif rule=='sum_bounds':combined=sum(vals)
        elif rule=='report_separately':combined=None
        else:e.append('invalid combination_rule')
    if d.get('status')=='accepted' and (e or w):e.append('accepted uncertainty budget has unresolved errors/warnings')
    return e,w,{'combined_magnitude':combined,'unit':d.get('unit')}

def main()->int:
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('budget',type=Path);a=ap.parse_args();d=yaml.safe_load(a.budget.read_text()) or {};e,w,s=validate(d);print(json.dumps({'ok':not e,'errors':e,'warnings':w,'summary':s},indent=2));return 0 if not e else 1
if __name__=='__main__':raise SystemExit(main())

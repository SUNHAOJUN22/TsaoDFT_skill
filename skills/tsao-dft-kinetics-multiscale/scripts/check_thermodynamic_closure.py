#!/usr/bin/env python3
"""Check forward/reverse barrier thermodynamic closure: ΔG‡rev = ΔG‡fwd - ΔGrxn."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import yaml

def main()->int:
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('network',type=Path);ap.add_argument('--tolerance',type=float,default=0.05);a=ap.parse_args();d=yaml.safe_load(a.network.read_text()) or {};e=[];rows=[]
    for rxn in d.get('reactions',[]):
        if not rxn.get('reversible'):continue
        rid=rxn.get('id');f=rxn.get('forward_barrier');g=rxn.get('reaction_free_energy');r=rxn.get('reverse_barrier')
        if f is None or g is None:e.append(f'{rid} lacks forward barrier/reaction free energy');continue
        expected=float(f)-float(g);delta=None
        if r is not None:
            delta=float(r)-expected
            if abs(delta)>a.tolerance:e.append(f'{rid} closure error {delta:.6g} exceeds {a.tolerance}')
        rows.append({'reaction_id':rid,'expected_reverse_barrier':expected,'reported_reverse_barrier':r,'closure_error':delta})
    print(json.dumps({'ok':not e,'errors':e,'reactions':rows,'unit':d.get('energy_unit')},indent=2));return 0 if not e else 1
if __name__=='__main__':raise SystemExit(main())

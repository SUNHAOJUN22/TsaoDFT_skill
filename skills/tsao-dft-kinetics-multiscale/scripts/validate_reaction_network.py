#!/usr/bin/env python3
"""Validate DFT-derived reaction-network identities, balances and thermodynamic data."""
from __future__ import annotations
import argparse,json,math
from pathlib import Path
import yaml

def side_balance(side:dict,species:dict,key:str)->dict:
    out={}
    for sid,coef in (side or {}).items():
        val=species[sid].get(key,{} if key=='composition' else 0)
        if isinstance(val,dict):
            for el,n in val.items():out[el]=out.get(el,0)+float(coef)*float(n)
        else:out[key]=out.get(key,0)+float(coef)*float(val)
    return out

def validate(d):
    e=[];w=[]
    for k in ['schema_version','network_id','temperature_K','phase_model','standard_state','energy_unit','species','reactions','status']:
        if k not in d:e.append(f'missing {k}')
    try:
        if float(d.get('temperature_K',0))<=0:e.append('temperature_K must be positive')
    except (TypeError,ValueError):e.append('temperature_K must be numeric')
    ids=[s.get('id') for s in d.get('species',[])];
    if len(ids)!=len(set(ids)):e.append('duplicate species ids')
    sp={s.get('id'):s for s in d.get('species',[]) if s.get('id')}
    for i,s in enumerate(d.get('species',[])):
        for k in ['id','composition','charge','phase','free_energy','artifact_id','method_fingerprint_id','acceptance_status']:
            if k not in s:e.append(f'species[{i}] missing {k}')
        if s.get('acceptance_status')!='accepted':w.append(f"species {s.get('id')} is not accepted DFT evidence")
    reaction_ids=[]
    for rxn in d.get('reactions',[]):
        rid=rxn.get('id');reaction_ids.append(rid)
        for side in ['reactants','products']:
            if not rxn.get(side):e.append(f'{rid} missing {side}')
            for sid,coef in (rxn.get(side) or {}).items():
                if sid not in sp:e.append(f'{rid} references unknown species {sid}')
                try:
                    if float(coef)<=0:e.append(f'{rid} nonpositive stoichiometric coefficient')
                except (TypeError,ValueError):e.append(f'{rid} invalid coefficient for {sid}')
        if all(sid in sp for side in ['reactants','products'] for sid in (rxn.get(side) or {})):
            for key,label in [('composition','element'),('charge','charge'),('site_occupancy','site')]:
                left=side_balance(rxn.get('reactants'),sp,key);right=side_balance(rxn.get('products'),sp,key)
                allkeys=set(left)|set(right)
                diff={k:right.get(k,0)-left.get(k,0) for k in allkeys if abs(right.get(k,0)-left.get(k,0))>1e-9}
                if diff:e.append(f'{rid} violates {label} balance: {diff}')
        if rxn.get('forward_barrier') is None:e.append(f'{rid} missing forward_barrier')
        if rxn.get('reversible') and rxn.get('reaction_free_energy') is None:e.append(f'{rid} reversible but missing reaction_free_energy')
        if rxn.get('reversible') and rxn.get('reverse_barrier') is None:w.append(f'{rid} reverse_barrier will need thermodynamic closure derivation')
        if rxn.get('path_degeneracy',1)<=0:e.append(f'{rid} path_degeneracy must be positive')
        if not rxn.get('transition_state_artifact_id'):w.append(f'{rid} transition-state artifact not linked')
    if len(reaction_ids)!=len(set(reaction_ids)):e.append('duplicate reaction ids')
    if d.get('status')=='accepted' and (e or w):e.append('accepted network has unresolved errors/warnings')
    return e,w

def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument('network',type=Path);a=ap.parse_args();d=yaml.safe_load(a.network.read_text()) or {};e,w=validate(d);print(json.dumps({'ok':not e,'errors':e,'warnings':w},indent=2));return 0 if not e else 1
if __name__=='__main__':raise SystemExit(main())

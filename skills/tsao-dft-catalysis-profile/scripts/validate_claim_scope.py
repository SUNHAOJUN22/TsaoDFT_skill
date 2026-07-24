#!/usr/bin/env python3
"""Validate claim scope for the optional polyolefin-catalysis DFT profile."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import yaml
LEVELS={'coordination_tendency','relative_binding_preference','elementary_step_mechanism','poisoning_hypothesis','catalyst_poisoning','industrial_performance'}
REQUIREMENTS={
 'coordination_tendency':{'accepted_dft'},
 'relative_binding_preference':{'accepted_dft','common_reference_state','conformer_spin_scope'},
 'elementary_step_mechanism':{'accepted_dft','confirmed_ts','irc_endpoints','alternative_paths'},
 'poisoning_hypothesis':{'accepted_dft','kinetic_context','competitive_species'},
 'catalyst_poisoning':{'accepted_dft','kinetic_context','competitive_species','experimental_validation'},
 'industrial_performance':{'accepted_dft','kinetic_context','experimental_validation','process_conditions','transport_or_reactor_model'},
}
def validate(d):
    e=[];w=[]
    for k in ['claim_id','claim_level','text','system_scope','evidence','limitations','status']:
        if k not in d:e.append(f'missing {k}')
    level=d.get('claim_level')
    if level not in LEVELS:e.append('invalid claim_level');return e,w
    evidence=set(d.get('evidence') or []);missing=REQUIREMENTS[level]-evidence
    if missing:e.append(f'{level} missing evidence: {sorted(missing)}')
    if level in {'catalyst_poisoning','industrial_performance'}:w.append('strong claim requires external experimental/process evidence; isolated DFT is insufficient')
    if level=='poisoning_hypothesis' and 'experimental_validation' not in evidence:w.append('label explicitly as hypothesis, not established poisoning')
    if d.get('status')=='accepted' and (e or w):e.append('accepted claim has unresolved errors/warnings')
    return e,w

def main()->int:
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('claim',type=Path);a=ap.parse_args();d=yaml.safe_load(a.claim.read_text()) or {};e,w=validate(d);print(json.dumps({'ok':not e,'errors':e,'warnings':w},indent=2));return 0 if not e else 1
if __name__=='__main__':raise SystemExit(main())

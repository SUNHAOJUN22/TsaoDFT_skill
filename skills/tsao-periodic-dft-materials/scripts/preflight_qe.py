#!/usr/bin/env python3
"""Preflight a Quantum ESPRESSO pw.x input."""
from __future__ import annotations
import argparse,json,re
from pathlib import Path

def parse(text:str)->dict:
    n={};
    for block in re.finditer(r'&(\w+)(.*?)\n\s*/',text,re.S):
        sec=block.group(1).lower();vals={}
        for m in re.finditer(r'(\w+)\s*=\s*([^,\n/]+)',block.group(2)):vals[m.group(1).lower()]=m.group(2).strip().strip("'\"")
        n[sec]=vals
    species=[];m=re.search(r'ATOMIC_SPECIES\s*\n(.*?)(?=\n\s*(?:ATOMIC_POSITIONS|CELL_PARAMETERS|K_POINTS|CONSTRAINTS|OCCUPATIONS|$))',text,re.S|re.I)
    if m:
        for line in m.group(1).splitlines():
            p=line.split();
            if len(p)>=3:species.append({'element':p[0],'mass':p[1],'pseudopotential':p[2]})
    cards={k:bool(re.search(r'^\s*'+k+r'\b',text,re.M|re.I)) for k in ['ATOMIC_POSITIONS','CELL_PARAMETERS','K_POINTS']}
    return {'namelists':n,'species':species,'cards':cards}

def validate(d:dict)->tuple[list[str],list[str]]:
    e=[];w=[];control=d['namelists'].get('control',{});system=d['namelists'].get('system',{});elect=d['namelists'].get('electrons',{})
    for sec in ['control','system','electrons']:
        if sec not in d['namelists']:e.append(f'missing &{sec.upper()}')
    for key in ['calculation','prefix','outdir','pseudo_dir']:
        if key not in control:w.append(f'CONTROL missing explicit {key}')
    for key in ['nat','ntyp','ecutwfc']:
        if key not in system:e.append(f'SYSTEM missing {key}')
    if system.get('ntyp'):
        try:
            if int(float(system['ntyp']))!=len(d['species']):e.append('ntyp does not equal ATOMIC_SPECIES entries')
        except ValueError:e.append('ntyp is not numeric')
    if not d['cards']['ATOMIC_POSITIONS']:e.append('missing ATOMIC_POSITIONS')
    ibrav=system.get('ibrav')
    if ibrav in ('0','0.0') and not d['cards']['CELL_PARAMETERS']:e.append('ibrav=0 requires CELL_PARAMETERS')
    if 'ecutrho' not in system:w.append('ecutrho not explicit; ratio must match pseudopotential type')
    if not d['cards']['K_POINTS']:w.append('K_POINTS absent; Gamma-only intent must be explicit')
    if system.get('nspin')=='2' and not any(k.startswith('starting_magnetization') for k in system):w.append('nspin=2 without starting_magnetization')
    if not d['species']:e.append('no ATOMIC_SPECIES entries')
    return e,w

def main()->int:
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('input',type=Path);a=ap.parse_args();d=parse(a.input.read_text(encoding='utf-8',errors='replace'));e,w=validate(d);print(json.dumps({'ok':not e,'errors':e,'warnings':w,'parsed':d},indent=2));return 0 if not e else 1
if __name__=='__main__':raise SystemExit(main())

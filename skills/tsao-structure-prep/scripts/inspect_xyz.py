#!/usr/bin/env python3
"""Inspect an XYZ geometry for deterministic structural red flags.

This script does not assign bond orders, charge, multiplicity, protonation, or oxidation states.
"""
from __future__ import annotations
import argparse,json,math,re
from pathlib import Path

COVALENT={
'H':0.31,'B':0.85,'C':0.76,'N':0.71,'O':0.66,'F':0.57,'Si':1.11,'P':1.07,'S':1.05,'Cl':1.02,
'Ti':1.60,'Cr':1.39,'Mn':1.39,'Fe':1.32,'Co':1.26,'Ni':1.24,'Cu':1.32,'Zn':1.22,'Br':1.20,'I':1.39,
'Zr':1.75,'Mo':1.54,'Ru':1.46,'Rh':1.42,'Pd':1.39,'Ag':1.45,'Cd':1.44,'Pt':1.36,'Au':1.36
}
VALID=re.compile(r'^[A-Z][a-z]?$')

def parse_xyz(path:Path)->tuple[str,list[dict]]:
    lines=path.read_text(encoding='utf-8',errors='replace').splitlines()
    if not lines:raise ValueError('empty XYZ')
    try:n=int(lines[0].strip())
    except ValueError:raise ValueError('first line must be atom count')
    if len(lines)<n+2:raise ValueError(f'expected {n} atoms but file has fewer lines')
    atoms=[]
    for i,line in enumerate(lines[2:2+n],1):
        p=line.split()
        if len(p)<4:raise ValueError(f'atom line {i} has fewer than 4 fields')
        el=p[0].capitalize()
        if not VALID.match(el):raise ValueError(f'invalid element token {p[0]} at atom {i}')
        try:x,y,z=map(float,p[1:4])
        except ValueError:raise ValueError(f'non-numeric coordinate at atom {i}')
        atoms.append({'index':i,'element':el,'x':x,'y':y,'z':z})
    return lines[1] if len(lines)>1 else '',atoms

def distance(a,b):return math.dist((a['x'],a['y'],a['z']),(b['x'],b['y'],b['z']))

def inspect(atoms:list[dict],clash_scale:float=0.55,bond_scale:float=1.25)->dict:
    errors=[];warnings=[];pairs=[];bonds=[]
    if not atoms:errors.append('no atoms')
    for i,a in enumerate(atoms):
        if a['element'] not in COVALENT:warnings.append(f"no covalent radius for {a['element']}; pair heuristics incomplete")
        for b in atoms[i+1:]:
            d=distance(a,b);pairs.append(d)
            ra=COVALENT.get(a['element']);rb=COVALENT.get(b['element'])
            if d<1e-6:errors.append(f"duplicate coordinates: atoms {a['index']} and {b['index']}")
            if ra and rb:
                ref=ra+rb
                if d<clash_scale*ref:errors.append(f"severe contact {a['index']}-{b['index']}: {d:.3f} Å")
                if d<=bond_scale*ref:bonds.append({'i':a['index'],'j':b['index'],'distance_angstrom':round(d,6),'heuristic_only':True})
    degree={a['index']:0 for a in atoms}
    for b in bonds:degree[b['i']]+=1;degree[b['j']]+=1
    isolated=[i for i,v in degree.items() if v==0]
    if isolated:warnings.append(f'heuristically isolated atoms: {isolated}; review fragments/coordination')
    centroid={k:sum(a[k] for a in atoms)/len(atoms) for k in ['x','y','z']} if atoms else {}
    span={axis:max(a[axis] for a in atoms)-min(a[axis] for a in atoms) for axis in ['x','y','z']} if atoms else {}
    return {'ok':not errors,'errors':errors,'warnings':sorted(set(warnings)),'atom_count':len(atoms),'elements':{e:sum(a['element']==e for a in atoms) for e in sorted({a['element'] for a in atoms})},'centroid_angstrom':centroid,'span_angstrom':span,'minimum_pair_distance_angstrom':min(pairs) if pairs else None,'heuristic_bonds':bonds,'note':'Bond list is a geometry heuristic, not electronic-structure evidence.'}

def main()->int:
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('xyz',type=Path);ap.add_argument('--json',action='store_true');ap.add_argument('--out',type=Path);a=ap.parse_args()
    try:comment,atoms=parse_xyz(a.xyz);r=inspect(atoms);r['comment']=comment;r['source']=str(a.xyz.resolve())
    except Exception as exc:r={'ok':False,'errors':[str(exc)],'warnings':[],'source':str(a.xyz.resolve())}
    text=json.dumps(r,ensure_ascii=False,indent=2)
    if a.out:a.out.write_text(text,encoding='utf-8')
    print(text if a.json or True else ('PASS' if r['ok'] else 'FAIL'))
    return 0 if r['ok'] else 1
if __name__=='__main__':raise SystemExit(main())

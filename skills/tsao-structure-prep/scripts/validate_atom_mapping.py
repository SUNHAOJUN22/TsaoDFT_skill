#!/usr/bin/env python3
"""Validate atom ordering/mapping between two XYZ structures."""
from __future__ import annotations
import argparse,json,math
from pathlib import Path
from inspect_xyz import parse_xyz

def validate(a:list[dict],b:list[dict],mapping:list[int]|None=None)->tuple[list[str],list[str],dict]:
    e=[];w=[]
    if len(a)!=len(b):e.append(f'atom count differs: {len(a)} vs {len(b)}');return e,w,{}
    n=len(a);mapping=mapping or list(range(1,n+1))
    if len(mapping)!=n or sorted(mapping)!=list(range(1,n+1)):e.append('mapping must be a 1-based permutation');return e,w,{}
    sq=0.0;maxd=0.0;element_mismatch=[]
    for i,j1 in enumerate(mapping):
        aa=a[i];bb=b[j1-1]
        if aa['element']!=bb['element']:element_mismatch.append((i+1,j1,aa['element'],bb['element']))
        d=math.dist((aa['x'],aa['y'],aa['z']),(bb['x'],bb['y'],bb['z']));sq+=d*d;maxd=max(maxd,d)
    if element_mismatch:e.append(f'element mismatches: {element_mismatch}')
    rmsd=math.sqrt(sq/n) if n else 0.0
    if rmsd>2.0:w.append('large raw-coordinate RMSD; alignment was not performed')
    return e,w,{'atom_count':n,'raw_rmsd_angstrom':rmsd,'max_displacement_angstrom':maxd,'mapping':mapping,'note':'RMSD uses provided coordinates without rotation/translation alignment.'}

def main()->int:
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('reference',type=Path);ap.add_argument('candidate',type=Path);ap.add_argument('--mapping',help='comma-separated 1-based candidate indices');a=ap.parse_args()
    _,aa=parse_xyz(a.reference);_,bb=parse_xyz(a.candidate);mapping=[int(x) for x in a.mapping.split(',')] if a.mapping else None;e,w,s=validate(aa,bb,mapping);print(json.dumps({'ok':not e,'errors':e,'warnings':w,'summary':s},indent=2));return 0 if not e else 1
if __name__=='__main__':raise SystemExit(main())

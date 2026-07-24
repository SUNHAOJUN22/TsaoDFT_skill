#!/usr/bin/env python3
"""Validate activation scope and dependencies of the catalysis profile."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import yaml

def validate(d):
    e=[];w=[]
    for k in ['profile_id','scope','allowed_systems','activation_terms','forbidden_default_claims','requires','dft_center','status']:
        if k not in d:e.append(f'missing {k}')
    req=set(d.get('requires') or [])
    for skill in ['tsao-dft-suite','tsao-dft-researcher','tsao-structure-prep','tsao-dft-kinetics-multiscale']:
        if skill not in req:e.append(f'required Skill missing: {skill}')
    if d.get('dft_center') is not True:e.append('profile must declare dft_center: true')
    if not d.get('activation_terms'):e.append('activation_terms must not be empty')
    if 'industrial_poisoning' not in (d.get('forbidden_default_claims') or []):w.append('industrial poisoning should remain a forbidden default claim')
    if d.get('status')=='accepted' and (e or w):e.append('accepted profile has unresolved errors/warnings')
    return e,w

def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument('profile',type=Path);a=ap.parse_args();d=yaml.safe_load(a.profile.read_text()) or {};e,w=validate(d);print(json.dumps({'ok':not e,'errors':e,'warnings':w},indent=2));return 0 if not e else 1
if __name__=='__main__':raise SystemExit(main())

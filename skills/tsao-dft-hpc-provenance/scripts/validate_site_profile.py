#!/usr/bin/env python3
"""Validate a private/public HPC site profile without exposing secrets."""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
import yaml
SCHED={'local','slurm','pbs'}

def validate(d):
    e=[];w=[]
    for k in ['schema_version','site_id','scheduler','execution_host_scope','software','scratch','resource_limits','security','status']:
        if k not in d:e.append(f'missing {k}')
    if d.get('scheduler') not in SCHED:e.append('unsupported scheduler')
    software=d.get('software') or {}
    for engine,rec in software.items():
        if not isinstance(rec,dict):e.append(f'software.{engine} must be mapping');continue
        for k in ['executable','version_policy','module_or_environment']:
            if rec.get(k) in (None,'unknown'):w.append(f'software.{engine} unresolved {k}')
    sec=d.get('security') or {}
    if sec.get('contains_credentials') is True:e.append('site profile must not contain credentials')
    text=json.dumps(d)
    if re.search(r'(token|password|secret)\s*[=:]\s*["\']?[^"\',}\s]+',text,re.I):e.append('possible credential literal detected')
    limits=d.get('resource_limits') or {}
    for k in ['max_nodes','max_walltime','max_memory_gb_per_node']:
        if k not in limits:w.append(f'resource_limits missing {k}')
    if d.get('status')=='accepted' and (e or w):e.append('accepted site profile has unresolved errors/warnings')
    return e,w

def main()->int:
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('profile',type=Path);a=ap.parse_args();d=yaml.safe_load(a.profile.read_text()) or {};e,w=validate(d);print(json.dumps({'ok':not e,'errors':e,'warnings':w},indent=2));return 0 if not e else 1
if __name__=='__main__':raise SystemExit(main())

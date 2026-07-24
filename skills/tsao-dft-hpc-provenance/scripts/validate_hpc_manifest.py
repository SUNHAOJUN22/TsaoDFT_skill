#!/usr/bin/env python3
"""Validate an engine-aware HPC execution manifest."""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
import yaml
ENGINES={'gaussian','vasp','quantum-espresso','cp2k','generic'};SCHED={'local','slurm','pbs'};APPROVAL={'pending','approved','rejected','not_required'};LEVELS={'L0_REFERENCE','L1_HANDOFF','L2_VALIDATED_ADAPTER','L3_EXECUTION_TESTED'}
def validate(d):
    e=[];w=[]
    for k in ['schema_version','job_id','engine','engine_version','support_level','method_fingerprint_id','executable','input','workdir','scheduler','resources','environment','expected_outputs','checkpoint_policy','preflight','parser','approval']:
        if k not in d:e.append(f'missing {k}')
    if d.get('engine') not in ENGINES:e.append('unsupported engine')
    if d.get('scheduler') not in SCHED:e.append('unsupported scheduler')
    if d.get('approval') not in APPROVAL:e.append('invalid approval')
    if d.get('support_level') not in LEVELS:e.append('invalid support_level')
    r=d.get('resources') or {}
    for k in ['nodes','tasks_per_node','cpus_per_task','memory_gb','walltime']:
        if k not in r:e.append(f'resources missing {k}')
    for k in ['nodes','tasks_per_node','cpus_per_task']:
        try:
            if int(r.get(k,0))<1:e.append(f'{k} must be >=1')
        except (TypeError,ValueError):e.append(f'{k} must be integer')
    try:
        if float(r.get('memory_gb',0))<=0:e.append('memory_gb must be positive')
    except (TypeError,ValueError):e.append('memory_gb must be numeric')
    if not re.match(r'^(?:\d+-)?\d{1,3}:\d{2}:\d{2}$',str(r.get('walltime',''))):e.append('walltime must be HH:MM:SS or D-HH:MM:SS')
    if not d.get('expected_outputs'):e.append('expected_outputs must not be empty')
    if not (d.get('preflight') or {}).get('command'):e.append('preflight.command required')
    if not (d.get('parser') or {}).get('command'):e.append('parser.command required')
    if d.get('approval')=='approved' and d.get('support_level')=='L0_REFERENCE':e.append('documentation-only support cannot be approved for execution')
    if d.get('approval')=='approved' and e:e.append('approved manifest has validation errors')
    return e,w

def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument('manifest',type=Path);a=ap.parse_args();d=yaml.safe_load(a.manifest.read_text()) or {};e,w=validate(d);print(json.dumps({'ok':not e,'errors':e,'warnings':w},indent=2));return 0 if not e else 1
if __name__=='__main__':raise SystemExit(main())

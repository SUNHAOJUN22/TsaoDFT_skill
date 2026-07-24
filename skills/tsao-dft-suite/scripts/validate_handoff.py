#!/usr/bin/env python3
"""Validate a cross-Skill TsaoDFT handoff."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path
import yaml

SKILLS={
 'tsao-dft-suite','tsao-structure-prep','tsao-dft-researcher','tsao-periodic-dft-materials',
 'tsao-dft-ml-active-learning','tsao-dft-hpc-provenance','tsao-dft-kinetics-multiscale',
 'tsao-dft-catalysis-profile'
}
LEVELS={'L0_REFERENCE','L1_HANDOFF','L2_VALIDATED_ADAPTER','L3_EXECUTION_TESTED'}
APPROVAL={'pending','approved','rejected','not_required'}
SHA=re.compile(r'^[0-9a-f]{64}$')

def validate(data:dict)->tuple[list[str],list[str]]:
    errors=[]; warnings=[]
    required=['handoff_version','project_id','handoff_id','source_skill','target_skill','source_task_id',
              'target_task_id','scientific_objective','observable','model_identity','structure_artifacts',
              'accepted_parent_artifacts','method_fingerprint_id','support_level','open_assumptions',
              'blocking_unknowns','requested_outputs','success_criteria','resource_estimate','approval_status']
    for key in required:
        if key not in data: errors.append(f'missing {key}')
    if data.get('source_skill') not in SKILLS: errors.append('unknown source_skill')
    if data.get('target_skill') not in SKILLS: errors.append('unknown target_skill')
    if data.get('source_skill')==data.get('target_skill'): warnings.append('source_skill equals target_skill; handoff may be unnecessary')
    if data.get('support_level') not in LEVELS: errors.append('invalid support_level')
    if data.get('approval_status') not in APPROVAL: errors.append('invalid approval_status')
    for field in ['structure_artifacts','accepted_parent_artifacts']:
        for i,item in enumerate(data.get(field) or []):
            if not isinstance(item,dict): errors.append(f'{field}[{i}] must be an object'); continue
            if not item.get('id'): errors.append(f'{field}[{i}] missing id')
            if not SHA.match(str(item.get('sha256',''))): errors.append(f'{field}[{i}] invalid sha256')
            if field=='accepted_parent_artifacts' and item.get('status')!='accepted': errors.append(f'{field}[{i}] is not accepted')
    estimate=data.get('resource_estimate') or {}
    for key in ['jobs','cpu_hours','gpu_hours','storage_gb']:
        try:
            if float(estimate.get(key,0))<0: errors.append(f'resource_estimate.{key} must be nonnegative')
        except (TypeError,ValueError): errors.append(f'resource_estimate.{key} must be numeric')
    blocking=data.get('blocking_unknowns') or []
    if blocking and data.get('approval_status')=='approved': errors.append('approved handoff still has blocking_unknowns')
    if data.get('support_level')=='L0_REFERENCE' and data.get('approval_status')=='approved':
        warnings.append('L0_REFERENCE is documentation-only; approval does not make it executable')
    if not data.get('success_criteria'): warnings.append('no success_criteria declared')
    return errors,warnings

def main()->int:
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument('handoff',type=Path); ap.add_argument('--json',action='store_true'); a=ap.parse_args()
    data=yaml.safe_load(a.handoff.read_text(encoding='utf-8'))
    e,w=validate(data or {}); report={'ok':not e,'errors':e,'warnings':w}
    print(json.dumps(report,indent=2) if a.json else '\n'.join(['PASS' if not e else 'FAIL']+[f'ERROR: {x}' for x in e]+[f'WARN: {x}' for x in w]))
    return 0 if not e else 1
if __name__=='__main__': raise SystemExit(main())

#!/usr/bin/env python3
"""Validate a DFT-ML model card."""
from __future__ import annotations
import argparse,json
from pathlib import Path

def validate(d):
    e=[];w=[]
    for k in ['schema_version','model_id','model_family','features','target','group_column','split_policy','preprocessing_fit_scope','metrics','counts','scientific_interpretation','status']:
        if k not in d:e.append(f'missing {k}')
    if d.get('preprocessing_fit_scope')!='train_only':e.append('preprocessing_fit_scope must be train_only')
    if d.get('split_policy') not in {'group','scaffold','composition','time','external','leave-one-family-out'}:w.append('split policy may not demonstrate structural extrapolation')
    for split in ['train','test']:
        if split not in (d.get('metrics') or {}):e.append(f'missing {split} metrics')
        else:
            for metric in ['mae','rmse','r2']:
                if metric not in d['metrics'][split]:e.append(f'{split} missing {metric}')
    if d.get('scientific_interpretation') not in {'baseline_only','predictive_within_domain','external_validation_supported','exploratory'}:e.append('invalid scientific_interpretation')
    if d.get('status')=='accepted' and d.get('scientific_interpretation') in {'baseline_only','exploratory'}:e.append('baseline/exploratory model cannot be accepted as predictive evidence')
    if not d.get('applicability_domain'):w.append('applicability_domain not recorded')
    if not d.get('uncertainty_calibration'):w.append('uncertainty calibration not recorded')
    return e,w

def main()->int:
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('card',type=Path);a=ap.parse_args();d=json.loads(a.card.read_text());e,w=validate(d);print(json.dumps({'ok':not e,'errors':e,'warnings':w},indent=2));return 0 if not e else 1
if __name__=='__main__':raise SystemExit(main())

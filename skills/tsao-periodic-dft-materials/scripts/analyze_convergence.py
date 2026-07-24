#!/usr/bin/env python3
"""Analyze a one-parameter DFT convergence table."""
from __future__ import annotations
import argparse,csv,json,math
from pathlib import Path

def main()->int:
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('csv',type=Path);ap.add_argument('--value-column',default='value');ap.add_argument('--observable-column',default='observable_value');ap.add_argument('--absolute-threshold',type=float,required=True);ap.add_argument('--tail',type=int,default=2);a=ap.parse_args()
    with a.csv.open(encoding='utf-8') as f:rows=list(csv.DictReader(f))
    errors=[];data=[]
    for i,r in enumerate(rows):
        try:data.append((float(r[a.value_column]),float(r[a.observable_column]),r))
        except Exception as exc:errors.append(f'row {i+2}: {exc}')
    data.sort(key=lambda x:x[0]);deltas=[]
    for prev,cur in zip(data,data[1:]):deltas.append({'from':prev[0],'to':cur[0],'absolute_change':abs(cur[1]-prev[1])})
    tail=deltas[-a.tail:] if deltas else [];converged=bool(tail) and all(x['absolute_change']<=a.absolute_threshold for x in tail)
    report={'ok':not errors,'errors':errors,'point_count':len(data),'deltas':deltas,'threshold':a.absolute_threshold,'tail_checked':len(tail),'converged_candidate':converged,'recommended_value':data[-1][0] if converged else None,'note':'Convergence of one observable does not validate all properties or scientific model choices.'}
    print(json.dumps(report,indent=2));return 0 if not errors and converged else 2 if not errors else 1
if __name__=='__main__':raise SystemExit(main())

#!/usr/bin/env python3
"""Calculate transparent CPU/GPU-hour and allocation estimates from an HPC manifest."""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
import yaml

def hours(value:str)->float:
    p=value.split(':')
    if len(p)==3:return int(p[0])+int(p[1])/60+int(p[2])/3600
    m=re.match(r'(?:(\d+)-)?(\d+):(\d+):(\d+)',value)
    if m:return int(m.group(1) or 0)*24+int(m.group(2))+int(m.group(3))/60+int(m.group(4))/3600
    raise ValueError('walltime must be HH:MM:SS or D-HH:MM:SS')
def main()->int:
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('manifest',type=Path);ap.add_argument('--jobs',type=int,default=1);a=ap.parse_args();d=yaml.safe_load(a.manifest.read_text()) or {};r=d.get('resources') or {}
    try:
        wh=hours(str(r['walltime']));nodes=int(r['nodes']);tpn=int(r['tasks_per_node']);cpt=int(r['cpus_per_task']);gpn=int(r.get('gpus_per_node',r.get('gpus',0)));mem=float(r['memory_gb']);jobs=a.jobs
        rep={'ok':True,'jobs':jobs,'walltime_hours_each':wh,'allocated_cpu_cores_each':nodes*tpn*cpt,'allocated_cpu_hours_total':jobs*wh*nodes*tpn*cpt,'allocated_gpu_hours_total':jobs*wh*nodes*gpn,'allocated_memory_gb_nodes_total':jobs*mem*nodes,'upper_bound_storage_gb':float(d.get('estimated_storage_gb',0))*jobs,'note':'Allocation estimates are upper bounds, not measured utilization.'}
    except Exception as exc:rep={'ok':False,'errors':[str(exc)]}
    print(json.dumps(rep,indent=2));return 0 if rep['ok'] else 1
if __name__=='__main__':raise SystemExit(main())

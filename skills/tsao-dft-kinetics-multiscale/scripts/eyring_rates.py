#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,math
from pathlib import Path
KB=1.380649e-23;H=6.62607015e-34;R=1.98720425864083
ap=argparse.ArgumentParser();ap.add_argument('barriers',type=Path);ap.add_argument('--temperature',type=float,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--kappa',type=float,default=1.0);a=ap.parse_args();rows=list(csv.DictReader(a.barriers.open(encoding='utf-8')))
for r in rows:
 dg=float(r['delta_g_dagger_kcal_mol']);deg=float(r.get('path_degeneracy') or 1);r['k_tst_s-1_or_standard_state']=f"{a.kappa*deg*KB*a.temperature/H*math.exp(-dg/(R*a.temperature)):.8e}";r['temperature_K']=a.temperature
with a.out.open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
print(a.out)

#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,math
from pathlib import Path
KB=1.380649e-23;H=6.62607015e-34;R=1.98720425864083

def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('barriers',type=Path);ap.add_argument('--temperature',type=float,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--kappa',type=float,default=1.0);ap.add_argument('--standard-state',default='unspecified');a=ap.parse_args();rows=list(csv.DictReader(a.barriers.open(encoding='utf-8')))
 if a.temperature<=0 or a.kappa<=0:raise SystemExit('temperature and kappa must be positive')
 for r in rows:
  dg=float(r['delta_g_dagger_kcal_mol']);deg=float(r.get('path_degeneracy') or 1);mol=int(r.get('molecularity') or 1);value=a.kappa*deg*KB*a.temperature/H*math.exp(-dg/(R*a.temperature));r['k_tst_s-1_or_standard_state']=f"{value:.8e}";r['temperature_K']=a.temperature;r['kappa']=a.kappa;r['rate_unit']='s^-1' if mol==1 else 'M^-1 s^-1' if mol==2 else f'M^{1-mol} s^-1';r['standard_state']=a.standard_state
 with a.out.open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
 print(a.out);return 0
if __name__=='__main__':raise SystemExit(main())

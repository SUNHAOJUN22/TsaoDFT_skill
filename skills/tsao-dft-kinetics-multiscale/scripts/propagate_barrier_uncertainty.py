#!/usr/bin/env python3
"""Propagate a symmetric activation-free-energy bound into a TST rate interval."""
from __future__ import annotations
import argparse,json,math
KB=1.380649e-23;H=6.62607015e-34;R=1.98720425864083

def rate(dg,T,kappa,deg):return kappa*deg*KB*T/H*math.exp(-dg/(R*T))
def main()->int:
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--barrier',type=float,required=True);ap.add_argument('--uncertainty',type=float,required=True);ap.add_argument('--temperature',type=float,required=True);ap.add_argument('--kappa',type=float,default=1.0);ap.add_argument('--degeneracy',type=float,default=1.0);ap.add_argument('--molecularity',type=int,default=1);a=ap.parse_args()
    if a.temperature<=0 or a.uncertainty<0 or a.kappa<=0 or a.degeneracy<=0:return 1
    central=rate(a.barrier,a.temperature,a.kappa,a.degeneracy);slow=rate(a.barrier+a.uncertainty,a.temperature,a.kappa,a.degeneracy);fast=rate(a.barrier-a.uncertainty,a.temperature,a.kappa,a.degeneracy);unit='s^-1' if a.molecularity==1 else 'M^-1 s^-1 (standard-state convention required)' if a.molecularity==2 else f'concentration^({1-a.molecularity}) s^-1'
    print(json.dumps({'barrier_kcal_mol':a.barrier,'uncertainty_kcal_mol':a.uncertainty,'temperature_K':a.temperature,'central_rate':central,'lower_rate':slow,'upper_rate':fast,'rate_unit':unit,'note':'Interval reflects only the declared barrier bound, not model/transport uncertainty.'},indent=2));return 0
if __name__=='__main__':raise SystemExit(main())

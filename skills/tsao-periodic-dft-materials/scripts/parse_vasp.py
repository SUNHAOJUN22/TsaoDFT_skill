#!/usr/bin/env python3
"""Parse VASP output evidence from OUTCAR/OSZICAR without scientific overclaiming."""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
FLOAT=r'[-+]?\d*\.?\d+(?:[Ee][-+]?\d+)?'
def parse(path:Path)->dict:
    run=path if path.is_dir() else path.parent;out=run/'OUTCAR' if path.is_dir() else path;text=out.read_text(encoding='utf-8',errors='replace') if out.exists() else ''
    normal='General timing and accounting informations for this job' in text
    version=(re.search(r'vasp\.([\d.]+)',text,re.I).group(1) if re.search(r'vasp\.([\d.]+)',text,re.I) else None)
    energies=[float(x) for x in re.findall(r'free\s+energy\s+TOTEN\s*=\s*(%s)\s+eV'%FLOAT,text)]
    efermi=[float(x) for x in re.findall(r'E-fermi\s*:\s*(%s)'%FLOAT,text)]
    nions=(int(re.findall(r'NIONS\s*=\s*(\d+)',text)[-1]) if re.findall(r'NIONS\s*=\s*(\d+)',text) else None)
    electronic_converged='aborting loop because EDIFF is reached' in text or 'EDIFF is reached' in text
    ionic_converged='reached required accuracy - stopping structural energy minimisation' in text
    warnings=[]
    for pat,msg in [(r'BRMIX: very serious problems','BRMIX mixing problem'),(r'ZBRENT: fatal error','ZBRENT ionic optimization error'),(r'WARNING: Sub-Space-Matrix is not hermitian','subspace matrix warning'),(r'EDDDAV: Call to ZHEGV failed','diagonalization failure')]:
        if re.search(pat,text,re.I):warnings.append(msg)
    force_blocks=re.findall(r'TOTAL-FORCE \(eV/Angst\)(.*?)total drift',text,re.S|re.I);max_force=None
    if force_blocks:
        vals=[]
        for line in force_blocks[-1].splitlines():
            p=line.split()
            if len(p)>=6:
                try:vals.append((float(p[-3])**2+float(p[-2])**2+float(p[-1])**2)**0.5)
                except ValueError:pass
        max_force=max(vals) if vals else None
    elapsed=(float(re.findall(r'Elapsed time \(sec\):\s*(%s)'%FLOAT,text)[-1]) if re.findall(r'Elapsed time \(sec\):\s*(%s)'%FLOAT,text) else None)
    status='RUN_FAILED' if not text else 'COMPLETED_UNVALIDATED'
    if normal and electronic_converged:status='STATIC_VALIDATED_CANDIDATE'
    if normal and electronic_converged and ionic_converged:status='RELAX_VALIDATED_CANDIDATE'
    if normal and not electronic_converged:warnings.append('VASP ended but electronic convergence marker was not found')
    return {'status':status,'normal_termination':normal,'version':version,'last_toten_eV':energies[-1] if energies else None,'energy_count':len(energies),'fermi_energy_eV':efermi[-1] if efermi else None,'nions':nions,'electronic_converged':electronic_converged,'ionic_converged':ionic_converged,'max_force_eV_per_angstrom':max_force,'elapsed_seconds':elapsed,'warnings':warnings,'scientific_acceptance':'PENDING'}
def main()->int:
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('path',type=Path);a=ap.parse_args();r=parse(a.path);print(json.dumps(r,indent=2));return 0 if r['normal_termination'] else 1
if __name__=='__main__':raise SystemExit(main())

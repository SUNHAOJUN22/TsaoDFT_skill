#!/usr/bin/env python3
"""Parse Quantum ESPRESSO pw.x output evidence."""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
FLOAT=r'[-+]?\d*\.?\d+(?:[Ee][-+]?\d+)?'
RY_TO_EV=13.605693122994

def parse(path:Path)->dict:
    text=path.read_text(encoding='utf-8',errors='replace');done='JOB DONE.' in text
    version=(re.search(r'Program PWSCF v\.([\w.\-]+)',text).group(1) if re.search(r'Program PWSCF v\.([\w.\-]+)',text) else None)
    energies=[float(x) for x in re.findall(r'!\s+total energy\s+=\s*(%s)\s+Ry'%FLOAT,text)]
    scf_converged='convergence has been achieved' in text
    ionic_converged='End of BFGS Geometry Optimization' in text or 'bfgs converged in' in text.lower()
    fermi=[float(x) for x in re.findall(r'the Fermi energy is\s*(%s)\s*ev'%FLOAT,text,re.I)]
    force=[float(x) for x in re.findall(r'Total force =\s*(%s)'%FLOAT,text)]
    pressure=[float(x) for x in re.findall(r'P=\s*(%s)'%FLOAT,text)]
    warnings=[]
    if 'convergence NOT achieved' in text:warnings.append('SCF convergence not achieved')
    if 'Error in routine' in text:warnings.append('QE Error in routine detected')
    status='RUN_FAILED' if not done else ('RELAX_VALIDATED_CANDIDATE' if scf_converged and ionic_converged else 'STATIC_VALIDATED_CANDIDATE' if scf_converged else 'COMPLETED_UNVALIDATED')
    return {'status':status,'job_done':done,'version':version,'last_total_energy_Ry':energies[-1] if energies else None,'last_total_energy_eV':energies[-1]*RY_TO_EV if energies else None,'energy_count':len(energies),'scf_converged':scf_converged,'ionic_converged':ionic_converged,'fermi_energy_eV':fermi[-1] if fermi else None,'last_total_force_Ry_per_bohr':force[-1] if force else None,'last_pressure_kbar':pressure[-1] if pressure else None,'warnings':warnings,'scientific_acceptance':'PENDING'}
def main()->int:
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('output',type=Path);a=ap.parse_args();r=parse(a.output);print(json.dumps(r,indent=2));return 0 if r['job_done'] else 1
if __name__=='__main__':raise SystemExit(main())

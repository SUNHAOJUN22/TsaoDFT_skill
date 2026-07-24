#!/usr/bin/env python3
"""Parse CP2K output evidence."""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
FLOAT=r'[-+]?\d*\.?\d+(?:[Ee][-+]?\d+)?'
HARTREE_TO_EV=27.211386245988

def parse(path:Path)->dict:
    text=path.read_text(encoding='utf-8',errors='replace');ended='PROGRAM ENDED AT' in text
    version=(re.search(r'CP2K\| version string:\s*(.+)',text).group(1).strip() if re.search(r'CP2K\| version string:\s*(.+)',text) else None)
    energies=[float(x) for x in re.findall(r'ENERGY\| Total FORCE_EVAL.*?energy \(a\.u\.\):\s*(%s)'%FLOAT,text)]
    scf_converged='SCF run converged' in text
    geo_converged='GEOMETRY OPTIMIZATION COMPLETED' in text or 'Reevaluating energy at the minimum' in text
    max_force=[float(x) for x in re.findall(r'Max\. gradient\s*=\s*(%s)'%FLOAT,text)]
    warnings=[]
    if 'SCF run NOT converged' in text:warnings.append('SCF not converged')
    if 'ABORT' in text:warnings.append('CP2K abort detected')
    status='RUN_FAILED' if not ended else ('RELAX_VALIDATED_CANDIDATE' if scf_converged and geo_converged else 'STATIC_VALIDATED_CANDIDATE' if scf_converged else 'COMPLETED_UNVALIDATED')
    return {'status':status,'program_ended':ended,'version':version,'last_total_energy_hartree':energies[-1] if energies else None,'last_total_energy_eV':energies[-1]*HARTREE_TO_EV if energies else None,'energy_count':len(energies),'scf_converged':scf_converged,'geometry_converged':geo_converged,'last_max_gradient':max_force[-1] if max_force else None,'warnings':warnings,'scientific_acceptance':'PENDING'}
def main()->int:
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('output',type=Path);a=ap.parse_args();r=parse(a.output);print(json.dumps(r,indent=2));return 0 if r['program_ended'] else 1
if __name__=='__main__':raise SystemExit(main())

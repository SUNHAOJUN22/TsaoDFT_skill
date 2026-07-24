#!/usr/bin/env python3
"""Generate reviewed local/Slurm/PBS job scripts for DFT engines."""
from __future__ import annotations
import argparse,shlex
from pathlib import Path
import yaml


def q(x):return shlex.quote(str(x))

def engine_command(d:dict)->str:
    eng=d['engine'];exe=q(d['executable']);inp=q(d['input']);out=q(d.get('stdout') or (Path(str(d['input'])).stem+'.stdout'));err=q(d.get('stderr') or (Path(str(d['input'])).stem+'.stderr'))
    launcher=d.get('launcher','')
    prefix=(launcher.strip()+' ') if launcher else ''
    if eng=='gaussian':return f"{prefix}{exe} < {inp} > {out} 2> {err}"
    if eng=='vasp':return f"{prefix}{exe} > {out} 2> {err}"
    if eng=='quantum-espresso':return f"{prefix}{exe} -in {inp} > {out} 2> {err}"
    if eng=='cp2k':return f"{prefix}{exe} -i {inp} -o {out} 2> {err}"
    return f"{prefix}{exe} {inp} > {out} 2> {err}"

def build(d:dict)->str:
    r=d['resources'];s=d['scheduler'];lines=['#!/usr/bin/env bash','set -euo pipefail']
    headers=[]
    if s=='slurm':
        headers=[f"#SBATCH --job-name={d['job_id']}",f"#SBATCH --nodes={r['nodes']}",f"#SBATCH --ntasks-per-node={r['tasks_per_node']}",f"#SBATCH --cpus-per-task={r['cpus_per_task']}",f"#SBATCH --mem={r['memory_gb']}G",f"#SBATCH --time={r['walltime']}"]
        if r.get('partition'):headers.append(f"#SBATCH --partition={r['partition']}")
        if int(r.get('gpus_per_node',r.get('gpus',0)))>0:headers.append(f"#SBATCH --gpus-per-node={int(r.get('gpus_per_node',r.get('gpus',0)))}")
    elif s=='pbs':
        select=f"select={r['nodes']}:ncpus={int(r['tasks_per_node'])*int(r['cpus_per_task'])}:mem={r['memory_gb']}gb"
        if int(r.get('gpus_per_node',r.get('gpus',0)))>0:select+=f":ngpus={int(r.get('gpus_per_node',r.get('gpus',0)))}"
        headers=[f"#PBS -N {d['job_id']}",f"#PBS -l {select}",f"#PBS -l walltime={r['walltime']}"]
        if r.get('queue'):headers.append(f"#PBS -q {r['queue']}")
    lines[1:1]=headers
    lines += ['',f"# engine: {d['engine']} {d.get('engine_version','unknown')}",f"# method_fingerprint_id: {d.get('method_fingerprint_id','unknown')}",f"# support_level: {d.get('support_level','unknown')}",f"# approval: {d.get('approval','pending')}"]
    env=d.get('environment') or {}
    for m in env.get('modules',[]):lines.append(f'module load {q(m)}')
    for src in env.get('source',[]):lines.append(f'source {q(src)}')
    for key,val in (env.get('variables') or {}).items():lines.append(f'export {key}={q(val)}')
    scratch=d.get('scratch') or {}
    if scratch.get('path'):
        lines.append(f"mkdir -p {q(scratch['path'])}")
        if d['engine']=='gaussian':lines.append(f"export GAUSS_SCRDIR={q(scratch['path'])}")
    lines += ['',f"cd {q(d['workdir'])}",'echo "TsaoDFT job start: $(date -Is)"','echo "Host: $(hostname)"']
    lines.append(f"# preflight: {(d.get('preflight') or {}).get('command','not recorded')}")
    if (d.get('preflight') or {}).get('run_in_job',False):lines.append(str(d['preflight']['command']))
    lines.append(engine_command(d))
    lines += ['rc=$?','echo "TsaoDFT job end: $(date -Is) rc=${rc}"']
    if (d.get('parser') or {}).get('run_in_job',False):lines.append(str(d['parser']['command']))
    lines.append('exit ${rc}')
    return '\n'.join(lines)+'\n'

def main()->int:
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('manifest',type=Path);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();d=yaml.safe_load(a.manifest.read_text());a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(build(d),encoding='utf-8');a.out.chmod(0o755);print(a.out);return 0
if __name__=='__main__':raise SystemExit(main())

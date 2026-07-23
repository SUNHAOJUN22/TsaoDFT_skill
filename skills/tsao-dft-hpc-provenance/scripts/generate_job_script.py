#!/usr/bin/env python3
import argparse,shlex
from pathlib import Path
import yaml
ap=argparse.ArgumentParser();ap.add_argument('manifest',type=Path);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();d=yaml.safe_load(a.manifest.read_text());r=d['resources'];s=d['scheduler'];lines=['#!/usr/bin/env bash','set -euo pipefail']
if s=='slurm':
 lines[1:1]=[f"#SBATCH --job-name={d['job_id']}",f"#SBATCH --nodes={r['nodes']}",f"#SBATCH --ntasks-per-node={r['tasks_per_node']}",f"#SBATCH --cpus-per-task={r['cpus_per_task']}",f"#SBATCH --mem={r['memory_gb']}G",f"#SBATCH --time={r['walltime']}"]
elif s=='pbs':
 lines[1:1]=[f"#PBS -N {d['job_id']}",f"#PBS -l select={r['nodes']}:ncpus={r['tasks_per_node']*r['cpus_per_task']}:mem={r['memory_gb']}gb",f"#PBS -l walltime={r['walltime']}"]
for m in (d.get('environment') or {}).get('modules',[]):lines.append(f'module load {shlex.quote(str(m))}')
for src in (d.get('environment') or {}).get('source',[]):lines.append(f'source {shlex.quote(str(src))}')
lines += [f"cd {shlex.quote(str(d['workdir']))}",f"{shlex.quote(str(d['executable']))} < {shlex.quote(str(d['input']))} > {shlex.quote(Path(str(d['input'])).stem+'.stdout')} 2> {shlex.quote(Path(str(d['input'])).stem+'.stderr')}"]
a.out.write_text('\n'.join(lines)+'\n');a.out.chmod(0o755);print(a.out)

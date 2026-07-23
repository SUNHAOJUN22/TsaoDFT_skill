# Tsao DFT HPC and Provenance

General execution Skill for computational chemistry on local machines, Slurm, PBS and cloud/HPC. It generates reviewable scripts and provenance records but does not submit without explicit approval.

```bash
python scripts/validate_hpc_manifest.py examples/slurm/hpc-manifest.yaml
python scripts/generate_job_script.py examples/slurm/hpc-manifest.yaml --out job.slurm
python scripts/classify_failure.py examples/failures/gaussian-memory.log
```

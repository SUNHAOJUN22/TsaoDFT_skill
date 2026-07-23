---
name: tsao-dft-hpc-provenance
description: "Prepare and audit local, Slurm, PBS and cloud/HPC computational-chemistry execution: environment inspection, dependency checks, resource estimates, job scripts, batch DAGs, monitoring, failure classification, checkpoint/restart policy, provenance, reproducibility and scientific CI."
license: MIT
compatibility: Python 3.10+ and PyYAML. Slurm, PBS, containers, AiiDA, Snakemake and Nextflow are optional external systems.
metadata: {"version": "0.3.0-alpha.1", "author": "SUNHAOJUN22", "repository": "https://github.com/SUNHAOJUN22/TsaoDFT_skill"}
---

# Tsao DFT HPC and Provenance

This Skill owns execution mechanics, not scientific method selection. It consumes accepted plans from the scientific Skills and returns immutable run records and validated outputs.

## Workflow

1. Read a site guide or inspect the named execution target; never scan unrelated filesystems.
2. Record executable/module/container, version, scheduler, partition/queue, scratch, quotas, MPI/OpenMP/GPU layout and environment variables.
3. Estimate CPU/GPU hours, memory, wall time and storage before production submission.
4. Generate scripts from a reviewed manifest. Submission, cancellation and destructive cleanup require explicit user instruction.
5. Monitor scheduler and logs. Classify exact failures before changing one parameter at a time.
6. Preserve input, actual script, stdout/stderr, checkpoints, output hashes, software/environment fingerprint and restart lineage.
7. Promote outputs only after the engine parser validates them; HPC success is not scientific acceptance.

## Routes

| Need | Route |
|---|---|
| Environment, modules, dependencies | `environment` |
| Slurm/PBS/local job script | `job_script` |
| Batch DAG and campaign | `batch` |
| Monitor, failure and restart | `recovery` |
| Provenance, packaging, reproducibility and CI | `provenance` |

## Hard Guardrails

- Never submit merely because an input file exists.
- Never auto-increase cost or wall time without logging the reason and obtaining approval when material.
- Restart only from compatible checkpoints; changing method or geometry policy creates a new run lineage.
- Do not hide failed attempts. Keep every attempt, error signature and fix.
- Containers do not solve licensed-software or pseudopotential distribution rights.
- Scheduler completion means only that the process ended; the engine-specific validator owns result quality.


# Compute Efficiency Guide

This guide separates **repository software overhead**, **scheduler throughput** and **electronic-structure kernel cost**. A faster parser cannot make an unconverged calculation acceptable, and more ranks or threads do not guarantee lower wall time.

## Implemented repository optimizations

### Large-output parsing

VASP, Quantum ESPRESSO and CP2K output adapters use read-only memory maps and bytes patterns. They retain selected last values and bounded terminal blocks rather than decoding entire outputs and building complete match lists.

The Gaussian adapter remains on its established decoded-text implementation. A lower-retention prototype reduced Python allocation on a synthetic rich log, but the wall-time gain was modest and the shared-context compatibility risk was not justified for this release.

### Content hashing

Provenance and structure files are hashed in 1 MiB chunks. The digest remains ordinary SHA-256 and is byte-identical to the former `read_bytes()` implementation.

Large DFT-labelled datasets preserve the exact historical digest of `json.dumps(rows, sort_keys=True)`, but serialize the canonical list in bounded 256-row batches. Small datasets retain the faster one-shot path.

### Linear algebra

The NumPy ridge baseline selects the smaller regularized system:

- **primal** for matrices that are not wider than the training set;
- **dual** for wide feature matrices;
- `numpy.linalg.lstsq` when `alpha = 0`.

It rejects NaN/Inf, records requested/selected solver, solve dimension, data shape and constant features. A condition-number SVD is not performed automatically because it can duplicate the dominant solve cost.

### Homogeneous Slurm campaigns

`generate_job_array.py` produces:

1. one approval-gated Slurm array script;
2. one JSONL task table with task ID, work directory and shell-quoted engine command.

`max_concurrent` becomes the Slurm `%` array throttle. The task table is written incrementally. This reduces file and scheduler-record scale; it does not promise faster local YAML/script generation or faster DFT kernels.

Example:

```bash
python skills/tsao-dft-hpc-provenance/scripts/generate_job_array.py \
  skills/tsao-dft-hpc-provenance/templates/slurm-array-campaign.yaml \
  --script campaign.sh \
  --tasks campaign.tasks.jsonl
```

The generator never submits the result. Pending or rejected approval inserts a runtime `exit 64` guard.

### Oversubscription guard

`validate_hpc_manifest.py` checks common thread variables against `resources.cpus_per_task`:

- `OMP_NUM_THREADS`
- `OPENBLAS_NUM_THREADS`
- `MKL_NUM_THREADS`
- `BLIS_NUM_THREADS`
- `VECLIB_MAXIMUM_THREADS`
- `NUMEXPR_NUM_THREADS`
- `NUMEXPR_MAX_THREADS`

When `cpus_per_node` is provided, `tasks_per_node × cpus_per_task` may not exceed it. This is a conservative manifest check, not a replacement for site topology documentation.

## Reproducible microbenchmark

```bash
python scripts/benchmark_performance.py \
  --baseline-commit 27745b74c4bc1521a47e6d74c4795cce477460bb \
  --out performance-results.json
```

Use `--quick` for a smaller smoke run. The script uses synthetic fixtures, medians after warm-up and `tracemalloc`; it never launches a DFT engine. See [`PERFORMANCE_AUDIT.md`](PERFORMANCE_AUDIT.md) for the measured revision results and rejected candidates.

## Target-environment guidance

### Avoid nested parallelism

Treat the product of scheduler tasks, OpenMP threads and BLAS/FFT internal threads as an allocation contract. Do not add a Python process pool around an already MPI/BLAS-parallel engine unless the site configuration explicitly supports that nesting.

### Use arrays for independent homogeneous calculations

Use a Slurm array when tasks share resources, software environment and method policy but differ by input/workdir/output. Use a workflow DAG when tasks have dependencies or materially different resources.

### Reuse only compatible state

Checkpoint, charge-density and wavefunction reuse can save major work, but compatibility must include engine/version, method fingerprint, geometry policy, basis/pseudopotential and relevant parallel/restart semantics. A changed scientific model creates a new lineage.

### Prevent duplicate calculations

ASE database `reserve()` and AiiDA content-based caching illustrate safe coordination patterns. Any future TsaoDFT cache must include full content and method/environment provenance; no implicit cache is currently enabled.

### Tune engines empirically

- VASP: benchmark `KPAR`, `NCORE`, ranks and OpenMP threads for the actual model.
- Quantum ESPRESSO: benchmark pools, images, task groups, diagonalization and restart layout with the actual build.
- CP2K: benchmark MPI/OpenMP balance, libraries and wavefunction restart behavior on the target site.
- Stage I/O-heavy work on approved scratch and record high-water memory, wall time, CPU efficiency and output volume.

## Non-claims

The repository does not claim universal speedups for Gaussian, VASP, Quantum ESPRESSO, CP2K, Multiwfn, Cantera or any HPC installation. Only measurements from the legal target environment can establish an L3 performance result.

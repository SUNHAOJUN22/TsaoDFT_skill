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

When `cpus_per_node` is provided, `tasks_per_node × cpus_per_task` may not exceed it. The acceleration contract additionally checks `tasks_per_node = gpus_per_node × ranks_per_gpu`, requires explicit GPU-oversubscription approval and rejects incompatible backend/vendor pairs.

### GPU, native-code and edge acceleration planner

`plan_acceleration.py` converts an explicit YAML profile into a deterministic compatibility and benchmark plan. It covers Gaussian, VASP, Quantum ESPRESSO, CP2K and generic native integrations across workstation, HPC and edge targets.

```bash
python skills/tsao-dft-hpc-provenance/scripts/plan_acceleration.py \
  skills/tsao-dft-hpc-provenance/templates/acceleration-profile.yaml \
  --out acceleration-plan.json
```

The report separates four routes:

1. engine-native GPU builds;
2. CPU MPI/OpenMP execution;
3. CUDA-accelerated atomistic ML surrogates;
4. edge orchestration or validated edge inference with remote production DFT.

It evaluates cuBLAS, cuSOLVER, cuSOLVERMp, cuFFT, cuFFTMp, cuSPARSE, NCCL, NVSHMEM, cuTENSOR, cuEquivariance and CUTLASS without treating any library as a universal drop-in switch. It records initial MPI-rank/GPU mapping, build fingerprint requirements, CPU/native boundaries, benchmark metrics, mixed-precision warnings and explicit non-claims.

The planner is an L2 validated adapter. It does not modify or launch licensed engines, and its output is L1 planning evidence until real target-environment measurements are attached.

### Bound acceleration benchmark materialization

`materialize_acceleration_campaign.py` converts a matching base Manifest and acceleration profile into reproducible, approval-gated benchmark artifacts:

```bash
python skills/tsao-dft-hpc-provenance/scripts/materialize_acceleration_campaign.py \
  skills/tsao-dft-hpc-provenance/templates/vasp-gpu-hpc-manifest.yaml \
  skills/tsao-dft-hpc-provenance/templates/acceleration-profile.yaml \
  --manifest-out build/vasp-h100.yaml \
  --matrix-out build/benchmark-matrix.csv \
  --candidate-dir build/candidates \
  --plan-out build/acceleration-plan.json
```

The default profile produces an FP64 CPU scientific reference and 1/2/4-GPU candidates. It preserves engine identity, scientific input, method fingerprint and convergence policy; calculates tasks and CPUs from `gpus_per_node`, `ranks_per_gpu` and `cpus_per_gpu`; writes one candidate Manifest per matrix row; and forces every candidate to `approval: pending`. It never calls `sbatch`, `qsub`, `srun` or the DFT engine.

For Slurm, `launcher: auto` generates a reviewed `srun` step with total ranks, ranks per node, CPUs per task, bad-exit propagation and declared CPU/GPU binding. One-rank-per-GPU layouts request one GPU per task. The script leaves device visibility to the scheduler rather than exporting a fixed `CUDA_VISIBLE_DEVICES`.

When runtime capture is enabled, the generated script records profile/build/benchmark IDs, scheduler job/node/local-rank fields, visible-device variables and NVIDIA GPU name, UUID, PCI bus, driver and memory where `nvidia-smi` is available. These fields are provenance, not a performance result.

## Reproducible microbenchmark

```bash
python scripts/benchmark_performance.py \
  --baseline-commit 27745b74c4bc1521a47e6d74c4795cce477460bb \
  --out performance-results.json
```

Use `--quick` for a smaller smoke run. The script uses synthetic fixtures, medians after warm-up and `tracemalloc`; it never launches a DFT engine. See [`PERFORMANCE_AUDIT.md`](PERFORMANCE_AUDIT.md) for the measured revision results and rejected candidates.

## Target-environment guidance

### Keep Python on the control plane

Python remains appropriate for schemas, validation, provenance, scheduling, campaign logic, result parsing and experiment control. Rewriting these paths in C++ usually shifts maintenance cost without accelerating an external SCF kernel.

Move code only after profiling identifies a numerical hotspot. Use vectorized NumPy first, then a measured GPU array/framework backend or a compiled C++/Fortran/CUDA/OpenACC kernel. Bind native code through a narrow C ABI, pybind11/nanobind interface or versioned file/JSON subprocess contract, and retain a deterministic CPU fallback.

### Avoid nested parallelism

Treat the product of scheduler tasks, OpenMP threads and BLAS/FFT internal threads as an allocation contract. Do not add a Python process pool around an already MPI/BLAS-parallel engine unless the site configuration explicitly supports that nesting.

### Use arrays for independent homogeneous calculations

Use a Slurm array when tasks share resources, software environment and method policy but differ by input/workdir/output. Use a workflow DAG when tasks have dependencies or materially different resources.

### Reuse only compatible state

Checkpoint, charge-density and wavefunction reuse can save major work, but compatibility must include engine/version, method fingerprint, geometry policy, basis/pseudopotential and relevant parallel/restart semantics. A changed scientific model creates a new lineage.

### Prevent duplicate calculations

ASE database `reserve()` and AiiDA content-based caching illustrate safe coordination patterns. Any future TsaoDFT cache must include full content and method/environment provenance; no implicit cache is currently enabled.

### Tune engines empirically

- VASP: use the supported OpenACC GPU build where applicable; start from one MPI rank per GPU and `NCORE=1`, then benchmark `KPAR`, `NSIM`, ranks and OpenMP threads for the actual model.
- Quantum ESPRESSO: use a versioned GPU-enabled build and benchmark pools, images, task groups, diagonalization, MPI ranks, OpenMP threads and restart layout.
- CP2K: use the target-specific accelerator build and benchmark MPI/OpenMP balance, DBCSR/GRID/DBM/PW paths, ELPA/SPLA/COSMA choices and wavefunction restart behavior.
- Gaussian: use only vendor-supported accelerator features; never inject or redistribute CUDA libraries into a licensed binary.
- Stage I/O-heavy work on approved scratch and record high-water memory, wall time, CPU/GPU efficiency, host/device memory and output volume.

### Treat CUDA-X by workload, not by brand name

- cuEquivariance belongs to equivariant atomistic ML training or inference, not a Kohn-Sham SCF loop.
- cuTENSOR belongs to measured tensor contractions or explicit native integrations, not an arbitrary packaged DFT executable.
- cuSOLVERMp and cuFFTMp require explicit distributed designs and one-process-per-GPU style mappings appropriate to their APIs.
- NCCL and NVSHMEM help only when the selected engine, MPI stack and communication path support them.
- CUTLASS is a bespoke-kernel tool and should follow profiling, not precede it.

## Non-claims

The repository does not claim universal speedups for Gaussian, VASP, Quantum ESPRESSO, CP2K, Multiwfn, Cantera or any HPC installation. Only measurements from the legal target environment can establish an L3 performance result.

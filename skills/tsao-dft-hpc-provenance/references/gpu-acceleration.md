# GPU, native-code and edge acceleration contract

## Scope

This route plans acceleration without claiming that a Python manifest, a CUDA library name or a requested GPU makes an external DFT engine faster. The electronic-structure engine, its versioned build and the target site own kernel execution. TsaoDFT owns routing, resource contracts, provenance, validation and benchmark evidence.

## Decision order

1. Freeze the scientific model, convergence thresholds, reference states and acceptance tolerances.
2. Identify the measured bottleneck: SCF kernels, FFT, diagonalization, tensor contraction, ML inference/training, parser/I/O or campaign throughput.
3. Prefer the engine's supported accelerated build before custom integration.
4. Establish a CPU reference and a single-device result before multi-GPU or multi-node scaling.
5. Record compiler, architecture, driver/runtime, MPI, math libraries, engine commit/version, scheduler layout and input hash.
6. Accept acceleration only when time to solution improves and the scientific result remains within the declared tolerance.

## CUDA-X applicability

| Library | Suitable use | Boundary |
|---|---|---|
| cuBLAS / cuSOLVER | Dense linear algebra consumed by a supported GPU engine build or measured native extension | Not injected into an arbitrary prebuilt engine |
| cuSOLVERMp | Distributed dense solves and eigensystems in code that explicitly integrates the API | Requires multi-process/multi-GPU design and benchmark evidence |
| cuFFT / cuFFTMp | Local or distributed FFT kernels in compatible plane-wave or custom code | Engine build, decomposition and communication remain decisive |
| cuSPARSE | Measured sparse linear-algebra paths | Do not add for dense workloads |
| NCCL / NVSHMEM | Supported GPU collectives or GPU-initiated communication | Not a substitute for a compatible MPI and engine build |
| cuTENSOR | Measured tensor contractions, reductions and permutations | Not a drop-in acceleration flag for VASP, QE, CP2K or Gaussian |
| cuEquivariance | Equivariant atomistic ML training or inference | Accelerates an ML surrogate, not a Kohn-Sham SCF kernel |
| CUTLASS | Bespoke C++/CUDA kernels after profiling | High maintenance cost; retain a portable reference path |

## Engine routes

### VASP

Use the supported OpenACC GPU port. Begin benchmarking with one MPI rank per GPU and `NCORE=1`, then sweep `KPAR`, `NSIM`, OpenMP threads and communication settings for the actual system. Record whether the build uses CUDA-aware MPI and NCCL. Never infer speedup from GPU allocation alone.

### Quantum ESPRESSO

Use a versioned GPU-enabled build and its upstream test suite. Benchmark pools, images, task groups, diagonalization, MPI ranks and OpenMP threads. One rank per GPU is only a starting candidate because the optimum depends on the executable, k-point count, bands, FFT grids and interconnect.

### CP2K

Use a target-specific CUDA or HIP build and benchmark the enabled DBCSR, GRID, DBM and PW paths together with ELPA, SPLA and COSMA choices. Measure host/device memory, MPI/OpenMP balance, communication, I/O and restart compatibility.

### Gaussian and other licensed binaries

Use only vendor-documented accelerator features. Do not preload, patch, redistribute or reverse-engineer a licensed executable. Keep TsaoDFT at the manifest, scheduling, parsing and evidence boundary.

## Python and native-code boundary

Keep Python for:

- manifests, schemas and validation;
- scheduler and workflow orchestration;
- provenance, hashing and evidence graphs;
- lightweight parsing, reporting and experiment control.

Move only measured kernels to compiled code:

- C++/Fortran for CPU-native kernels and established engine integrations;
- CUDA or OpenACC for NVIDIA targets;
- HIP for supported AMD or cross-vendor builds;
- OpenMP target offload, Kokkos or SYCL when portability is a primary requirement;
- pybind11/nanobind, a narrow C ABI, or a versioned file/JSON subprocess contract at the Python boundary.

Every native path must have deterministic error propagation, an explicit architecture/build fingerprint, tests, and a CPU reference or fallback. Do not wrap an MPI/OpenMP/BLAS/GPU engine in a blind Python process pool.

## Scheduler binding contract

A GPU allocation count is incomplete without the rank and binding contract. An enabled acceleration Manifest records:

- backend and GPU vendor;
- `ranks_per_gpu` and explicit oversubscription approval;
- CPU binding (`cores`, `threads` or `none`);
- GPU binding (`closest`, `map:<IDs>` or `none`);
- precision policy;
- acceleration profile, build fingerprint and benchmark-plan IDs;
- whether runtime hardware identity must be captured.

For Slurm, `launcher: auto` generates an `srun` step with total ranks, ranks per node, CPUs per task, bad-exit propagation and the declared CPU/GPU binding. One rank per GPU also requests one GPU per task. The script does not export a fixed `CUDA_VISIBLE_DEVICES`; the scheduler owns visibility and binding.

When NVIDIA acceleration is enabled, the generated script can record:

- scheduler job, node and local-rank identifiers;
- the scheduler-provided visible-device map;
- GPU name, UUID, PCI bus ID, driver version and memory through `nvidia-smi`;
- profile, build-fingerprint, benchmark-plan, backend and precision identifiers.

These records contain execution metadata, not credentials, and remain subordinate to site policy.

## Benchmark materialization

First create the compatibility plan:

```bash
python skills/tsao-dft-hpc-provenance/scripts/plan_acceleration.py \
  skills/tsao-dft-hpc-provenance/templates/acceleration-profile.yaml \
  --out acceleration-plan.json
```

Then combine an engine-compatible base Manifest with the acceleration profile:

```bash
python skills/tsao-dft-hpc-provenance/scripts/materialize_acceleration_campaign.py \
  skills/tsao-dft-hpc-provenance/templates/vasp-gpu-hpc-manifest.yaml \
  skills/tsao-dft-hpc-provenance/templates/acceleration-profile.yaml \
  --manifest-out build/vasp-h100.yaml \
  --matrix-out build/benchmark-matrix.csv \
  --candidate-dir build/candidates \
  --plan-out build/acceleration-plan.json
```

The materializer:

1. rejects a base Manifest for a different engine;
2. transfers node, GPU, rank and CPU layout into a validated acceleration contract;
3. creates a mandatory FP64 CPU scientific reference;
4. creates the declared GPU scaling candidates;
5. resets every candidate to `approval: pending`;
6. writes only files and never submits a job.

The default VASP profile creates CPU, 1-GPU, 2-GPU and 4-GPU candidates. The scientific input, method fingerprint and convergence thresholds must remain identical across the matrix.

## Edge-computing route

Production DFT normally remains on a workstation, cluster or cloud/HPC target. Edge devices should preferentially perform structure validation, feature generation, provenance capture, queue control, visualization or validated surrogate inference. Route uncertain or out-of-domain candidates back to the accepted DFT execution path.

## Evidence boundary

The generated reports, Manifests and benchmark matrix are planning evidence only. Promote a scoped performance claim to L3 only after immutable real-engine measurements record time to solution, numerical agreement, utilization, peak host/device memory, I/O, scaling and the complete environment fingerprint.

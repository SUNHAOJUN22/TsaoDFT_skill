# TsaoDFT Skill

<p align="center">
  <strong>An evidence-locked, auditable DFT-first research operating system for molecular and periodic systems</strong><br>
  Python scientific control plane + verifiable numerical cores + professional external engines + non-fabricable qualification boundaries
</p>

<p align="center">
  <a href="README.md">中文</a> · <a href="README_EN.md">English</a>
</p>

<p align="center">
  <a href="https://github.com/SUNHAOJUN22/TsaoDFT_skill/actions/workflows/ci.yml"><img src="https://github.com/SUNHAOJUN22/TsaoDFT_skill/actions/workflows/ci.yml/badge.svg?branch=main" alt="CI"></a>
  <img src="https://img.shields.io/badge/Python-3.10%20%7C%203.12%20%7C%203.13-3776AB" alt="Python 3.10, 3.12 and 3.13">
  <img src="https://img.shields.io/badge/tests-629%20passing-16A34A" alt="629 tests passing">
  <img src="https://img.shields.io/badge/Linux%20coverage-93.87%25%20stmt%20%7C%2083.86%25%20branch-16A34A" alt="Linux 93.87 percent statement and 83.86 percent branch coverage">
  <img src="https://img.shields.io/badge/Windows%20coverage-93.81%25%20stmt%20%7C%2083.70%25%20branch-1687FF" alt="Windows 93.81 percent statement and 83.70 percent branch coverage">
  <img src="https://img.shields.io/badge/external%20qualification-EXTERNAL__HOLD-B45309" alt="External qualification EXTERNAL HOLD">
  <img src="https://img.shields.io/badge/license-MIT-16A34A" alt="MIT license">
</p>

> **AI image declaration | AI-GENERATED CONCEPTUAL ILLUSTRATION:** The single AI cover below communicates research context and system concepts only. Its molecules, lattices, orbitals, servers and interfaces are not data produced by Gaussian, VASP, Quantum ESPRESSO, CP2K, Multiwfn, VMD or experiments. All other architecture figures are deterministic SVG assets governed by repository scripts and visibly marked as synthetic demonstrations. Quantitative claims must come from accepted source files, computation artifacts and machine evidence.

<p align="center">
  <img src="assets/ai/hero/tsao-dft-hero.svg" width="100%" alt="TsaoDFT evidence-first DFT research operating system conceptual overview">
</p>

## Governing engineering doctrine

The repository follows [`docs/ACCELERATION_ENGINEERING_DOCTRINE.md`](docs/ACCELERATION_ENGINEERING_DOCTRINE.md):

1. **Python is the scientific control plane, not a defect requiring wholesale replacement.** It owns workflow, Schemas, method identity, scheduling, parsing, evidence and reporting.
2. **Professional DFT kernels are not reimplemented here.** FFTs, eigensolvers, integrals, SCF, MPI/OpenMP and GPU kernels belong to VASP, QE, CP2K, Gaussian and other scientific engines.
3. **Only narrow hotspots proven by representative profiling may migrate.** The order is CPU reference → NumPy/algorithmic optimization → optional C++/OpenMP → optional CUDA/HIP/SYCL.
4. **Every new backend retains a deterministic reference, failure fallback and numerical-equivalence gate.** Process startup, transfers and kernel overhead are part of end-to-end cost.
5. **Technology awareness is not execution evidence.** Understanding CUDA-X, ROCm, oneAPI or Metal does not prove that a library, device or compatible engine build was used.
6. **No speedup is published without a real solver, license, fixed input, stable hardware identity, scientific tolerance and repeated runs.** External qualification remains `EXTERNAL_HOLD`.

## TsaoDFT in 30 seconds

<table>
<tr>
<td width="25%" valign="top"><strong>DFT-first</strong><br><sub>Define structures, method fingerprints, references and acceptance conditions before execution.</sub></td>
<td width="25%" valign="top"><strong>Evidence graph</strong><br><sub>Computations, artifacts, figures and claims are linked by explicit support edges; failures remain visible.</sub></td>
<td width="25%" valign="top"><strong>Multi-engine</strong><br><sub>Gaussian for molecular work; VASP, QE and CP2K for periodic work, with license and process boundaries preserved.</sub></td>
<td width="25%" valign="top"><strong>Profile-gated acceleration</strong><br><sub>CPU/GPU, native code, ML and HPC advance only after equivalence and evidence gates.</sub></td>
</tr>
</table>

```text
planned
→ prepared
→ completed
→ technically validated
→ scientifically accepted
→ claim accepted
```

<p align="center">
  <img src="assets/demo/workflow-architecture.svg" width="100%" alt="TsaoDFT auditable research loop synthetic demonstration">
</p>

## Eight Skills, one evidence chain

| Skill | Primary responsibility | Boundary that cannot be bypassed |
|---|---|---|
| [`tsao-dft-suite`](skills/tsao-dft-suite/) | DFT-first entry point, DAGs, cross-Skill routing, cost and approval gates | Coordinates work; does not replace engine-level scientific judgment |
| [`tsao-structure-prep`](skills/tsao-structure-prep/) | Molecules, crystals, surfaces, defects, adsorption, atom mapping and neighbor search | Does not silently decide charge, spin, oxidation state, termination or protonation |
| [`tsao-dft-researcher`](skills/tsao-dft-researcher/) | Gaussian DFT/TDDFT, Opt/Freq, TS/IRC, thermochemistry, NMR, Multiwfn and VMD | Real programs, licenses and execution environments are supplied by the user |
| [`tsao-periodic-dft-materials`](skills/tsao-periodic-dft-materials/) | VASP, Quantum ESPRESSO, CP2K, surfaces/defects, bands/DOS, NEB and convergence | Does not redistribute restricted data or mix incompatible energies |
| [`tsao-dft-ml-active-learning`](skills/tsao-dft-ml-active-learning/) | DFT-label audit, leakage control, applicability domain, uncertainty and active learning | High scores are not mechanisms or causal evidence |
| [`tsao-dft-kinetics-multiscale`](skills/tsao-dft-kinetics-multiscale/) | Eyring/TST, reaction networks, detailed balance, uncertainty propagation and reactor handoff | Consumes only standard-state and thermochemical evidence that passed validation |
| [`tsao-dft-hpc-provenance`](skills/tsao-dft-hpc-provenance/) | Windows/POSIX, Slurm/PBS, hardware inventory, parsers, benchmarks, signatures and content-addressed evidence | GPU allocation, a fastest single run or a synthetic fixture is not real acceleration |
| [`tsao-dft-catalysis-profile`](skills/tsao-dft-catalysis-profile/) | Catalysis and polymer-specific profiles | Does not automatically generalize to unrelated systems |

## Implemented software-acceleration layers

### 1. Structure neighbor search

`skills/tsao-structure-prep/scripts/neighbor_list.py` is the first governed repository-owned numerical core:

- `reference`: scalar all-pairs reference;
- `numpy`: bounded-memory row-vectorized execution;
- `cell-list`: neighboring occupied-cell candidate enumeration;
- `auto`: NumPy for medium structures and cell-list for large structures;
- non-periodic, orthogonal periodic, triclinic periodic and partially periodic cells;
- one minimum-image definition and deterministic pair order across all backends;
- fail-closed coordinates, cutoffs, periodic flags and cell matrices;
- no implicit GPU selection.

```bash
python skills/tsao-structure-prep/scripts/inspect_xyz.py structure.xyz \
  --backend cell-list \
  --json

python skills/tsao-structure-prep/scripts/inspect_xyz.py periodic.xyz \
  --backend cell-list \
  --periodic xyz \
  --box 10 0 0 0 10 0 0 0 10 \
  --json
```

`pair_count` and `evaluated_pair_count` establish a change in candidate enumeration only. They are not DFT-engine performance evidence.

### 2. Shared mmap parser transport

`skills/tsao-dft-hpc-provenance/scripts/engine_scan_core.py` provides:

- read-only mmap;
- SHA-256 of the mapped artifact;
- bounded literal and regular-expression scans;
- last-marker and block boundaries;
- deterministic resource disposal.

The Gaussian, VASP, QE and CP2K paths in `engine_parser_contract.py` all consume this core while preserving fatal-over-success precedence, final-Link1 semantics, non-finite rejection and compatibility with retained public entry points. Parser I/O optimization is not electronic-structure acceleration.

## Current and future compute layers

| Layer | State | Technology | Evidence required |
|---|---|---|---|
| Scientific control plane | Implemented | Python, JSON Schema, YAML, structured argv | Permanent Linux and Windows gates |
| CPU numerical reference | Implemented | Scalar code, NumPy, BLAS/LAPACK | Determinism, finite values, regression equivalence |
| Cell-list neighbor core | Implemented | NumPy + grid candidate reduction | Reference/NumPy/cell-list equivalence |
| mmap parser transport | Implemented | mmap, byte regex, SHA-256 | Four-engine state-machine regression |
| C++/OpenMP sidecar | Not established | C++20, narrow JSON/file protocol | Profiling, Windows/Linux builds, sanitizers, fallback |
| CUDA/HIP/SYCL | Not established | Optional device plugins | Explicit device identity, CPU/GPU equivalence, end-to-end benchmark |
| External-engine acceleration | `EXTERNAL_HOLD` | Official engine GPU/MPI builds | License, build/site/run/hardware, ≥3 repeats, verified artifacts |

<p align="center">
  <img src="assets/demo/hybrid-compute-architecture.svg" width="100%" alt="Hybrid Python native and external-engine architecture">
</p>

## Acceleration registry and interpretation

Canonical source:

```text
skills/tsao-dft-hpc-provenance/scripts/acceleration_registry.py
```

It centralizes backends, vendors, aliases, eligible workloads and invalid interpretations. Permanent gates reject planners that reintroduce mirror catalogs.

| Route | Valid use | Invalid interpretation |
|---|---|---|
| cuBLAS / cuSOLVER | Large repeated dense linear algebra with data resident on device | “Python is automatically accelerated” |
| cuSPARSE | Profiled sparse problems | Generic optimization for small dense tables |
| cuFFT / cuFFTMp | Official engine integration or an explicit repository-owned FFT kernel | A wrapper automatically accelerates VASP/QE/CP2K |
| cuTENSOR | Profiled custom high-order tensor contraction | A universal external-DFT switch |
| cuEquivariance | Accepted MACE/NequIP/e3nn-class models | A Kohn–Sham DFT accelerator |
| NCCL / NVSHMEM | Compatible multi-GPU and distributed communication | Generic parser, small-file or single-GPU optimization |
| ROCm / oneAPI / Metal | Explicit vendor and workload routes | Automatic conversion of another vendor's build |

<table>
<tr>
<td width="50%"><img src="assets/demo/cuda-x-decision-map.svg" width="100%" alt="CUDA-X library decision map"></td>
<td width="50%"><img src="assets/demo/acceleration-registry-governance.svg" width="100%" alt="Canonical acceleration registry governance"></td>
</tr>
<tr>
<td><img src="assets/demo/backend-portability-stack.svg" width="100%" alt="Backend portability stack"></td>
<td><img src="assets/demo/native-acceleration-roadmap.svg" width="100%" alt="Profile-gated native acceleration roadmap"></td>
</tr>
</table>

## Professional external-engine boundary

- **VASP:** only a version-matched official GPU/OpenACC build, CUDA-aware MPI, GPU/rank binding and complete build fingerprint are eligible.
- **Quantum ESPRESSO:** records version, compiler, GPU support, MPI, pool/task-group and diagonalization path.
- **CP2K:** records official CUDA/HIP/OpenCL build capability and real execution identity.
- **Gaussian:** the repository owns preflight, parsing, batching and evidence; it does not claim electronic-structure acceleration unless the installed product explicitly provides such a route.

Different engines, builds, sites or hardware identities cannot be merged into one speedup campaign.

<p align="center">
  <img src="assets/demo/windows-linux-execution-matrix.svg" width="100%" alt="Windows and Linux execution matrix">
</p>

## Evidence contracts and qualification chain

The machine contracts enforce:

- canonical nested benchmark-result v1.1;
- canonical compute-campaign v1.1;
- legacy v1.0 only through central migration;
- custom Schemas are not qualification inputs;
- recursively frozen `CampaignConfig` and `CampaignDocument`;
- explicit role, run, site, build, hardware, multi-GPU, scientific-identity and artifact invariants;
- fail-closed unknown/mixed versions, additional fields, duplicate keys, type confusion and NaN/Infinity;
- migrations apply no defaults, create no evidence and cannot promote qualification.

```bash
python scripts/validate_benchmark_contract.py --json
python scripts/validate_compute_qualification.py --json
python scripts/capture_compute_contract_evidence.py --json
```

Machine-evidence Schema v1.5 records:

```text
python_control_plane: true
whole_repo_cpp_rewrite: NOT_RECOMMENDED
neighbor_search.implemented: true
parser_scan.implemented: true
native_sidecar.implemented: false
cuda_kernels.implemented: false
external_engine_acceleration: EXTERNAL_HOLD
external_engine_invoked: false
performance_ratio_published: false
```

<p align="center">
  <img src="assets/demo/evidence-qualification-pipeline.svg" width="100%" alt="Scoped acceleration evidence qualification pipeline">
</p>

<p align="center">
  <img src="assets/demo/scientific-acceleration-funnel.svg" width="100%" alt="Scientific acceleration qualification funnel">
</p>

## ML, kinetics and edge computing

The accepted edge path is not full production DFT on an edge device. It is:

```text
structure and conditions
→ accepted surrogate
→ uncertainty / OOD gate
→ safe-domain inference
→ remote real-DFT fallback outside the domain
→ accepted results returned to the governed dataset
```

Model version, training-data hash, feature definition, calibration, OOD threshold and fallback are mandatory. Surrogate inference and real DFT remain separate evidence classes.

<table>
<tr>
<td width="50%"><img src="assets/demo/dft-ml-dashboard.svg" width="100%" alt="DFT ML provenance-aware dashboard"></td>
<td width="50%"><img src="assets/demo/edge-hpc-closed-loop.svg" width="100%" alt="Edge to HPC scientific feedback loop"></td>
</tr>
<tr>
<td><img src="assets/demo/multiscale-kinetics.svg" width="100%" alt="DFT to kinetics multiscale handoff"></td>
<td><img src="assets/demo/periodic-dft-materials.svg" width="100%" alt="Periodic DFT evidence chain"></td>
</tr>
</table>

## Scientific-figure governance

The following figures are marked `SYNTHETIC DEMO · NOT SCIENTIFIC DATA`. They demonstrate figure contracts and evidence organization, not production results.

<table>
<tr>
<td width="50%"><img src="assets/demo/wavefunction-esp-gallery.svg" width="100%" alt="Wavefunction and ESP figure contract"></td>
<td width="50%"><img src="assets/demo/scientific-acceleration-funnel.svg" width="100%" alt="Scientific evidence funnel"></td>
</tr>
</table>

See [`docs/README_VISUAL_DESIGN_SYSTEM.md`](docs/README_VISUAL_DESIGN_SYSTEM.md) for the visual system and [`docs/AI_IMAGE_GOVERNANCE.md`](docs/AI_IMAGE_GOVERNANCE.md) for AI-image governance.

## Install and validate

```bash
python scripts/install.py \
  --agent codex \
  --scope project \
  --skill all \
  --dry-run \
  --validate

python scripts/quality_gate.py
```

PowerShell:

```powershell
pwsh -NoProfile -File .\scripts\quality_gate.ps1
```

Additional contracts:

- [`docs/ENGINE_SUPPORT_MATRIX.md`](docs/ENGINE_SUPPORT_MATRIX.md)
- [`docs/DFT_VALIDATION_LADDER.md`](docs/DFT_VALIDATION_LADDER.md)
- [`docs/CROSS_SKILL_HANDOFF.md`](docs/CROSS_SKILL_HANDOFF.md)
- [`docs/CAPABILITY_STATUS.yaml`](docs/CAPABILITY_STATUS.yaml)

## Permanent qualification gates

Every `main` HEAD must pass:

```text
Python 3.10
Python 3.12
Python 3.13
Windows PowerShell
Dependency audit + CycloneDX SBOM
CodeQL
28/28 repository quality stages
629 tests / 9 suites
```

Current formal software evidence:

| Platform | Statement | Branch | Result |
|---|---:|---:|---|
| Linux Python 3.12 | 93.87% | 83.86% | PASS |
| Windows Python 3.12 | 93.81% | 83.70% | PASS |
| `engine_parser_contract.py` | 100.00% | 100.00% | core gate PASS |
| `neighbor_list.py` | 98.29% | 95.10% | equivalence gate PASS |

These figures establish tested software artifacts. They do not establish acceleration of an external DFT engine. External execution and performance qualification remain `EXTERNAL_HOLD`.

---

**TsaoDFT does not optimize for making every file look more “low level.” It optimizes for making every scientific claim, performance claim and engineering migration reviewable against an explicit evidence boundary.**

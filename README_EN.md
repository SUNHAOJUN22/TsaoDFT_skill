# TsaoDFT Skill

<p align="center">
  <strong>A DFT-first, mathematical, evidence-locked and auditable research operating system for molecular and periodic systems</strong><br>
  Python scientific control plane + verifiable numerical cores + professional external engines + machine-readable qualification boundaries
</p>

<p align="center">
  <a href="README.md">中文</a> · <a href="README_EN.md">English</a>
</p>

<p align="center">
  <a href="https://github.com/SUNHAOJUN22/TsaoDFT_skill/actions/workflows/ci.yml"><img src="https://github.com/SUNHAOJUN22/TsaoDFT_skill/actions/workflows/ci.yml/badge.svg?branch=main" alt="CI"></a>
  <img src="https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-3776AB" alt="Python 3.11, 3.12 and 3.13">
  <img src="https://img.shields.io/badge/tests-see%20current%20CI-64748B" alt="Tests: inspect the current commit CI">
  <img src="https://img.shields.io/badge/quality%20gates-29%20defined-64748B" alt="29 required quality gates">
  <img src="https://img.shields.io/badge/software-static%20preflight-64748B" alt="Static preflight is not executed acceptance">
  <img src="https://img.shields.io/badge/external%20qualification-EXTERNAL__HOLD-B45309" alt="External qualification EXTERNAL HOLD">
  <img src="https://img.shields.io/badge/license-MIT-16A34A" alt="MIT license">
</p>

> **AI image declaration | AI-GENERATED CONCEPTUAL ILLUSTRATION:** The localized AI vision images, governed archival cover and AI-assisted SVGs communicate system architecture, mathematical contracts and usage strategy only. Molecules, lattices, orbitals, bands, energy surfaces, servers and interfaces are not data produced by Gaussian, VASP, Quantum ESPRESSO, CP2K, Multiwfn, VMD or experiments. Every technical figure is labelled `SYNTHETIC DEMO · NOT SCIENTIFIC DATA`; quantitative claims must come from accepted inputs, outputs, parsers, hashes and machine evidence.

<!-- LOCALIZED_VISION_EN:START -->
## Project vision: from Kohn–Sham equations to molecular and materials evidence

<p align="center">
  <img src="docs/assets/vision-en.png" width="100%" alt="TsaoDFT English first-principles workflow and mathematical evidence architecture">
</p>

> The equations explain method identity, periodic geometry, parsing, SCF and evidence gates in the code. The figure is not electron density, a band structure, an orbital or a real DFT result.

> The Eyring equation in this concept image is the unimolecular baseline. Bimolecular and higher-order steps require the standard-concentration factor and barrier reference contract below.

<!-- LOCALIZED_VISION_EN:END -->

<p align="center">
  <img src="assets/ai/hero/tsao-dft-hero.svg" width="100%" alt="TsaoDFT evidence-first DFT research operating system conceptual overview">
</p>


## Delivery scope and code-backed entry points

TsaoDFT organizes structure checks, periodic-log parsing, rate calculations, machine-learning baselines and computation evidence as independent Python tools. It ships testable contracts, reference algorithms and handoff files. Electronic-structure calculations still require a configured Gaussian, VASP, Quantum ESPRESSO or CP2K installation. The project vision is to trace every reported number to an input, method, final job and review record.

| Task | Implemented entry point | Output and boundary |
| --- | --- | --- |
| Structure and periodic geometry | `skills/tsao-structure-prep/scripts/inspect_xyz.py` | Atomic geometry, neighbors and algorithm equivalence; no electronic-density calculation |
| Periodic-output verification | `skills/tsao-periodic-dft-materials/scripts/parse_qe.py`, `parse_vasp.py`, `parse_cp2k.py` | Final-job convergence, energy, version, line/byte witnesses and full-artifact SHA-256 |
| Eyring rates and intervals | `skills/tsao-dft-kinetics-multiscale/scripts/eyring_rates.py`, `propagate_barrier_uncertainty.py` | kcal/mol barriers and kelvin; higher-order reactions require concentration, barrier reference state and activity convention |
| Ridge baseline | `skills/tsao-dft-ml-active-learning/scripts/train_ridge_baseline.py` | Fixed group splits, dataset/split hashes, predictions and model card; completion is `training_completed` / `UNQUALIFIED` |
| Scientific qualification and delivery | `scripts/quality_gate.py` | Executed software-gate receipt; software success does not certify an external engine or scientific conclusion |

### Install and run software gates

The supported Python floor is now **3.11**, with a 3.11 / 3.12 / 3.13 CI matrix. The 2026-10-21 dependency audit requires Pillow 13.0.0, which fixes eight vulnerabilities in the former 12.3.0 pin and requires Python >=3.11 upstream. Python 3.10 is therefore no longer supported. Create a fresh environment and use the matching `constraints/py311.txt`, `py312.txt` or `py313.txt`; do not reuse a Python 3.10 environment. certifi is also updated to 2026.10.19. Sources: [Pillow 13.0.0](https://pypi.org/project/Pillow/13.0.0/), [certifi advisory](https://github.com/advisories/GHSA-6q48-6c7w-9gw2).

Use an isolated Python 3.12 environment with the constrained dependencies. Store execution reports outside the checkout to keep machine-specific observations separate from source files.

```bash
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -c constraints/py312.txt -r requirements-dev.txt
python -m pip check
python scripts/run_all_tests.py
python scripts/quality_gate.py --report-dir ../tsao-dft-acceptance
```

The [seven-repository modification and six-hour acceptance prompt](docs/SEVEN_REPOSITORY_ACCEPTANCE_PROMPT.md) specifies parallel delivery. Its runner counts two sequential 10,800-second totals of successful test-process elapsed time. Installation, queues, idle waits and failed runs contribute no time. A complete independently checked receipt set is required; this is segmented regression, not uninterrupted service-soak qualification.

### Higher-order rates require a barrier reference state

For an elementary step of molecularity $m$, concentrations expressed numerically in mol/L and activity convention $a=c/c^\circ$:

$$
k_m=\kappa g\frac{k_B T}{h}\exp\left(-\frac{\Delta G^\ddagger_{c^\circ}}{RT}\right)(c^\circ)^{1-m},
\qquad [k_m]=\mathrm{M}^{1-m}\mathrm{s}^{-1}.
$$

The implementation evaluates $\ln k_m=\ln\kappa+\ln g+\ln(k_BT/h)-\Delta G^\ddagger/(RT)+(1-m)\ln c^\circ$. `standard_state` and `barrier_standard_state` must agree. Otherwise calculation fails until the researcher supplies a justified reference-state conversion. Holding the **numerical barrier** fixed while changing 1 M to 0.1 M multiplies a bimolecular rate by ten. This tests the concentration factor; it is not a claim that a consistent reference-state transformation changes a physical prediction.

```bash
python skills/tsao-dft-kinetics-multiscale/scripts/eyring_rates.py \
  skills/tsao-dft-kinetics-multiscale/examples/catalysis/barriers.csv --temperature 298.15 --out ../rates.csv
python skills/tsao-dft-kinetics-multiscale/scripts/propagate_barrier_uncertainty.py \
  --barrier 15 --uncertainty 1 --temperature 298.15 --molecularity 2 \
  --standard-state '1 M' --barrier-standard-state '1 M' --activity-convention 'a=c/c0'
```

For a declared symmetric barrier bound $u_G$, $k_{\min,\max}=\exp[\ln k_m\mp u_G/(RT)]$. This interval excludes functional, solvent, transport and pathway uncertainty. Very small rates may underflow to zero while JSON retains their log rates. Overflow and nonfinite inputs are rejected.

### Periodic logs: numerical evidence belongs to the final job

```bash
python skills/tsao-periodic-dft-materials/scripts/parse_qe.py pw.out
python skills/tsao-periodic-dft-materials/scripts/parse_vasp.py OUTCAR
python skills/tsao-periodic-dft-materials/scripts/parse_cp2k.py cp2k.out
```

All three entry points share a bounded line reader: at most 1 MiB per line, 1 GiB per artifact and 10,000 jobs. Exceeding a bound fails explicitly. A new job resets version, energy and convergence, so an empty final job cannot inherit an earlier energy. When `source_complete=false`, the hash covers consumed bytes only and cannot qualify a complete artifact. NaN, infinity, nonzero literals rounded to zero and unit-conversion overflow are rejected; finite small values remain valid. Accepted parsing still reports `scientific_acceptance=PENDING`.

### Machine learning: distinguish completed training from scientific approval

An existing `split` column is preserved and must use `train`, `valid` or `test`; a parent group may not span splits. A fixed-seed group split is used only when that column is absent. Features cannot include the target or group identifier. The model card records the raw CSV SHA-256, split hash and explicit `UNQUALIFIED` state.

```bash
python skills/tsao-dft-ml-active-learning/scripts/train_ridge_baseline.py dataset.csv \
  --features descriptor_a,descriptor_b --target energy_eV --group parent_id \
  --out-dir ../ridge-baseline
```

Optional `--validation-artifact validation.json` additionally binds the report schema, dataset hash, sample count, split hash and method fingerprints to this run. Identity checks on a supplied report do not perform independent scientific review. Report errors on a fixed held-out set; discuss generalization only after group isolation. Ensemble spread and OOD scores do not replace calibration.

## Acceptance state and modification specification

- Static preflight uses `SOFTWARE_PREFLIGHT_READY`; legacy `SOFTWARE_ACCEPTANCE_READY` is not evidence of executed acceptance. Require this run's `quality-run-acceptance.json` state `SOFTWARE_GATES_PASSED` and success of all required CI jobs;
- Real Gaussian/VASP/QE/CP2K correctness and performance: `EXTERNAL_HOLD`;
- Machine acceptance: `python scripts/build_release_acceptance.py --out release-acceptance.json --json`;
- Reusable modification prompt: [`docs/ACCEPTANCE_REWRITE_PROMPT.md`](docs/ACCEPTANCE_REWRITE_PROMPT.md);
- Governing doctrine: [`docs/ACCELERATION_ENGINEERING_DOCTRINE.md`](docs/ACCELERATION_ENGINEERING_DOCTRINE.md).

```bash
python scripts/capture_compute_contract_evidence.py --out compute-contract-evidence.json --json
python scripts/build_release_acceptance.py --out release-acceptance.json --json
python scripts/quality_gate.py
```

## Governing engineering doctrine

1. **Python is the scientific control plane.** It owns workflow, Schemas, method identity, scheduling, parsing, evidence and reporting; it is not a defect requiring a wholesale C++ rewrite.
2. **Professional DFT kernels remain external.** FFTs, eigensolvers, integrals, SCF and MPI/OpenMP/GPU kernels belong to versioned Gaussian/VASP/QE/CP2K builds.
3. **Only profiled narrow hotspots may migrate.** CPU reference → NumPy/algorithm → optional C++/OpenMP → optional CUDA/HIP/SYCL.
4. **Every backend retains a deterministic reference, finite-number boundary, safe fallback and equivalence gate.**
5. **Technology awareness is not execution evidence.** CUDA-X awareness, a detected GPU or a generated job is not speedup evidence.
6. **Correctness qualification precedes performance qualification.** No speed ratio is published without a fixed input, real engine, license, stable build/site/run/hardware identity, scientific tolerances and repeated runs.

<p align="center">
  <img src="assets/demo/workflow-architecture.svg" width="100%" alt="TsaoDFT auditable research loop synthetic demonstration">
</p>

## Capability levels are evidence contracts

Public capability statements use four evidence levels:

- `L0_REFERENCE`: reference material, templates or method guidance; no executable-adapter claim.
- `L1_HANDOFF`: produces a structured handoff while execution and scientific acceptance remain downstream responsibilities.
- `L2_VALIDATED_ADAPTER`: the adapter, Schema, strict input boundary and regression suite are validated; this is not proof of execution on a real licensed professional engine or target device.
- `L3_EXECUTION_TESTED`: must bind real `engine/version/site/run_id` and immutable artifact SHA-256. HPC or acceleration L3 additionally binds build/hardware identity, a CPU reference, at least three repeats, numerical equivalence, parser acceptance, performance policy, a content-addressed evidence root and independent signed review.

The repository neighbor-list, bounded periodic stream parser, unified mmap parser, contract validators and release-acceptance builder are permanently tested software artifacts. They do not automatically promote external Gaussian, VASP, QE or CP2K capability to `L3_EXECUTION_TESTED`.

## Mathematical core: mapping equations to software contracts

The equations below explain workflow and validation contracts. They are not scientific outputs already computed by this repository.

### 1. Kohn–Sham equation and electron density

$$
\hat H_{\mathrm{KS}}[\rho]\,\psi_i(\mathbf r)=\varepsilon_i\psi_i(\mathbf r),
\qquad
\rho(\mathbf r)=\sum_i f_i\lvert\psi_i(\mathbf r)\rvert^2.
$$

Repository strategy:

- `method_fingerprint_id` freezes functional, basis/pseudopotential, dispersion, relativity, cutoffs and convergence settings;
- `observable_set` declares energies, forces, stresses and additional properties;
- results from different engines, pseudopotential families or standard states are never silently merged.

### 2. Total-energy functional and SCF fixed point

$$
E[\rho]=T_s[\rho]+\int v_{\mathrm{ext}}(\mathbf r)\rho(\mathbf r)\,d\mathbf r
+E_H[\rho]+E_{\mathrm{xc}}[\rho]+E_{\mathrm{II}},
$$

$$
\rho^{(n+1)}=\mathcal F[\rho^{(n)}],
\qquad
R_n=\left\|\rho^{(n+1)}-\rho^{(n)}\right\|,
\qquad
R_n\le \tau_\rho.
$$

The evidence contract requires parser acceptance, zero exit status, convergence and finite values. An earlier success marker cannot override a later fatal marker.

Numeric ingestion also distinguishes genuine zero from nonzero underflow. With $\operatorname{fl}(x)$ denoting conversion from a decimal source literal to the runtime floating-point representation, the input boundary requires

$$
\operatorname{isfinite}(\operatorname{fl}(x))
\quad\land\quad
\bigl(x=0\;\lor\;\operatorname{fl}(x)\ne0\bigr).
$$

The public Gaussian parser applies this check to parsed energies, frequencies, orbitals, coordinates and other numeric fields. Overflow or nonzero underflow returns `parser_accepted=false`, `NUMERIC_RANGE_ERROR`, a nonzero exit code and strict JSON. Benchmark evidence, qualification, EngineCapability, bridge and trust-boundary JSON readers also reject nested duplicate keys, `NaN`, `Infinity` and nonzero underflow; JSONL records use the same rule. YAML readers for benchmark evidence, EngineCapability, the bridge and qualification policies likewise reject explicit duplicate keys, nonfinite numbers and nonzero underflow while preserving valid `<<` merges, merge-list precedence and explicit overrides of inherited values. JSON/YAML campaign tolerances cannot silently turn tiny nonzero numbers into zero. Genuine signed zeros, representable subnormals and JSON integer values remain intact. Resolve range errors through an explicit unit or representation change, not by replacing the input with zero to obtain a pass. Readers cannot reconstruct precision already lost by a caller before serialization.

The unified mmap parser also checks range after Hartree/Ry-to-eV, force and pressure conversions: a finite source value can still overflow or underflow when scaled. Out-of-range force rows cannot be silently discarded to produce apparently complete data. These checks concern software parsing; `scientific_acceptance` still requires independent scientific review.

Engine parser v1.2 emits QE forces only when the final force block in the final PWSCF job declares `Ry/au`, has a known atom count, contains exactly one three-component row for each atom index `1..N`, and closes with a `Total force` line. The result is a flat `3N` array ordered `x,y,z` per atom, converted with the project's fixed CODATA 2018 Rydberg and Bohr constants. This is the benchmark bridge's flat storage shape; it does not by itself satisfy the `TypedQuantity` contract, which requires an `N×3` shape and exact `atom_mapping`. QE `Total force` is a scalar norm and `P=` is scalar pressure; CP2K `Max. gradient` is also scalar. None is emitted as a force vector or stress tensor. Missing, unsupported-unit or incomplete data remains `null` with a warning, while the original output remains hash-addressed evidence. `parser_accepted` termination/SCF gates do not imply that all scientific observables are present. See [`engine_parser_contract.py`](skills/tsao-dft-hpc-provenance/scripts/engine_parser_contract.py).

The benchmark bridge accepts a parser result only when it is bound to the supplied output: `parser_result.engine` must match the bridge engine and `source_artifact.sha256` must match the output file read by the bridge. If a parser result also supplies `size_bytes`, the file size must match. A failed binding sets parser acceptance to false and records the reason in `evidence_source.missing_fields`. These fields show that the parsed bytes match the cited output file; they do not prove which executable or HPC job produced it. Process exit status must come from runtime or scheduler evidence: `runtime.exit_status` is primary, with `scheduler_metrics.exit_status` as fallback when runtime status is absent. If both are present, they must agree. Missing, invalid or conflicting statuses are recorded as `execution.exit_status = -1` (unknown) with a reason in `missing_fields`; the bridge never infers zero from a normal-termination marker. Parser acceptance and successful process exit are separate; performance evidence requires both parser acceptance and exit status zero.

### 3. Forces, stress and geometry acceptance

$$
\mathbf F_I=-\frac{\partial E}{\partial \mathbf R_I},
\qquad
\sigma_{\alpha\beta}=\frac{1}{\Omega}\frac{\partial E}{\partial\epsilon_{\alpha\beta}}.
$$

Geometry optimization must be accepted together with gradients, displacements, frequencies or constraints. A transition state is not accepted from optimization convergence alone; it normally requires one targeted imaginary mode and IRC or equivalent path evidence.

### 4. Periodic systems, plane waves and Brillouin-zone integration

$$
A=\frac{1}{\Omega_{\mathrm{BZ}}}\int_{\mathrm{BZ}}A(\mathbf k)\,d\mathbf k
\approx \sum_{\mathbf k}w_{\mathbf k}A(\mathbf k),
$$

$$
\frac{\lvert\mathbf k+\mathbf G\rvert^2}{2}\le E_{\mathrm{cut}}.
$$

k-point meshes, cutoff energy, smearing, pseudopotentials, magnetism and supercell identity remain explicit. Band/DOS convergence and total-energy convergence are accepted separately.

### 5. Periodic minimum image and cell lists

The implementation uses NumPy **row-vector** convention: lattice vectors are rows of $\mathbf H$, so Cartesian displacements satisfy $\Delta\mathbf r=\Delta\mathbf s\mathbf H$. For a general triclinic cell, component-wise `round()` is guaranteed to select the closest periodic image only in special cases such as orthogonal boxes. The general definition is a closest-lattice-point problem over the enabled periodic axes $\mathcal P$:

$$
\mathbf n^\star=
\operatorname*{arg\,min}_{\mathbf n\in\mathbb Z_{\mathcal P}}
\left\|\Delta\mathbf r-\mathbf n\mathbf H\right\|_2,
\qquad
\Delta\mathbf r_{\mathrm{MIC}}
=\Delta\mathbf r-\mathbf n^\star\mathbf H.
$$

For orthogonal boxes, that reduces to the fast path

$$
\Delta\mathbf s_{\mathrm{MIC}}
=\Delta\mathbf s-\operatorname{round}_{\mathcal P}(\Delta\mathbf s),
\qquad
\Delta\mathbf r_{\mathrm{MIC}}
=\Delta\mathbf s_{\mathrm{MIC}}\mathbf H,
\qquad
d_{ij}=\lVert\Delta\mathbf r_{\mathrm{MIC}}\rVert_2.
$$

`neighbor_list.py` uses a bounded closest-lattice enumeration for skewed cells and enforces `MAX_MINIMUM_IMAGE_CANDIDATES` as a resource ceiling; pathological cells fail closed instead of falling back to an incorrect component-wise rounding approximation. The all-pairs reference is $O(N^2)$. At finite density and fixed cutoff, the average cell-list candidate cost approaches

$$
O\!\left(N+N\,\bar n_{\mathrm{cell}}\right).
$$

The `reference`, `numpy` and `cell-list` backends must return the same deterministically ordered pair set.

### 6. Numerical equivalence, tolerances and performance qualification

$$
\lvert x-x_{\mathrm{ref}}\rvert
\le a_{\mathrm{tol}}+r_{\mathrm{tol}}\lvert x_{\mathrm{ref}}\rvert,
$$

$$
S=\frac{\operatorname{median}(t_{\mathrm{reference}})}
        {\operatorname{median}(t_{\mathrm{candidate}})},
\qquad n_{\mathrm{repeat}}\ge 3.
$$

$S$ is reviewable only after stable input/method/build/hardware/site identity, unique run IDs, accepted parsers, `VERIFIED` artifacts and scientific equivalence. Otherwise the state remains `EXTERNAL_HOLD`.

### 7. Kinetics and detailed balance

$$
k(T)=\kappa\frac{k_{\mathrm B}T}{h}\exp\!\left(-\frac{\Delta G^\ddagger}{RT}\right),
$$

$$
\frac{k_f}{k_r}=\exp\!\left(-\frac{\Delta G_{\mathrm{rxn}}}{RT}\right).
$$

The unimolecular expression assumes $m=1$ and $g=1$. Higher-order steps use the concentration factor and barrier reference contract above. The forward/reverse ratio connects to a thermodynamic equilibrium constant only under consistent activities, standard states and partition definitions; concentration-rate ratios require the relevant standard-concentration power. The CLI validates declarations, not the scientific validity of supplied thermochemistry.

### 8. ML uncertainty and OOD gating

For ensemble predictions $\{\hat y_m(\mathbf x)\}$:

$$
\bar y(\mathbf x)=\frac1M\sum_{m=1}^M\hat y_m(\mathbf x),
\qquad
u^2(\mathbf x)=\frac1{M-1}\sum_{m=1}^M\left(\hat y_m-\bar y\right)^2.
$$

If $u(\mathbf x)>u_{\max}$ or an OOD score exceeds its threshold, the workflow should pause predictions and request real DFT verification. This is a workflow policy; the baseline script does not launch a remote solver.

<p align="center">
  <img src="assets/demo/dft-mathematical-core.svg" width="100%" alt="Kohn-Sham mathematics mapped to TsaoDFT software contracts">
</p>

<p align="center">
  <img src="assets/demo/qualification-mathematics.svg" width="100%" alt="Numerical equivalence and performance qualification mathematics">
</p>

## Eight Skills, one evidence chain

| Skill | Primary responsibility | Acceptance boundary |
|---|---|---|
| [`tsao-dft-suite`](skills/tsao-dft-suite/) | DFT-first entry point, DAGs, approvals and cross-Skill routing | Coordinates work; does not replace engine science |
| [`tsao-structure-prep`](skills/tsao-structure-prep/) | Molecules, crystals, surfaces, defects, adsorption, atom mapping and neighbor search | Does not silently choose charge, spin, oxidation state, termination or protonation |
| [`tsao-dft-researcher`](skills/tsao-dft-researcher/) | Gaussian DFT/TDDFT, Opt/Freq, TS/IRC, thermochemistry, NMR, Multiwfn and VMD | The user supplies real programs, licenses and execution environments |
| [`tsao-periodic-dft-materials`](skills/tsao-periodic-dft-materials/) | VASP, QE, CP2K, surfaces/defects, bands/DOS, NEB and convergence | Does not mix incompatible energies or pseudopotential identities |
| [`tsao-dft-ml-active-learning`](skills/tsao-dft-ml-active-learning/) | Label audit, leakage control, applicability domain, uncertainty and active learning | High scores are not mechanisms or causal evidence |
| [`tsao-dft-kinetics-multiscale`](skills/tsao-dft-kinetics-multiscale/) | Eyring/TST, reaction networks, detailed balance and uncertainty propagation | Consumes only accepted standard-state and thermochemical data |
| [`tsao-dft-hpc-provenance`](skills/tsao-dft-hpc-provenance/) | Windows/POSIX, Slurm/PBS, hardware inventory, parsers, benchmarks and signatures | GPU allocation or one fastest run is not real speedup |
| [`tsao-dft-catalysis-profile`](skills/tsao-dft-catalysis-profile/) | Catalysis and polymer profiles | Does not automatically generalize to unrelated systems |

## Executable usage strategies

### Strategy A: structure preparation and neighbor search

```bash
python skills/tsao-structure-prep/scripts/inspect_xyz.py structure.xyz \
  --backend reference --json
python skills/tsao-structure-prep/scripts/inspect_xyz.py structure.xyz \
  --backend numpy --json
python skills/tsao-structure-prep/scripts/inspect_xyz.py periodic.xyz \
  --backend cell-list --periodic xyz \
  --box 10 0 0 0 10 0 0 0 10 --json
```

Use `reference` to establish small-system truth, then check `numpy` and `cell-list` equivalence. `evaluated_pair_count` is not DFT speedup evidence.

### Strategy B: unified parsers and artifact hashes

```bash
python skills/tsao-dft-hpc-provenance/scripts/engine_parser_contract.py \
  --engine gaussian --input job.log --json
python skills/tsao-dft-hpc-provenance/scripts/engine_parser_contract.py \
  --engine vasp --input OUTCAR --json
```

The parser uses read-only mmap, bounded scans and mapped-artifact SHA-256. Fatal markers outrank earlier success markers.

### Strategy C: Gaussian molecular workflow

1. Freeze charge, multiplicity, solvent, functional, basis, dispersion and integration grid;
2. Run preflight before Opt/Freq;
3. A minimum requires no imaginary frequency; a TS normally requires one targeted imaginary mode plus IRC/path evidence;
4. Wavefunction/ESP/Multiwfn/VMD figures retain source-artifact hashes.

### Strategy D: VASP / QE / CP2K periodic workflow

1. Converge cutoff, k points, smearing, magnetism, supercell and pseudopotential identity;
2. Then execute geometry, bands/DOS, defects, surfaces, NEB or phonons;
3. GPU routes require official version-matched builds and complete build/hardware/site/run identity;
4. Different engines, builds or sites never share one speedup campaign.

### Strategy E: HPC and Windows/Linux

```bash
python skills/tsao-dft-hpc-provenance/scripts/generate_job_script.py \
  --shell bash --scheduler slurm --json
pwsh -NoProfile -File .\scripts\quality_gate.ps1
```

External programs cross structured argv, versioned JSON, files, return codes and content hashes; untrusted shell concatenation is not allowed.

### Strategy F: qualification evidence

```bash
python scripts/validate_benchmark_contract.py --json
python scripts/validate_compute_qualification.py --json
python scripts/capture_compute_contract_evidence.py --out compute-contract-evidence.json --json
python scripts/build_release_acceptance.py --out release-acceptance.json --json
```

<p align="center">
  <img src="assets/demo/evidence-qualification-pipeline.svg" width="100%" alt="Scoped acceleration evidence qualification pipeline">
</p>

<p align="center">
  <img src="assets/demo/scientific-acceleration-funnel.svg" width="100%" alt="Scientific acceleration qualification funnel">
</p>

## Implemented software acceleration layers

| Layer | State | Implementation | Non-claim |
|---|---|---|---|
| Python scientific control plane | Implemented | Schemas, DAG, argv, parsers, evidence | Not an electronic-structure kernel |
| CPU reference | Implemented | Scalar, NumPy, BLAS/LAPACK | Not automatically optimal performance |
| neighbor list | Implemented | reference / NumPy / cell-list | Not external DFT speedup |
| mmap parser | Implemented | read-only mmap, byte regex, SHA-256 | Does not accelerate SCF/FFT/eigensolvers |
| C++/OpenMP sidecar | Not established | profile-gated | Must not be documented as complete |
| CUDA/HIP/SYCL | Not established | optional device plugins | GPU presence does not enable it |
| external-engine performance | `EXTERNAL_HOLD` | official engine GPU/MPI builds | no speed ratio published |

<p align="center">
  <img src="assets/demo/hybrid-compute-architecture.svg" width="100%" alt="Hybrid Python native and external-engine architecture">
</p>

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

## Windows, Linux and external-engine boundary

- VASP: only version-matched official OpenACC/GPU builds, CUDA-aware MPI, GPU/rank binding and build fingerprints are eligible;
- Quantum ESPRESSO: records version, compiler, GPU support, MPI, pool/task-group and diagonalization path;
- CP2K: records official CUDA/HIP/OpenCL build capability and real execution identity;
- Gaussian: the repository owns preflight, parsing, batching and evidence, not an unproven electronic-structure acceleration claim.

<p align="center">
  <img src="assets/demo/windows-linux-execution-matrix.svg" width="100%" alt="Windows and Linux execution matrix">
</p>

## ML, kinetics and edge loop

```text
structure and conditions
→ accepted surrogate
→ uncertainty / OOD gate
→ safe-domain inference
→ remote real-DFT fallback outside the domain
→ accepted results returned to the governed dataset
```

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

The following figures are synthetic demonstrations, not production computational results:

<table>
<tr>
<td width="50%"><img src="assets/demo/wavefunction-esp-gallery.svg" width="100%" alt="Wavefunction and ESP figure contract"></td>
<td><img src="assets/demo/scientific-acceleration-funnel.svg" width="100%" alt="Scientific evidence funnel"></td>
</tr>
</table>

See [`docs/README_VISUAL_DESIGN_SYSTEM.md`](docs/README_VISUAL_DESIGN_SYSTEM.md) and [`docs/AI_IMAGE_GOVERNANCE.md`](docs/AI_IMAGE_GOVERNANCE.md).

## Install, validate and accept

```bash
python scripts/install.py --agent codex --scope project --skill all --dry-run --validate
python scripts/validate_readme_math.py --json
python scripts/quality_gate.py
```

PowerShell:

```powershell
pwsh -NoProfile -File .\scripts\quality_gate.ps1
```

Permanent CI must pass Python 3.11/3.12/3.13, Windows PowerShell, dependency audit + CycloneDX SBOM, CodeQL and all 29/29 repository quality stages. The historical baseline was 630 tests / 9 suites; current counts and outcomes must come from the current commit run.

Static preflight validates repository contracts, not completed tests. Executed software acceptance requires the current commit quality receipt and CI results. External DFT execution and acceleration qualification remain `EXTERNAL_HOLD`.

---

**TsaoDFT is not designed to make every file look lower-level. It is designed to make every equation, parameter, computation, figure, performance claim and engineering migration auditable.**

<!-- CURRENT_MAIN_ACCEPTANCE_V2:START -->
## Current `main`: code–mathematics–evidence loop

<p align="center"><img src="docs/current-main/tsao-dft-current-main-en.svg" width="100%" alt="Current `main`: code–mathematics–evidence loop"></p>

> This figure is generated from current code contracts and is conceptual documentation, not electronic-structure run data.

### Core mathematical contracts

$$
\left[-\frac{1}{2}\nabla^2+V_{\mathrm{eff}}[n]\right]\psi_i=\varepsilon_i\psi_i
$$

$$
\mathbf n^\star=\operatorname*{arg\,min}_{\mathbf n\in\mathbb Z_{\mathcal P}}\lVert(\mathbf s-\mathbf n)\mathbf H\rVert_2
$$

$$
|\Delta E|\le\tau_E\quad\land\quad\max_i\lVert\Delta\mathbf F_i\rVert_2\le\tau_F
$$

### Usage strategy

1. Freeze structure, cell, periodicity and units before generating engine input.
2. Accept SCF, energy, forces and stress only when finite, converged and method identity is complete.
3. Discovery, templates and parser outputs must not be promoted to real DFT execution evidence.
4. Any new commit invalidates six-hour software evidence bound to an older SHA.

> **Responsibility boundary：** Software gates validate the control plane, reference numerics and evidence contracts only; external engines such as Gaussian, VASP, QE and CP2K are not executed here and remain EXTERNAL_HOLD.

Execution prompt: [SIX_REPOSITORY_PARALLEL_6H_ACCEPTANCE_PROMPT_V2.md](docs/SIX_REPOSITORY_PARALLEL_6H_ACCEPTANCE_PROMPT_V2.md)
<!-- CURRENT_MAIN_ACCEPTANCE_V2:END -->

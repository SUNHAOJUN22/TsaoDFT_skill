# TsaoDFT Skill

**Turn molecular, crystal and reaction questions into auditable computational evidence.** This repository provides a Python scientific control plane, deterministic reference algorithms, input checks, output parsers, kinetics and machine-learning baselines, and governed execution/evidence handoffs. Electronic-structure calculations are performed by separately configured professional engines such as Gaussian, VASP, Quantum ESPRESSO and CP2K.

[简体中文](README.md) · [Eight Skills](skills/) · [Engine support matrix](docs/ENGINE_SUPPORT_MATRIX.md) · [Architecture](docs/ARCHITECTURE.md) · [MIT license](LICENSE)

![English: molecules and crystals, evidence you can audit; synthetic AI concept, not measured data](docs/assets/readme-vnext/hero.en.svg)

**AI image declaration — AI-GENERATED CONCEPTUAL ILLUSTRATION.** The cover combines original AI artwork with code-checked English labels and outlined mathematical typography. Structures, fields and surfaces are synthetic concepts, not orbitals, electron densities, experimental observations or actual engine results. Equations describe software algorithms with explicit assumptions. [Provenance and SHA-256](docs/assets/readme-vnext/artwork-provenance.json) are validated with the assets; historical figures remain linked in the archive below.

## Delivery scope and status

[pyproject.toml](pyproject.toml) declares version `0.4.0a2` and **Python 3.11 or later**. Preparation, process completion, parser acceptance and scientific acceptance are recorded separately, including for examples, illustrations and model cards.

| Capability | Executable implementation | Outputs and limits |
|---|---|---|
| Molecular and periodic geometry | [inspect_xyz.py](skills/tsao-structure-prep/scripts/inspect_xyz.py), [neighbor_list.py](skills/tsao-structure-prep/scripts/neighbor_list.py) | Contacts, distances, deterministic neighbour pairs; XYZ alone cannot establish charge, multiplicity or chemical validity |
| Molecular input and output | [preflight_gaussian_input.py](skills/tsao-dft-researcher/scripts/preflight_gaussian_input.py), [parse_gaussian.py](skills/tsao-dft-researcher/scripts/parse_gaussian.py) | Method, termination, final-job, frequency/orbital observations; transition states and mechanisms still need review |
| Periodic input and output | [Periodic scripts](skills/tsao-periodic-dft-materials/scripts/) | VASP/QE/CP2K preflight, final-job parsing and convergence series; engines and pseudopotentials remain external |
| Reaction rates and bounds | [eyring_rates.py](skills/tsao-dft-kinetics-multiscale/scripts/eyring_rates.py), [propagate_barrier_uncertainty.py](skills/tsao-dft-kinetics-multiscale/scripts/propagate_barrier_uncertainty.py) | Eyring reference rates with explicit standard states and propagated barrier bounds; no automatic mechanism validation |
| Data and Ridge baseline | [train_ridge_baseline.py](skills/tsao-dft-ml-active-learning/scripts/train_ridge_baseline.py) | Isolated groups, training-only scaling, primal/dual solvers, predictions and model cards; completed training stays `UNQUALIFIED` |
| Execution and scientific evidence | [HPC/provenance](skills/tsao-dft-hpc-provenance/), [build_release_acceptance.py](scripts/build_release_acceptance.py) | Structured argv, input identity, hashes, signed review and qualification reports; external execution requires actual run evidence |

`SOFTWARE_PREFLIGHT_READY` describes static delivery preflight. The historical label `SOFTWARE_ACCEPTANCE_READY` is not proof of executed gates. Only a completed gate process can record `SOFTWARE_GATES_PASSED` in `quality-run-acceptance.json`; that receipt covers this process alone, and other required CI jobs must pass independently. External DFT correctness, site performance and scientific conclusions remain **`EXTERNAL_HOLD`** when their evidence is absent.

## Installation and first run

Run commands from the repository root. The Linux/macOS example uses Python 3.12; use `constraints/py311.txt` or `constraints/py313.txt` with the corresponding Python version. [requirements-dev.txt](requirements-dev.txt) and the constraints govern runtime and development dependencies. Software regression does not require installing an external DFT engine.

```bash
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -c constraints/py312.txt -r requirements-dev.txt
python -m pip check
```

All bundled examples below are **SYNTHETIC DEMO / NOT SCIENTIFIC DATA**. Write outputs to `../tsao-dft-demo`, outside the repository, and never select an original input as an output. For scientific runs, use a fresh directory and retain original bytes, environment identity and method identity.

### 1. Inspect structures before choosing a method

```bash
python skills/tsao-structure-prep/scripts/inspect_xyz.py \
  skills/tsao-structure-prep/examples/geometry-audit/water.xyz \
  --backend cell-list --json
```

XYZ lengths are in Å. The nine `--box` values are row lattice vectors; `--periodic` explicitly selects periodic axes. `auto` chooses a reference/NumPy/cell-list path by size, and the backends must agree on deterministically sorted pairs. Radius-based bonds are geometry heuristics, not authority to change valence or protonation.

### 2. Preflight molecular inputs and inspect periodic output

```bash
python skills/tsao-dft-researcher/scripts/preflight_gaussian_input.py \
  skills/tsao-dft-researcher/tests/fixtures/preflight.gjf --json
```

```bash
python skills/tsao-periodic-dft-materials/scripts/preflight_vasp.py \
  skills/tsao-periodic-dft-materials/examples/engine-adapters/vasp --json
python skills/tsao-periodic-dft-materials/scripts/parse_vasp.py \
  skills/tsao-periodic-dft-materials/examples/engine-adapters/vasp/OUTCAR
```

These commands read synthetic inputs and logs; they do not launch Gaussian or VASP. For actual Gaussian logs, use the positional input and `--json` of `parse_gaussian.py`; QE/CP2K use the output-file positional argument of `parse_qe.py`/`parse_cp2k.py`. The shared [engine_parser_contract.py](skills/tsao-dft-hpc-provenance/scripts/engine_parser_contract.py) is a Python import API and **has no `--engine gaussian` CLI**. A silent module invocation is not a successful parse.

Public periodic parsers stream bounded lines: at most 1 MiB per line, 1 GiB per file and 10,000 jobs. A new final job resets energy, version and convergence state; an empty trailing job cannot inherit an earlier success. With `source_complete=false`, the digest covers only consumed bytes and cannot attest the complete artifact. Passing termination/SCF gates does not establish that every observable exists; `scientific_acceptance` still awaits scientific review.

### 3. Calculate rates under an explicit standard state

```bash
python skills/tsao-dft-kinetics-multiscale/scripts/eyring_rates.py \
  skills/tsao-dft-kinetics-multiscale/examples/catalysis/barriers.csv \
  --temperature 298.15 --out ../tsao-dft-demo/rates.csv
```

```bash
python skills/tsao-dft-kinetics-multiscale/scripts/propagate_barrier_uncertainty.py \
  --barrier 15 --uncertainty 1 --temperature 298.15 --molecularity 2 \
  --standard-state '1 M' --barrier-standard-state '1 M' --activity-convention 'a=c/c0'
```

Barriers and half-widths use kcal/mol; temperature uses K. Transmission coefficient `kappa` and path degeneracy must be positive and finite. Higher molecularity requires matching rate/barrier reference concentrations and the activity convention. The tool does not perform an undocumented free-energy standard-state conversion. CSV headers cannot be empty or duplicated; outputs cannot replace inputs, and a failed rate calculation preserves an existing output file.

### 4. Check uncertainty sources

```bash
python skills/tsao-dft-researcher/scripts/validate_uncertainty_budget.py \
  skills/tsao-dft-researcher/templates/uncertainty-budget.yaml
```

The template uses `report_separately`, so it produces no aggregate error. `root_sum_square` and `sum_bounds` require interpretations consistent with their components. Any invalid component or unrepresentable combined value rejects acceptance with `combined_magnitude=null`, rather than displaying a plausible partial total.

### 5. Train a baseline with independent groups

```bash
python skills/tsao-dft-ml-active-learning/scripts/train_ridge_baseline.py \
  skills/tsao-dft-ml-active-learning/examples/dft-baseline/dataset.csv \
  --features descriptor_1,descriptor_2 --target target --group parent_id \
  --alpha 1 --solver auto --out-dir ../tsao-dft-demo/ridge
```

The example `target` is a synthetic label with no scientific unit. Real data need a data card declaring property, unit and method fingerprint. An existing `split` column must contain `train`/`valid`/`test`, with no `parent_id` crossing splits; only datasets without that column use seeded group allocation. Means and scales are fitted on training data alone; target and group identifiers cannot be features. Duplicate headers, unreadable inputs and output paths replacing the dataset/validation artifact are rejected.

`predictions.csv` and `model-card.json` retain predictions, split hashes, source CSV SHA-256 and preprocessing parameters. Optional `--validation-artifact` binds a supplied report's schema, row count, split hash and method identity; successful binding does not confer independent scientific approval. The active-learning selector ranks uncertainty and retains at most one candidate per group. It never launches remote DFT.

## Mathematical core: implemented algorithms and external-method contracts

### A. Kohn–Sham identity: an external-engine contract

$$
\hat H_{\mathrm{KS}}[\rho]\psi_i(\mathbf r)=\varepsilon_i\psi_i(\mathbf r),
\qquad \rho(\mathbf r)=\sum_i f_i|\psi_i(\mathbf r)|^2.
$$

$$
E[\rho]=T_s[\rho]+\int v_{\mathrm{ext}}(\mathbf r)\rho(\mathbf r)\,d\mathbf r
+E_H[\rho]+E_{\mathrm{xc}}[\rho]+E_{\mathrm{II}}.
$$

These definitions describe the electronic-structure method; this repository does not implement a Kohn–Sham solver. Orbitals $\psi_i$, occupations $f_i$, density $\rho$ and energies require a real external calculation under a declared method. [Method-fingerprint validation](skills/tsao-dft-suite/scripts/validate_method_fingerprint.py) fixes functional, basis/pseudopotential, dispersion, spin, grids and tolerances so that incompatible models are not silently combined.

$$
\mathbf F_I=-\frac{\partial E}{\partial\mathbf R_I},
\qquad A=\frac1{\Omega_{\mathrm{BZ}}}\int_{\mathrm{BZ}}A(\mathbf k)\,d\mathbf k
\approx\sum_{\mathbf k}w_{\mathbf k}A(\mathbf k).
$$

Force is a three-component quantity per atom, and Brillouin-zone weights require their declared normalization. Energy, force, pressure and stress are different quantities: QE `Total force`, `P=` and CP2K `Max. gradient` are scalars and do not create force arrays or stress tensors. The shared QE parser's flattened `3N` force storage also does not automatically satisfy a TypedQuantity requiring `N×3` shape and an atom mapping.

### B. Periodic geometry: row lattices, minimum images and deterministic pairs

$$
\Delta\mathbf r=\Delta\mathbf s\mathbf H,\qquad
\mathbf n^\star=\operatorname*{arg\,min}_{\substack{\mathbf n\in\mathbb Z^3\\n_j=0\ (j\notin\mathcal P)}}
\|\Delta\mathbf r-\mathbf n\mathbf H\|_2,
\qquad\Delta\mathbf r_{\mathrm{MIC}}=\Delta\mathbf r-\mathbf n^\star\mathbf H.
$$

Rows of $\mathbf H$ are lattice vectors; $\mathcal P$ selects periodic axes. General skew cells use bounded closest-lattice search. Componentwise rounding is reserved for the orthogonal-cell fast path:

$$
\Delta\mathbf s_{\mathrm{MIC}}=\Delta\mathbf s-\operatorname{round}_{\mathcal P}(\Delta\mathbf s),
\qquad\Delta\mathbf r_{\mathrm{MIC}}=\Delta\mathbf s_{\mathrm{MIC}}\mathbf H.
$$

[neighbor_list.py](skills/tsao-structure-prep/scripts/neighbor_list.py) requires finite coordinates, a valid cell and a positive cutoff. `MAX_MINIMUM_IMAGE_CANDIDATES=100000` bounds pathological cells; exceeding it is a rejection, not an approximate success. Pairs have deterministic ordering. The all-pairs reference is $O(N^2)$; at fixed density/cutoff and bounded local occupancy, average cell-list candidates scale approximately as:

$$
O\!\left(N+N\bar n_{\mathrm{cell}}\right).
$$

This conditional complexity is not measured speedup. Compare the complete preparation, search, serialization and execution environment.

### C. Eyring rates: complete the logarithm before exponentiation

$$
k_m=\kappa g\frac{k_BT}{h}\exp\!\left(-\frac{\Delta G^\ddagger_{c^\circ}}{RT}\right)
(c^\circ)^{1-m},\qquad[k_m]=\mathrm M^{1-m}\mathrm s^{-1}.
$$

$$
\ln k_m=\ln\kappa+\ln g+\ln k_B+\ln T-\ln h
-\frac{\Delta G^\ddagger}{RT}+(1-m)\ln c^\circ.
$$

[tst_math.py](skills/tsao-dft-kinetics-multiscale/scripts/tst_math.py) uses $k_B=1.380649\times10^{-23}$ J/K, $h=6.62607015\times10^{-34}$ J·s and $R=8.31446261815324/4184$ kcal/(mol·K). Logs act on numerical values in these fixed units, with the numerical $c^\circ$ expressed in mol/L. Unimolecular $m=1$ gives s⁻¹; higher molecularity requires explicit $a=c/c^\circ$. Changing concentration while holding the numerical barrier fixed tests a concentration factor, not a reference-state transformation of the same physical system.

$$
\ln k_{\min}=\ln k_m-\frac{u_G}{RT},\qquad
\ln k_{\max}=\ln k_m+\frac{u_G}{RT}.
$$

$u_G\ge0$ is a supplied symmetric barrier bound. Rates and intervals include the concentration factor before exponentiation, so intermediate overflow cannot reject an otherwise representable final rate. Nonfinite inputs and final overflow are rejected. Extremely small rates may underflow to zero; interval JSON retains finite log rates. The interval is not an automatically calibrated confidence interval and excludes unquantified mechanism, solvent and transport errors. Extreme floating-point regression does not enlarge the physical domain of TST.

### D. Uncertainty: declare the rule and verify the aggregate

$$
u_{\mathrm{RSS}}=\sqrt{\sum_i u_i^2},\qquad
u_{\mathrm{bound}}=\sum_i u_i.
$$

[Budget validation](skills/tsao-dft-researcher/scripts/validate_uncertainty_budget.py) uses stable `math.hypot` and compensated `math.fsum`, then checks the aggregate for finiteness. RSS is appropriate for components declared as independent standard uncertainties in one unit; the script does not infer correlations. Summing bounds only gives a meaningful bound when the components truly have that interpretation. `report_separately` does not aggregate.

### E. Ridge: training-only preprocessing and independent groups

$$
z_{ij}=\frac{x_{ij}-\mu_j^{\mathrm{train}}}{s_j^{\mathrm{train}}},\qquad
\min_{b,\boldsymbol\beta}\|\mathbf y-b\mathbf1-\mathbf Z\boldsymbol\beta\|_2^2
+\alpha\|\boldsymbol\beta\|_2^2.
$$

Training standard deviations use the population definition. Constant columns receive scale 1 and are recorded in the model card. The intercept is unpenalized. For centered training matrix $\mathbf Z_c$ and target $\mathbf y_c$:

$$
\boldsymbol\beta=(\mathbf Z_c^\top\mathbf Z_c+\alpha\mathbf I)^{-1}\mathbf Z_c^\top\mathbf y_c,
\qquad
\boldsymbol\beta=\mathbf Z_c^\top(\mathbf Z_c\mathbf Z_c^\top+\alpha\mathbf I)^{-1}\mathbf y_c.
$$

These are equivalent primal/dual expressions; the code solves linear systems without explicitly forming inverses. `auto` selects dual when features outnumber training samples; $\alpha=0$ uses least squares. Mean absolute error and root mean squared error retain the target unit:

$$
\mathrm{MAE}=\frac1n\sum_i|\hat y_i-y_i|,\qquad
\mathrm{RMSE}=\sqrt{\frac1n\sum_i(\hat y_i-y_i)^2}.
$$

Use a fixed test set for final evaluation; constant-target $R^2$ is `null`. An uncertainty threshold $u(\mathbf x)>u_{\max}$ and out-of-domain decisions require a calibrated model and explicit research policy. The Ridge baseline supplies neither ensemble uncertainty nor automatic DFT queries.

### F. Numerical equivalence, performance and evidence

$$
|x-x_{\mathrm{ref}}|\le a_{\mathrm{tol}}+r_{\mathrm{tol}}|x_{\mathrm{ref}}|,
\qquad S=\frac{\operatorname{median}(t_{\mathrm{ref}})}{\operatorname{median}(t_{\mathrm{candidate}})}.
$$

Declare tolerances with quantity kind, units, shape, method and benchmark. Performance qualification requires the policy repeat count (at least three), consistent input/build/hardware/site identity, actual exit status, numerical equivalence, verified artifacts and signed review. Output success markers cannot replace process exit status; detecting a GPU cannot establish speedup. The [benchmark contract](skills/tsao-dft-hpc-provenance/scripts/benchmark_contract.py) and [trust boundary](skills/tsao-dft-hpc-provenance/scripts/trust_boundary.py) implement these limits.

## Strategies across eight Skills

| Skill | When to use it | Main strategy |
|---|---|---|
| [tsao-dft-suite](skills/tsao-dft-suite/) | Questions crossing modules | Fix observables, method identity, DAG, budget and acceptance before execution |
| [tsao-structure-prep](skills/tsao-structure-prep/) | Before engine input | Compare conformers, protonation, spin, adsorption sites and image contacts; preserve atom mapping |
| [tsao-dft-researcher](skills/tsao-dft-researcher/) | Molecular Opt/Freq, TS/IRC, TDDFT | Review minima and TS separately; one imaginary mode is a candidate requiring displacement/path checks |
| [tsao-periodic-dft-materials](skills/tsao-periodic-dft-materials/) | Crystals, surfaces, defects, NEB | Converge cutoff, k points, cell size, vacuum and magnetic state before comparing observables |
| [tsao-dft-hpc-provenance](skills/tsao-dft-hpc-provenance/) | Jobs, restarts and performance | Structured argv, manifest-bound approval, retained failed attempts and complete execution identity |
| [tsao-dft-ml-active-learning](skills/tsao-dft-ml-active-learning/) | Models of reviewed labels | Group independent physical objects, fit preprocessing on training data and keep test data out of selection |
| [tsao-dft-kinetics-multiscale](skills/tsao-dft-kinetics-multiscale/) | Accepted thermochemistry to rates/networks | Establish standard states, molecularity, degeneracy and network closure first |
| [tsao-dft-catalysis-profile](skills/tsao-dft-catalysis-profile/) | Chemistry within its declared scope | Explicit opt-in; isolated molecular orbitals cannot establish catalyst poisoning |

Capability levels are `L0_REFERENCE`, `L1_HANDOFF`, `L2_VALIDATED_ADAPTER` and `L3_EXECUTION_TESTED`. L2 adapter tests do not create L3 execution facts; scoped performance eligibility does not automatically promote a public capability level.

## Automated acceptance and auditable evidence

```bash
python scripts/validate_benchmark_contract.py --json
python scripts/validate_compute_qualification.py --json
python scripts/capture_compute_contract_evidence.py \
  --out ../tsao-dft-demo/compute-contract-evidence.json --json
python scripts/build_release_acceptance.py \
  --out ../tsao-dft-demo/release-acceptance.json --json
```

Preflight `release-acceptance.json` and executed-gate receipts serve different purposes. All **29/29** permanent gates remain required: assets/dependencies/constraints, acceleration and benchmark contracts, engines/qualification, artifact evidence, architecture/packaging/catalog/agent eval/governance/claims, secrets, ignore markers, images, README/local links, Ruff, two mypy layers, coverage, Bandit, repository audit and the full test suites. Run the complete acceptance process:

```bash
python scripts/quality_gate.py --report-dir ../tsao-dft-acceptance
```

Coverage thresholds remain overall statements ≥90%, branches ≥80%, trust-core statements 100% and branches ≥95%. [scripts/validate_readme_math.py](scripts/validate_readme_math.py) maintains bilingual mathematics and executable-strategy contracts. Visual checks cover language, historical archives, SHA-256, the single embedded PNG and prohibited active SVG content. `--skip-tests` and archived reports cannot replace a fresh full run.

[CI](.github/workflows/ci.yml) separately reports Linux Python 3.11/3.12/3.13, Windows PowerShell, dependency/SBOM and CodeQL jobs. Windows uses `scripts/quality_gate.ps1` with a configured Python environment; Linux results do not substitute for a Windows runner. Tracked historical coverage reports are archives; current figures must come from reports actually generated for the current commit.

The [seven-repository parallel/six-hour prompt](docs/SEVEN_REPOSITORY_ACCEPTANCE_PROMPT.md) and [repository modification prompt](docs/ACCEPTANCE_REWRITE_PROMPT.md) describe review order. Two segments of 10,800 seconds of successful test-process runtime are distinct from a baseline run. Installation, waiting, queue time and failed processes do not count as successful regression. No six-hour completion is claimed without original receipts tied to the relevant commit.

## Troubleshooting

| Symptom | Investigation and remedy |
|---|---|
| Parser rejection or no energy in the final job | Check final-job boundaries, fatal markers and complete source capture; never borrow earlier success |
| Rejected/zero rate or interval | Check kcal/mol, K, standard states, degeneracy and finite ranges; interpret numerical underflow using log rates |
| Rejected uncertainty budget | Correct all components, units and rules; change representation for overflow rather than deleting inconvenient components |
| Duplicate CSV columns, missing values or group leakage | Correct the source and data card; a later duplicate column must not replace a scientific label |
| `UNQUALIFIED` model card | Expected after training; independent data, applicability and scientific review are still required |
| Missing glyphs or broken formulas | New artwork uses glyph outlines; verify hashes and SVG support. Body equations use GitHub math rendering |
| Receipt belongs to another source commit | Pin and rerun the new commit; do not edit receipts or transfer an earlier PASS |

## Historical figure archive

These English technical illustrations retain their original files, synthetic-data labels and governance checks. They explain contracts and do not attest actual engine execution or measurements.

- <a href="assets/ai/hero/tsao-dft-hero.svg">Original AI concept cover</a>
- <a href="assets/demo/workflow-architecture.svg">Workflow</a>
- <a href="assets/demo/wavefunction-esp-gallery.svg">Wavefunction and ESP contracts</a>
- <a href="assets/demo/dft-ml-dashboard.svg">DFT and ML</a>
- <a href="assets/demo/periodic-dft-materials.svg">Periodic materials</a>
- <a href="assets/demo/multiscale-kinetics.svg">Multiscale kinetics</a>
- <a href="assets/demo/hybrid-compute-architecture.svg">Hybrid compute</a>
- <a href="assets/demo/cuda-x-decision-map.svg">CUDA-X decisions</a>
- <a href="assets/demo/edge-hpc-closed-loop.svg">Edge and HPC</a>
- <a href="assets/demo/native-acceleration-roadmap.svg">Native acceleration roadmap</a>
- <a href="assets/demo/evidence-qualification-pipeline.svg">Evidence qualification</a>
- <a href="assets/demo/acceleration-registry-governance.svg">Acceleration registry</a>
- <a href="assets/demo/backend-portability-stack.svg">Backend portability</a>
- <a href="assets/demo/windows-linux-execution-matrix.svg">Execution matrix</a>
- <a href="assets/demo/scientific-acceleration-funnel.svg">Scientific acceleration</a>
- <a href="assets/demo/dft-mathematical-core.svg">Mathematical core</a>
- <a href="assets/demo/qualification-mathematics.svg">Qualification mathematics</a>

See the [README visual system](docs/README_VISUAL_DESIGN_SYSTEM.md), [AI-image governance](docs/AI_IMAGE_GOVERNANCE.md) and [software/scientific acceptance boundaries](README_ACCEPTANCE.md) for further context.

<!-- CURRENT_MAIN_ACCEPTANCE_V2:START -->
## Regenerable source index

This section is maintained by the documentation generator. Equations and usage above map to the cited source. Generation verifies document reproducibility, not external execution.

Implementation anchors: [`skills/tsao-structure-prep/scripts/neighbor_list.py`](skills/tsao-structure-prep/scripts/neighbor_list.py) · [`scripts/build_release_acceptance.py`](scripts/build_release_acceptance.py) · [`scripts/capture_compute_contract_evidence.py`](scripts/capture_compute_contract_evidence.py)

[Archive: code-contract illustration](docs/current-main/tsao-dft-current-main-en.svg) · [Documentation boundaries](docs/CURRENT_MAIN_ACCEPTANCE.md)

<!-- CURRENT_MAIN_ACCEPTANCE_V2:END -->

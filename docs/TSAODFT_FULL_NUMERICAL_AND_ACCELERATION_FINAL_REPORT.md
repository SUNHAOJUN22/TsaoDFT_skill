# TsaoDFT Full Numerical Correctness and Acceleration Final Report

**Program:** `TSAODFT_FULL_NUMERICAL_CORRECTNESS_PERFORMANCE_AND_REAL_ACCELERATION_V2`  
**Repository:** `SUNHAOJUN22/TsaoDFT_skill`  
**Execution model:** sequential fast-forward commits to existing `main`; no branch or PR  
**Phase 5 starting HEAD:** `1f1a594a56a8444756c23132a4e6ad7cad72483f`  
**Phase 5 final documentation HEAD:** `2d1f3e67ca3bad3bddea0c759386b1c22ec02b33`  
**Phase 6 validated implementation HEAD:** `3157c5863fa7ca8ab79cf9592562e91bfe280d5a`  
**Phase 6 implementation run:** `30713615964`  
**Documentation candidate:** the `main` commit containing this report; its exact CI is verified separately after publication.  
**Public capability boundary:** `L2_VALIDATED_ADAPTER`

## 1. Executive conclusion

The repository-wide program established and implemented a correctness-first acceleration architecture.

The most important result is not a claimed GPU speedup. It is that several paths which could produce scientifically incorrect values or false benchmark qualification were identified, corrected and guarded by direct tests:

- a dimensionally inconsistent Eyring/TST rate expression;
- an incorrect ridge-regression intercept for non-centered features;
- overflow-prone uncertainty aggregation;
- incomplete-tail convergence acceptance;
- weak thermodynamic-closure input contracts;
- lossy integer coercion in performance evidence;
- NaN/Inf propagation into scientific equivalence and speedup;
- partial energy-profile output publication;
- scalar geometry reductions that could be safely vectorized.

Repository-level efficiency improved through streaming, vectorization, smaller linear systems, compiled BLAS/LAPACK use and transactional output. No external DFT-engine or GPU speedup is claimed because qualifying real hardware/build evidence was not available.

## 2. Architecture boundary

TsaoDFT remains an eight-skill Python control plane around external compiled electronic-structure engines.

Repository responsibilities include:

- manifest and schema validation;
- scientific preflight;
- job and scheduler generation;
- hardware-aware planning;
- output parsing;
- provenance and hashing;
- scientific-equivalence gates;
- benchmark evidence qualification;
- ML, kinetics, geometry and reporting utilities.

External engine responsibilities remain:

- Kohn–Sham iterations;
- FFTs;
- diagonalization;
- integral evaluation;
- sparse/dense solver kernels;
- engine-native MPI/OpenMP/GPU execution.

The repository therefore cannot truthfully claim to have accelerated VASP, Quantum ESPRESSO, CP2K or Gaussian merely because it can generate a GPU-aware plan or job script.

## 3. Mandatory V2 deliverables

The execution produced:

1. `docs/TSAODFT_FULL_NUMERICAL_CORRECTNESS_PERFORMANCE_AND_REAL_ACCELERATION_MASTER_PROMPT_V2.md`
2. `docs/TSAODFT_FORMULA_UNIT_REFERENCE_STATE_LEDGER.md`
3. `docs/TSAODFT_NUMERICAL_RISK_REGISTER.md`
4. `docs/TSAODFT_PERFORMANCE_PROFILE_AND_ACCELERATION_MATRIX.md`
5. `docs/TSAODFT_NUMERICAL_PERFORMANCE_AND_EVIDENCE_PHASE6_FINAL_REPORT.md`
6. `docs/TSAODFT_FULL_NUMERICAL_AND_ACCELERATION_FINAL_REPORT.md`

Together they define the reusable protocol, the validated formula inventory, resolved/open risks, profile-gated opportunities, Phase 6 implementation evidence and final program status.

## 4. Scientific correctness results

### 4.1 Eyring/TST unit correction

The original expression combined a `kcal/mol` activation barrier with a gas constant in `cal/(mol K)` without converting the barrier. The shared TST core now uses SI units:

```text
k = κ g (k_B T / h) exp[-ΔG‡/(R T)]
ΔG‡(kcal/mol) × 4184 → J/mol
```

For 15 kcal/mol at 298.15 K, κ = g = 1, the independent reference is:

`62.83270649519368 s^-1`

The implementation uses log-rate arithmetic and explicit overflow/underflow handling.

### 4.2 Thermodynamic closure

The relation:

`ΔG‡reverse = ΔG‡forward - ΔGreaction`

is retained, with finite numeric validation, exact reversible booleans, common-unit assumptions, compensated sums and structured failure.

### 4.3 Energy-profile reference state

Relative energies use:

`ΔE(kcal/mol) = (E - Eref)(Hartree) × 627.5094740631`

The reference is explicitly `first`, `min` or one unique label. Duplicate labels and non-finite energies fail before output.

### 4.4 Ridge regression

The corrected unpenalized intercept is:

`b = mean(y) - mean(X)^T β`

Features and targets are centered, the smaller primal/dual system is chosen, and α = 0 uses stable least squares.

## 5. Numerical-stability results

Implemented controls include:

- log-space exponentials;
- `math.fsum` for cancellation-sensitive sums and differences;
- `math.hypot` for overflow-resistant RSS;
- finite checks for scientific and performance values;
- exact integer checks excluding bool and fractional floats;
- stable median/MAD/IQR summaries;
- no explicit dense matrix inverse;
- no fabricated R² for zero target variance;
- complete-tail convergence requirements;
- finite positive timing requirements before speedup.

## 6. Algorithmic and I/O efficiency results

### 6.1 Streaming

Implemented streaming/bounded-memory paths include:

- Eyring CSV processing;
- QE output parsing;
- CP2K output parsing;
- selected VASP parsing paths;
- file and provenance hashing.

### 6.2 Vectorization and native libraries

Implemented:

- NumPy vectorized atom-mapping displacement, RMSD and maximum displacement;
- vectorized pair-distance reduction;
- NumPy/BLAS/LAPACK ridge solves;
- direct vector metric reductions.

No C++ rewrite was added where NumPy already calls optimized native libraries.

### 6.3 Transactional publication

Energy-profile CSV/SVG/PDF/PNG outputs are generated in same-filesystem staging, validated as a complete bundle and only then published. Existing formal outputs remain unchanged if rendering fails before publication; publish-time failures restore backups.

## 7. Performance-evidence correctness

The performance-evidence trust boundary now requires:

- exact repeat/node/rank/thread/iteration integers;
- finite positive wall times;
- finite CPU time, memory, utilization and energy values;
- finite energy, force, stress, property and convergence values;
- consistent scientific identity;
- consistent build and hardware identities;
- verified artifacts;
- sufficient successful repeats;
- numerical-equivalence PASS before speedup;
- independent review where policy requires it.

NaN cannot pass a speedup comparison, fractional topology cannot be truncated, and malformed non-empty policy sections cannot silently become defaults.

## 8. Test and coverage progression

| Stage | Tests | Suites | Failed suites | Statement | Branch |
|---|---:|---:|---:|---:|---:|
| pre-Phase-5 baseline | 415 | 9 | 0 | 93.83% | 82.98% |
| Phase 5 final | 434 | 9 | 0 | 93.98% | 83.22% |
| Phase 6 validated implementation | **450** | **9** | **0** | **94.13%** | **83.42%** |

Coverage was not raised by exclusions, denominator changes or weakened gates. New branches were covered with business-meaningful scientific, extreme-value, malformed-input and transactional-output tests.

The six execution/trust cores remain:

| Core | Statement | Branch |
|---|---:|---:|
| `shell_contract.py` | 100% | 100% |
| `trust_boundary.py` | 100% | 100% |
| `engine_parser_contract.py` | 100% | 100% |
| `benchmark_bridge.py` | 100% | 100% |
| `generate_job_script.py` | 100% | 98.53% |
| `validate_hpc_manifest.py` | 100% | 99.29% |

## 9. Permanent quality gate

The validated Phase 6 implementation passed:

- Python 3.10;
- Python 3.12;
- Python 3.13;
- Ruff lint and format;
- mypy across 18 isolated targets;
- strict trust-boundary mypy across 4 targets;
- 450 tests across 9 suites;
- statement and branch coverage;
- Bandit;
- strict repository audit;
- CodeQL;
- runtime, development and locked-environment dependency audits;
- CycloneDX SBOM generation.

The implementation coverage artifact was ID `8822743852`, digest `f7f8b30c679119550bef0f031e2d68506ddeb723396c93a85c24f292c5769a0c`.

The final documentation HEAD must independently pass the same permanent workflow. Its exact run and artifact are reported outside this file after the commit exists.

## 10. Real acceleration status

### Available

- hardware-aware optimization plans;
- CPU/GPU/provider compatibility validation;
- scheduler and binding generation;
- benchmark campaign materialization;
- parser-to-evidence bridge;
- robust performance statistics;
- scientific-equivalence gates;
- content-addressed evidence bundles;
- qualification rules that keep unreviewed/synthetic evidence at L2.

### Not available

- qualifying real VASP CPU-vs-GPU measurements;
- qualifying real QE CPU-vs-GPU measurements;
- qualifying real CP2K CPU-vs-GPU measurements;
- qualifying Gaussian accelerator measurements;
- real multi-GPU scaling evidence;
- real edge-device latency/energy evidence;
- accepted cuEquivariance workload evidence;
- explicit cuTENSOR contraction benchmark.

Therefore:

```text
REAL_DFT_ENGINE_BENCHMARK: NOT_AVAILABLE
REAL_GPU_BENCHMARK: NOT_AVAILABLE
REAL_EDGE_BENCHMARK: NOT_AVAILABLE
PUBLIC_CAPABILITY_PROMOTION: NOT_AUTHORIZED
```

## 11. Why no C++/CUDA/HIP/SYCL layer was added

The program found higher-priority correctness defects and low-risk Python/NumPy improvements. Remaining native candidates lack at least one of:

- representative profile;
- accepted workload;
- conversion-inclusive end-to-end benchmark;
- platform/build design;
- scientific-equivalence suite;
- real hardware access.

Adding a native layer without these conditions would increase maintenance, packaging and security risk without a trustworthy performance conclusion.

## 12. Remaining work

### Highest priority

1. Profile representative large Gaussian logs while preserving late-error-wins semantics.
2. Select one licensed VASP, QE or CP2K installation and run a real CPU-reference/accelerator campaign.
3. Review task-specific energy/force/stress/property tolerances.
4. Record complete build and hardware topology fingerprints.
5. Retain all failed and successful repeats in a signed evidence bundle.

### Conditional

- periodic cell-list/neighbor-list backend for accepted large trajectories;
- native/OpenMP/Kokkos geometry backend after conversion-inclusive profile;
- cuEquivariance for an accepted equivariant ML model;
- cuTENSOR for an explicit contraction hotspot;
- environment-inventory caching after privacy and invalidation design.

## 13. Repository-operation confirmation

The program used sequential GitHub contents writes. Before each write, the current `main` HEAD and current file SHA were re-read. Concurrent changes were not overwritten; GitHub SHA conflicts were treated as a stop-and-resynchronize signal.

No branch, PR, force push or history rewrite was used.

## 14. Final program status

```text
FULL_EXECUTABLE_CODE_INVENTORY: COMPLETE_FOR_CURRENT_COVERAGE_SCOPE
FORMULA_AND_DIMENSIONAL_AUDIT: COMPLETE_FOR_IDENTIFIED_SCIENTIFIC_MODULES
FORMULA_UNIT_REFERENCE_LEDGER: COMPLETE
NUMERICAL_RISK_REGISTER: COMPLETE
PERFORMANCE_ACCELERATION_MATRIX: COMPLETE
CRITICAL_TST_UNIT_DEFECT: CORRECTED
RIDGE_INTERCEPT_DEFECT: CORRECTED
EXACT_NUMERIC_TYPE_CONTRACTS: PASS
NONFINITE_VALUE_GATES: PASS
NUMERICAL_STABILITY_HARDENING: PASS_FOR_SCOPED_MODULES
ALGORITHMIC_COMPLEXITY_REVIEW: COMPLETE
STREAMING_AND_VECTORIZATION: IMPLEMENTED_FOR_PROVEN_SCOPES
PERFORMANCE_EVIDENCE_TRUST_BOUNDARY: PASS
ENERGY_PROFILE_ATOMIC_PUBLICATION: PASS
NATIVE_ACCELERATION: PROFILE_GATED
REAL_CPU_ACCELERATION_EVIDENCE: NOT_AVAILABLE
REAL_GPU_ACCELERATION_EVIDENCE: NOT_AVAILABLE
REAL_DFT_ENGINE_ACCELERATION_EVIDENCE: NOT_AVAILABLE
SCIENTIFIC_EQUIVALENCE_FRAMEWORK: PASS
VALIDATED_IMPLEMENTATION_CI: PASS
FINAL_DOCUMENTATION_HEAD_CI: VERIFY_AFTER_THIS_COMMIT
COVERAGE_REGRESSION: NO
PUBLIC_CAPABILITY_LEVEL: L2_VALIDATED_ADAPTER
BRANCH_CREATED: NO
PULL_REQUEST_CREATED: NO
FORCE_PUSH: NO
HISTORY_REWRITE: NO
QUALITY_GATE_REDUCTION: NO
TEST_DELETION: NO
FABRICATED_PERFORMANCE_CLAIM: NO
```

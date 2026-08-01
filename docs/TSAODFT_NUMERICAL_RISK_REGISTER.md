# TsaoDFT Numerical and Performance Risk Register

**Repository:** `SUNHAOJUN22/TsaoDFT_skill`  
**Scope:** scientific formulas, numerical stability, algorithmic scaling, parser behavior, performance evidence and real-acceleration claims  
**Assessment basis:** validated repository state through Phase 6; real external-engine and GPU benchmarks remain unavailable.

## 1. Severity and status definitions

Severity:

- `CRITICAL`: can change scientific conclusions or create false performance qualification;
- `HIGH`: can materially corrupt values, convergence decisions, resource accounting or reproducibility;
- `MEDIUM`: can cause partial outputs, scalability failure, ambiguity or unstructured failure;
- `LOW`: maintainability or evidence-quality issue with limited immediate scientific effect.

Status:

- `RESOLVED`: code and direct tests pass permanent CI;
- `MITIGATED`: current controls reduce the risk, but task-specific evidence is still required;
- `PROFILE_GATED`: no implementation change is justified until representative profiling exists;
- `REAL_EVIDENCE_REQUIRED`: no truthful real-performance conclusion can be made without hardware/build data;
- `OPEN_NONBLOCKING`: remaining issue is documented and does not invalidate the current L2 validated-adapter capability.

## 2. Resolved scientific and numerical risks

| ID | Severity | Area | Risk and failure mode | Resolution and evidence | Status |
|---|---|---|---|---|---|
| NR-001 | CRITICAL | Eyring/TST | activation barrier labelled kcal/mol was combined with a cal-based gas constant without the required factor, producing rate errors of about 10¹¹ in a representative case | shared SI implementation, kcal→J conversion, log-rate evaluation and independent 15 kcal/mol regression | `RESOLVED` |
| NR-002 | HIGH | ridge regression | intercept based only on target mean while coefficients were fitted to uncentered features; predictions changed under feature translation | centered features/targets, unpenalized intercept `ȳ - x̄ᵀβ`, primal/dual equivalence tests | `RESOLVED` |
| NR-003 | HIGH | uncertainty RSS | direct squaring could overflow even when the mathematical norm was representable | `math.hypot`, tests near 1e308 | `RESOLVED` |
| NR-004 | HIGH | convergence | an undersized requested tail could be treated as converged | complete-tail requirement, sorted finite inputs and negative tests | `RESOLVED` |
| NR-005 | HIGH | thermodynamic closure | bool, NaN/Inf, wrong roots and malformed YAML could crash or yield invalid closure values | finite contracts, exact boolean, `math.fsum`, structured CLI failure | `RESOLVED` |
| NR-006 | HIGH | performance evidence | fractional values could be truncated by `int()` into valid repeat/node/rank/thread counts | exact-integer TypeGuard and direct API tests | `RESOLVED` |
| NR-007 | CRITICAL | performance qualification | NaN/Inf energy, force, stress, property or wall time could enter comparison semantics and potentially bypass ordinary inequalities | finite-real gates before eligibility, summary, equivalence, speedup and qualification | `RESOLVED` |
| NR-008 | HIGH | policy parsing | malformed or non-finite repeat, outlier and tolerance policies could be silently coerced or misapplied | strict mapping/numeric/integer policy contracts and adversarial tests | `RESOLVED` |
| NR-009 | HIGH | speedup/scaling | zero, negative or non-finite medians and GPU counts could generate meaningless speedup or efficiency | finite positive timing checks, topology checks and no-value fallback | `RESOLVED` |
| NR-010 | MEDIUM | profiler adapters | malformed scheduler duration, CPU time or memory strings could enter summaries | range checks, finite checks and explicit NOT_AVAILABLE results | `RESOLVED` |
| NR-011 | HIGH | energy profile | NaN/Inf energies or duplicate labels could create invalid or ambiguous relative profiles | finite CSV contracts, unique labels, explicit reference selection | `RESOLVED` |
| NR-012 | MEDIUM | energy-profile publication | CSV could be written before figures, leaving a partial bundle after plotting failure | same-filesystem staging, staged-file validation and transactional publication | `RESOLVED` |
| NR-013 | MEDIUM | energy subtraction | close large Hartree totals are cancellation-sensitive | `math.fsum((energy, -reference))` and independent value tests | `RESOLVED` |
| NR-014 | MEDIUM | geometry mapping | per-atom Python distance calls limited scalability | NumPy vectorized displacement/RMSD/max reduction and 2,000-atom test | `RESOLVED` |
| NR-015 | MEDIUM | Eyring CSV | complete-table materialization retained O(rows) Python objects and could leave partial output | row streaming and atomic publication | `RESOLVED` |

## 3. Mitigated risks requiring task-specific scientific judgment

| ID | Severity | Area | Remaining risk | Current mitigation | Required next evidence | Status |
|---|---|---|---|---|---|---|
| NR-101 | HIGH | numerical equivalence | generic absolute tolerances may be inappropriate for a specific material, molecule or observable | tolerance table is explicit, finite, non-negative and bound to policy ID | domain-reviewed tolerances for each benchmark campaign | `MITIGATED` |
| NR-102 | HIGH | higher-order kinetics | rate units depend on activities and standard-state conventions, not only molecularity | output explicitly states convention requirement | declared solution/gas/surface standard state and activity model | `REAL_EVIDENCE_REQUIRED` |
| NR-103 | HIGH | uncertainty | RSS assumes independence and does not represent correlated model errors | aggregation rule is explicit; separate reporting supported | covariance/correlation model or empirical uncertainty calibration | `MITIGATED` |
| NR-104 | MEDIUM | convergence | absolute adjacent difference may not establish full scientific convergence for all observables | rule and threshold are explicit; incomplete tail fails | task-specific multi-observable and relative convergence study | `MITIGATED` |
| NR-105 | MEDIUM | RMSD | mapped-coordinate RMSD is not automatically rotationally aligned | scope is documented and mapping is explicit | alignment contract when structural superposition is required | `OPEN_NONBLOCKING` |
| NR-106 | MEDIUM | energy profile | Hartree-to-kcal conversion is correct, but combining energies from inconsistent methods remains scientifically invalid | surrounding manifests carry method fingerprints | method-identity enforcement at every profile ingestion route | `MITIGATED` |
| NR-107 | MEDIUM | performance outliers | MAD-based outlier flags do not explain root cause and must not justify deletion | outliers are counted and retained | profiler traces and operational review | `MITIGATED` |
| NR-108 | HIGH | benchmark topology | apparently identical GPU counts can conceal different CPU, interconnect or binding topology | hardware and GPU identities are recorded and compared | complete real-site topology fingerprint | `REAL_EVIDENCE_REQUIRED` |

## 4. Profile-gated performance and scalability risks

| ID | Severity | Candidate area | Current concern | Why no blind implementation was made | Profiling/acceptance requirement | Status |
|---|---|---|---|---|---|---|
| PR-201 | MEDIUM | Gaussian parser | rich parsing still processes substantial full-text/regex state for large logs | real large-log distribution and hotspot share are unknown | representative Gaussian logs; wall time, peak RSS, regex hotspots; late-error equivalence | `PROFILE_GATED` |
| PR-202 | MEDIUM | trajectory processing | future multi-frame geometry and neighbor-list work may become O(frames × atoms²) | no accepted large trajectory workload currently defines the boundary | representative frames/atoms/cell; memory and pair-count profile | `PROFILE_GATED` |
| PR-203 | MEDIUM | periodic neighbor lists | naïve full pair matrices can exceed memory | no current repository hotspot justifies a new native backend | cell-list/reference implementation and periodic-equivalence tests | `PROFILE_GATED` |
| PR-204 | LOW | energy-profile plots | Matplotlib startup dominates small tables | output generation is not established as an end-to-end hotspot | campaign-scale profile before caching or alternate renderer | `PROFILE_GATED` |
| PR-205 | LOW | hashing | streaming hashlib is already native and memory-bounded | custom C++ would duplicate optimized library code | profile showing hashing dominates end-to-end time | `PROFILE_GATED` |
| PR-206 | MEDIUM | ridge solver | BLAS/LAPACK performance depends on linked implementation and matrix shape | NumPy already delegates to native libraries | realistic dataset shapes and BLAS environment benchmark | `PROFILE_GATED` |
| PR-207 | MEDIUM | control-plane JSON/YAML | repeated canonicalization could matter in very large evidence campaigns | present campaigns are not shown to be serialization-bound | record-count profile and content-addressing cost breakdown | `PROFILE_GATED` |
| PR-208 | MEDIUM | environment probes | subprocess probe startup may dominate short local commands | probes are bounded and correctness-sensitive | representative repeated workflow profile; safe cache invalidation design | `PROFILE_GATED` |

## 5. Real-acceleration evidence risks

| ID | Severity | Claim surface | Risk | Required evidence before claim | Status |
|---|---|---|---|---|---|
| AR-301 | CRITICAL | VASP GPU speedup | control-plane support may be mistaken for measured VASP acceleration | real VASP GPU build, immutable input, CPU reference, repeats, scientific equivalence and signed evidence bundle | `REAL_EVIDENCE_REQUIRED` |
| AR-302 | CRITICAL | QE GPU speedup | backend recommendation does not prove the installed QE build supports or benefits from it | real build capabilities, decomposition sweep and measured topology | `REAL_EVIDENCE_REQUIRED` |
| AR-303 | CRITICAL | CP2K GPU speedup | CUDA/HIP/SYCL route depends on build, solver and workload | real CP2K build, DBM/DBCSR/solver profile, reference outputs | `REAL_EVIDENCE_REQUIRED` |
| AR-304 | CRITICAL | Gaussian acceleration | packaged Gaussian capabilities are externally controlled; repository cannot retrofit arbitrary kernels | supported executable/build evidence and real run comparison | `REAL_EVIDENCE_REQUIRED` |
| AR-305 | HIGH | multi-GPU scaling | speedup can appear from incomparable topology or insufficient single-GPU baseline | compatible single-GPU and N-GPU runs, bindings, interconnect and strong-scaling math | `REAL_EVIDENCE_REQUIRED` |
| AR-306 | HIGH | edge inference | a surrogate could be presented as replacing DFT validation | accepted model, calibration, OOD/uncertainty gate and remote DFT fallback | `REAL_EVIDENCE_REQUIRED` |
| AR-307 | HIGH | cuEquivariance | library may be incorrectly presented as a Kohn–Sham DFT accelerator | accepted equivariant ML workload such as MACE/NequIP/e3nn and measured inference/training | `REAL_EVIDENCE_REQUIRED` |
| AR-308 | HIGH | cuTENSOR | library may be treated as a generic packaged-engine switch | explicit tensor contraction hotspot, data-layout design, equivalence and real benchmark | `REAL_EVIDENCE_REQUIRED` |

## 6. Repository and quality risks

| ID | Severity | Risk | Current control | Status |
|---|---|---|---|---|
| QR-401 | HIGH | concurrent main writes overwrite new work | re-read HEAD and content SHA before every write; GitHub 409 protection | `MITIGATED` |
| QR-402 | HIGH | old CI result incorrectly attributed to latest commit | exact final HEAD combined status, jobs and logs checked | `MITIGATED` |
| QR-403 | HIGH | coverage improvement through denominator manipulation | permanent coverage inventory and no exclusion/gate changes | `MITIGATED` |
| QR-404 | HIGH | trust-boundary regression | six core modules tracked separately; strict mypy and adversarial tests | `MITIGATED` |
| QR-405 | MEDIUM | flaky timing benchmarks block CI | correctness/complexity invariants used instead of fragile time thresholds | `MITIGATED` |
| QR-406 | HIGH | simulated fixtures presented as real evidence | explicit evidence-source kind and L2-only qualification | `MITIGATED` |

## 7. Priority order for future work

1. Obtain representative large Gaussian logs and produce a parser profile without changing acceptance semantics.
2. Define one real, licensed and reproducible VASP/QE/CP2K benchmark campaign with CPU reference and complete hardware/build fingerprints.
3. Review task-specific scientific-equivalence tolerances before any real performance qualification.
4. Add periodic trajectory/neighbor-list work only when an accepted workload demonstrates a scaling bottleneck.
5. Consider native or GPU code only after end-to-end profiling includes data conversion and launch overhead.

## 8. Current residual-risk conclusion

```text
OPEN_CRITICAL_STATIC_NUMERICAL_DEFECTS_IN_SCOPED_MODULES: NONE_IDENTIFIED
OPEN_CRITICAL_REAL_ACCELERATION_CLAIMS: BLOCKED_BY_MISSING_REAL_EVIDENCE
PERFORMANCE_EVIDENCE_NONFINITE_BYPASS: CLOSED
LOSSY_INTEGER_BYPASS: CLOSED
PARTIAL_ENERGY_PROFILE_PUBLICATION: CLOSED
GAUSSIAN_LARGE_LOG_OPTIMIZATION: PROFILE_GATED
NATIVE_CPU_OR_GPU_EXTENSION: PROFILE_GATED
PUBLIC_CAPABILITY_LEVEL: L2_VALIDATED_ADAPTER
```

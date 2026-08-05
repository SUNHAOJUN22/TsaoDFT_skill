# Tsao DFT HPC and Provenance

General execution Skill for computational chemistry on local machines, Slurm, PBS and cloud/HPC. It generates reviewable scripts and provenance records but does not submit without explicit approval.

```bash
python scripts/validate_hpc_manifest.py examples/slurm/hpc-manifest.yaml
python scripts/generate_job_script.py examples/slurm/hpc-manifest.yaml --out job.slurm
python scripts/classify_failure.py examples/failures/gaussian-memory.log
```

## Acceleration registry

`plan_acceleration.py` and `hardware_optimization_contract.py` load library, alias and backend compatibility views at runtime from `scripts/acceleration_registry.py`. They no longer maintain independent mirror catalogs. The root quality gate rejects a planner that reintroduces a local `_library` catalog or stops loading the canonical registry.

```bash
python ../../scripts/validate_acceleration_registry.py --json
```

Registry membership is planning metadata. It does not prove that CUDA-X, ROCm, oneAPI, Metal or any external DFT engine is installed or executed.

## EngineCapability

VASP, Quantum ESPRESSO and CP2K use the strict `EngineCapability` contract to record:

- engine and executable identity;
- engine version and executable SHA-256;
- compiler, compiler version and build type;
- MPI implementation/version and OpenMP runtime;
- accelerator backend, GPU vendor and toolkit version;
- deterministic build fingerprint;
- version-probe observation, upstream-test status and execution authorization.

Repository templates intentionally contain `NOT_AVAILABLE` fields and validate as `EXTERNAL_HOLD`:

```bash
python ../../scripts/validate_engine_capabilities.py --json

python scripts/engine_capability.py \
  templates/vasp-engine-capability.yaml \
  --json
```

`IDENTITY_VERIFIED` means that the build identity is complete. It is not numerical or performance qualification. Missing engine access, license, build identity or authorization remains `EXTERNAL_HOLD`.

## Reproducible CPU/accelerator qualification

`qualify_compute_campaign.py` loads benchmark result documents in deterministic path order with a hard limit of eight worker threads. A campaign can reach `QUALIFIED_FOR_REVIEW` only when all of the following are present:

- at least three contiguous repeats for an FP64 CPU reference and each candidate;
- real-engine observations accepted by the existing benchmark result schema;
- identical input and method fingerprints;
- successful parsing, exit status and convergence;
- immutable build and hardware fingerprints;
- property-specific numerical equivalence within declared absolute and relative tolerances;
- a median reference-over-candidate wall-time ratio that meets the declared threshold.

Before JSON Schema validation, the evidence loader rejects non-standard `NaN`/`Infinity` constants and exponent overflow such as `1e999`. Non-finite wall times or scientific values therefore cannot enter equivalence, median or performance-ratio calculations.

```bash
python ../../scripts/validate_compute_qualification.py --json

python scripts/qualify_compute_campaign.py \
  templates/compute-qualification-campaign.yaml \
  results/*.json \
  --workers 8 \
  --out qualification-report.json
```

Without real GPU, licensed solver, engine build, hardware identity and accepted result evidence, the workflow reports `EXTERNAL_HOLD` and does not calculate or publish a speedup. `QUALIFIED_FOR_REVIEW` is still not signed L3 evidence.

## Machine-readable contract evidence

The permanent quality gate writes `compute-contract-evidence.json` from the three validators above without invoking an external engine. The report records:

- canonical registry validation and runtime single-source status;
- VASP, Quantum ESPRESSO and CP2K template state;
- repository performance qualification as `NOT_ESTABLISHED`;
- compute campaign state as `EXTERNAL_HOLD`;
- the eight-worker hard bound;
- `external_engine_invoked: false` and `performance_ratio_published: false`.

```bash
python ../../scripts/capture_compute_contract_evidence.py \
  --out compute-contract-evidence.json \
  --json
```

The coverage stage must load this report and embeds it under `contract_evidence` in `coverage-report.json`. A missing, malformed, invalid, externally invoking or ratio-publishing report fails the quality gate. Existing CI coverage artifacts therefore carry both test coverage and the current non-qualification boundary.

## Permanent gates

The root quality gate now runs, in order:

1. acceleration evidence contracts;
2. canonical acceleration registry validation;
3. EngineCapability validation;
4. reproducible compute qualification validation;
5. machine-readable compute contract evidence capture;
6. compute architecture audit;
7. lint, formatting, typing, evidence-bound coverage, security and repository tests.

```bash
python ../../scripts/quality_gate.py
```

## v0.4 depth

See `SKILL.md`, `manifest.yaml`, `scripts/`, `templates/`, and `tests/` for the deterministic DFT adapters and scientific gates introduced in v0.4.0-alpha.1.

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

## Benchmark-result authority and migration

The only authoritative production contract is the nested v1.1 Schema:

```text
templates/benchmark-result.schema.json
```

The repository-level `../../templates/benchmark-result.schema.json` is a byte-identical mirror checked by the permanent gate. Producers such as `benchmark_bridge.py`, import/validation commands, signed performance qualification and the bounded compute campaign all converge on this contract.

The internal semantic validator is also native nested v1.1. `performance_evidence.validate_canonical_result()` rejects any other version. The public `validate_result()` entrypoint first routes input through `benchmark_contract.normalize_record()` and then invokes native v1.1 semantics. There is no nested v1.0 downgrade view and no internal rewrite from `1.1` to `1.0`.

Two historical contracts remain explicit compatibility inputs only:

- **nested v1.0** has the same evidence shape and is accepted only by the central adapter, which performs a version-only transition to v1.1 before semantic validation;
- **flat v1.0** is preserved as `templates/benchmark-result-flat-v1.0.schema.json` and requires an explicit `scientific-reference` or `acceleration-candidate` role mapping.

The nested v1.0 transition preserves the submitted evidence and does not promote its qualification. Direct nested v1.0 calls to the native semantic function fail closed. Flat v1.0 cannot encode every v1.1 provenance field. Migration therefore never guesses the engine executable, model identity, convergence thresholds or original artifact path. Missing or contradictory information is written to `evidence_source.missing_fields`, the source becomes `imported-unverified`, and qualification remains `EXTERNAL_HOLD`.

The flat adapter also records lossy or contradictory cases explicitly, including:

- runtime/backend claims that disagree with the hardware inventory;
- an accelerated scientific-reference role;
- an acceleration candidate without accelerator identity;
- parser acceptance that conflicts with exit or convergence evidence;
- heterogeneous accelerator inventories that nested v1.1 cannot represent losslessly;
- missing build/hardware identities, simulated sources and `ml-surrogate` mapping to `generic`.

Unknown versions, mixed flat/nested documents, duplicate identities and non-finite values fail closed.

```bash
python ../../scripts/validate_benchmark_contract.py --json

python scripts/import_benchmark_evidence.py \
  legacy-results/*.json \
  --schema templates/benchmark-result.schema.json \
  --legacy-reference-candidate CPU-REFERENCE \
  --legacy-acceleration-candidate GPU-CANDIDATE \
  --out build/evidence.jsonl \
  --report build/evidence-import-report.json
```

The role flags are required only for flat v1.0 because that historical shape did not record the role. They are not inference switches and cannot upgrade evidence eligibility.

A caller-provided custom Schema remains available for nonqualifying ingestion. Such records keep their original version, receive `qualification_impact: NOT_ELIGIBLE`, and are not passed through canonical scientific or performance semantics. The importer never rewrites a custom version to `1.0`.

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

`qualify_compute_campaign.py` loads canonical benchmark records in deterministic path order with a hard limit of eight worker threads. Legacy flat v1.0 records may be read through the explicit migration adapter, but their irrecoverable provenance gaps keep the campaign on `EXTERNAL_HOLD`. A canonical campaign can reach `QUALIFIED_FOR_REVIEW` only when all of the following are present:

- at least three contiguous repeats for an FP64 CPU reference and each candidate;
- real-engine observations accepted by the canonical nested v1.1 contract;
- identical input and method fingerprints;
- successful parsing, exit status and convergence acceptance;
- immutable build and hardware fingerprints;
- property-specific numerical equivalence within declared absolute and relative tolerances;
- a median reference-over-candidate wall-time ratio that meets the declared threshold.

Before Schema validation, the evidence loaders reject non-standard `NaN`/`Infinity` constants and exponent overflow such as `1e999`. Non-finite wall times, nested result arrays, convergence thresholds or scientific properties therefore cannot enter equivalence, median or performance-ratio calculations.

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

The permanent quality gate writes `compute-contract-evidence.json` from the acceleration registry, benchmark contract, EngineCapability and compute-qualification validators without invoking an external engine. Evidence Schema v1.2 records:

- canonical acceleration registry validation and runtime single-source status;
- nested v1.1 benchmark authority and root-mirror digest;
- native semantic version `1.1`;
- `compatibility_view_present: false`;
- `legacy_semantic_bypass: FAIL_CLOSED`;
- supported central legacy migrations;
- flat v1.0 migration impact as `EXTERNAL_HOLD` and unknown/mixed input as `FAIL_CLOSED`;
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

The coverage stage must load this report and embeds it under `contract_evidence` in `coverage-report.json`. A missing, malformed, invalid, externally invoking or ratio-publishing report fails the quality gate. CI coverage artifacts therefore carry both test coverage and the current non-qualification boundary.

## Permanent gates

The root quality gate now runs, in order:

1. explicit legacy acceleration evidence contracts;
2. single-authority benchmark-result contract, native v1.1 semantics and migration validation;
3. canonical acceleration registry validation;
4. EngineCapability validation;
5. reproducible compute qualification validation;
6. machine-readable compute contract evidence capture;
7. compute architecture audit;
8. lint, formatting, typing, evidence-bound coverage, security and repository tests.

The benchmark contract gate performs table-driven negative regression over rare flat-field combinations, missing and contradictory provenance, nested/flat version migration, explicit roles, non-finite values and unknown or mixed shapes.

```bash
python ../../scripts/quality_gate.py
```

## v0.4 depth

See `SKILL.md`, `manifest.yaml`, `scripts/`, `templates/`, and `tests/` for the deterministic DFT adapters and scientific gates introduced in v0.4.0-alpha.1.

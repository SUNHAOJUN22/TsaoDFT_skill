# Real benchmark evidence and scoped L3 qualification

## Evidence state machine

```text
planned candidate
→ imported evidence
→ schema and artifact validation
→ parser-accepted successful repeats
→ numerical-equivalence gate
→ performance statistics
→ immutable evidence bundle
→ independent review
→ scoped L3 performance eligibility
```

No state transition is inferred from the previous state. A successful scheduler exit, a self-reported support level or a single fast run cannot bypass any gate.

## Input contract

`benchmark-result.schema.json` records the benchmark plan/candidate identity, repeat index, engine and build fingerprint, compiler/MPI/OpenMP/accelerator runtime, CPU/GPU hardware identity, scheduler/site/filesystem, input and method hashes, convergence thresholds, parser status, scientific observables, timing/utilization/memory/I/O, artifacts and evidence source.

Supported imports are JSON, YAML, JSONL and CSV with dotted field names. Import preserves all successful and failed attempts. Duplicate benchmark/candidate/repeat/run identities are rejected.

## Numerical-equivalence-first rule

Before any effective speedup is calculated, the candidate and CPU reference must share:

- engine and engine version;
- input SHA-256;
- method fingerprint;
- functional, basis/pseudopotential and correction policy;
- convergence thresholds;
- observable set;
- parser acceptance and successful exit.

Energy, forces, stress and declared scalar properties must fall inside the policy tolerances. A failed numerical gate produces no effective speedup and cannot be selected as the best candidate.

## Statistics

The default policy requires three accepted repeats per candidate. Formal summaries use medians rather than the fastest run and report min/max, quartiles, IQR, MAD, modified-z outliers, failed runs, CPU-to-candidate speedup, single-GPU-to-multi-GPU speedup, strong-scaling efficiency, GPU-hours, CPU-core-hours, memory, SCF iterations, I/O and energy-to-solution when available.

## Immutable bundle

`qualify_performance_evidence.py` writes:

- `benchmark-summary.json`;
- `benchmark-summary.md`;
- `performance-evidence-manifest.json`;
- `artifact-checksums.sha256`;
- `qualification-report.json`.

The manifest retains all attempts and receives a SHA-256 used by the qualification report.

## Qualification states

Possible candidate states are:

- `QUALIFIED_FOR_SCOPED_L3_PERFORMANCE_EVIDENCE`;
- `INSUFFICIENT_REPEATS`;
- `NUMERICAL_MISMATCH`;
- `BUILD_IDENTITY_MISSING`;
- `HARDWARE_IDENTITY_MISSING`;
- `PARSER_NOT_ACCEPTED`;
- `ARTIFACT_HASH_MISMATCH`;
- `REFERENCE_MISSING`;
- `PERFORMANCE_NOT_IMPROVED`;
- `L2_ONLY`.

A scoped qualification requires a real-engine evidence source, verified artifacts, sufficient repeats, an accepted CPU reference, numerical equivalence, performance improvement and approved independent review. It never modifies the repository's public capability level automatically.

## Optional metric adapters

`collect_optional_metrics.py` parses supplied summaries from Slurm `sacct`, GNU `time -v`, NVIDIA `nvidia-smi`, ROCm, Intel GPU tools, Nsight and engine parsers. It never invokes those tools. Missing executables or invalid optional summaries return `NOT_AVAILABLE`, never a fabricated zero.

## Commands

```bash
python skills/tsao-dft-hpc-provenance/scripts/validate_benchmark_result.py \
  results/*.yaml --artifact-root run-artifacts

python skills/tsao-dft-hpc-provenance/scripts/import_benchmark_evidence.py \
  results/* --artifact-root run-artifacts --out build/evidence.jsonl

python skills/tsao-dft-hpc-provenance/scripts/compare_acceleration_results.py \
  build/evidence.jsonl \
  --policy skills/tsao-dft-hpc-provenance/templates/performance-qualification-policy.yaml \
  --artifact-root run-artifacts \
  --out build/comparison.json

python skills/tsao-dft-hpc-provenance/scripts/qualify_performance_evidence.py \
  build/evidence.jsonl \
  --policy skills/tsao-dft-hpc-provenance/templates/performance-qualification-policy.yaml \
  --artifact-root run-artifacts \
  --review approved-review.yaml \
  --out-dir build/performance-evidence
```

These are evidence-processing commands. They do not submit jobs or execute a DFT engine.

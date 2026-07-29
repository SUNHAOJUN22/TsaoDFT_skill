# TsaoComputation Release Qualification Plan

## Purpose

This plan defines the measurable closure criteria for turning the TsaoDFT/TsaoComputation repository into a trustworthy scientific-computing control plane. Architectural completeness alone is not release qualification. Every capability claim must be tied to executable tests, immutable evidence, and explicit non-claims.

## Current verified baseline

- The permanent CI workflow runs Python 3.10, 3.12, and 3.13 quality gates.
- CodeQL security-extended analysis and dependency/SBOM jobs are required.
- The six HPC execution trust-core modules have 100% statement coverage and at least 98.53% branch coverage:
  - `shell_contract.py`
  - `trust_boundary.py`
  - `engine_parser_contract.py`
  - `benchmark_bridge.py`
  - `generate_job_script.py`
  - `validate_hpc_manifest.py`
- Research-manifest, scientific-figure, and release-coverage-runner boundary tests are versioned in the repository.
- No hardware speedup, energy-efficiency, or scientific-equivalence claim is accepted without measured evidence from the stated engine, hardware, build, input, and precision mode.

## Gate A: repository quality

Release qualification requires all of the following on the same commit:

1. Whole-repository statement coverage at or above 90%.
2. Whole-repository branch coverage at or above 80%.
3. Trust-core statement coverage at 100% and branch coverage at or above 95% per file.
4. Ruff lint and formatting pass.
5. Mypy and strict trust-boundary type checks pass.
6. All unit, negative, integration, governance, packaging, and Agent-evaluation suites pass.
7. Python 3.10, 3.12, and 3.13 jobs pass.
8. CodeQL, dependency audit, locked-environment audit, and CycloneDX SBOM generation pass.

Coverage thresholds must not be met by narrowing the production denominator, excluding reachable code, adding blanket pragmas, or lowering thresholds.

## Gate B: approval-controlled execution

A real engine command may be launched only when all of these conditions hold:

- The reviewed manifest hash exactly matches the execution manifest.
- A non-expired Ed25519 approval attestation binds the manifest, benchmark plan, build fingerprint, execution scope, and site profile.
- The executable and required inputs are content-addressed or recorded before launch.
- Structured argv is used; unreviewed shell fragments are rejected.
- Local, Slurm, and PBS execution paths use the same approval and evidence contract.
- Timeout, interruption, scheduler rejection, parser rejection, and non-zero exit paths retain logs and partial evidence.
- Checkpoint/restart execution creates explicit lineage rather than overwriting the parent run.

The executor must fail closed before invoking the engine when any approval or binding check fails.

## Gate C: scientific equivalence and performance evidence

An acceleration candidate is qualified only against a declared reference configuration. The evidence bundle must contain:

- engine name and version;
- executable/build fingerprint and linked acceleration backend;
- CPU, GPU, driver, runtime, compiler, MPI, and scheduler identity;
- input and output hashes;
- precision mode;
- repeated measurements, with at least three successful repeats unless a stricter benchmark plan applies;
- wall time, CPU time, host/device memory, transfer time, I/O, and available energy metrics;
- energy, force, stress, convergence, and other declared scientific observables;
- tolerances and pass/fail decisions for scientific equivalence;
- median and dispersion rather than a single best run;
- retained failed and rejected candidates.

A candidate may be marked `qualified` only when scientific equivalence passes first. A faster but scientifically non-equivalent candidate remains rejected.

## Gate D: portability and native migration

Python remains the orchestration, validation, provenance, and experiment-control layer. Native migration is permitted only for measured hotspots with a stable contract.

Required native boundaries:

1. versioned file/JSON subprocess contract for engine-scale components;
2. narrow C ABI for stable native kernels;
3. nanobind/pybind11 only where in-process calls are justified;
4. Python Array API and DLPack for zero-copy array interoperability where supported;
5. deterministic CPU fallback and cross-backend reference tests.

Backend qualification is separate for CUDA, HIP, SYCL/OpenMP offload, and Metal. Availability of a library does not imply that an external engine uses it.

## Gate E: edge execution

Edge support is qualified per device class rather than declared generically. Each supported profile must record:

- architecture and operating system;
- available memory and accelerator runtime;
- supported model/kernel format;
- thermal and power constraints when measurable;
- deterministic preprocessing and postprocessing;
- out-of-distribution or unsupported-input handling;
- escalation path to HPC for workloads outside the edge qualification envelope.

Edge inference, workflow triage, and lightweight surrogate evaluation must not be represented as a substitute for unperformed first-principles calculations.

## Gate F: release evidence

A release candidate requires an immutable evidence index containing:

- source commit and canonical hashes;
- CI run identifiers;
- coverage reports;
- test and static-analysis results;
- CodeQL and dependency-audit status;
- SBOM digest;
- benchmark-plan and performance-evidence digests;
- known limitations, unsupported combinations, and unresolved external-hardware work;
- explicit public-release authorization.

If any release-blocking evidence is missing, stale, mismatched, or unverified, the release status remains blocked.

## Ordered closure sequence

1. Close the whole-repository 90%/80% coverage gate with real boundary tests.
2. Implement the approval-controlled local/Slurm/PBS executor.
3. Implement timeout, checkpoint, restart-lineage, and partial-evidence retention.
4. Run CPU-reference scientific-equivalence campaigns.
5. Run backend-specific GPU and distributed benchmarks on real hardware.
6. Add profiling evidence and migrate only proven Python hotspots to native code.
7. Qualify edge profiles with explicit capability envelopes.
8. Assemble the immutable release evidence index and run all gates on one commit.

The repository is not “perfect” because it contains many features. It is release-qualified when every supported claim survives these gates and every unsupported claim remains explicit.

# Code Quality and Test Audit

Date: 2026-07-28  
Baseline branch: `main`  
Baseline commit: `6cf55b62eb2d063f6282703f70eb2ab220f36daf`

## Baseline evidence

Before this remediation, the permanent GitHub quality gate passed on Python 3.10, 3.12 and 3.13. The repository reported 92 unit tests across nine isolated suites with zero failed suites, and Ruff lint/format checks were clean.

This audit does not promote adapter tests into real-engine evidence. Gaussian, VASP, Quantum ESPRESSO, CP2K, Multiwfn, VMD, scheduler and reactor claims remain bounded by the support-level documents.

## Scope reviewed

- permanent GitHub Actions workflow and failure-log handling;
- `scripts/quality_gate.py` and `scripts/run_all_tests.py`;
- repository, catalog, AI-cover, README-visual and README-link validators;
- runtime and development dependency declarations;
- root tests and all eight per-Skill test suites;
- release/version consistency, temporary-file rejection and workflow hygiene;
- prior parser, hashing, ridge-solver and Slurm-array regression coverage.

## Findings

### 1. Dependency declarations could drift silently

Runtime dependencies were duplicated in `requirements.txt` and `pyproject.toml`; development dependencies were duplicated in `requirements-dev.txt` and `project.optional-dependencies.dev`. No offline gate proved that the declarations remained equivalent. A future edit could therefore pass unit tests in one installation path but fail in another.

**Remediation:** add `scripts/validate_dependencies.py`, validate normalized runtime/dev requirements, the requirements include chain, `VERSION` versus PEP 440 project version, and the Python floor versus Ruff target.

### 2. Quality stages had no local timeout

The workflow had a global job timeout, while individual validation stages could hang until the whole runner timed out. This obscured which stage stalled and delayed failure feedback.

**Remediation:** give every stage an explicit timeout, give the full test stage a larger bound, expose an optional positive `--timeout` override, and return code 124 with a deterministic timeout record.

### 3. JSON mode was not machine-clean

`quality_gate.py --json` inherited child-process output, so logs could appear before the JSON document.

**Remediation:** capture child output in JSON mode and include it only for failed stages.

### 4. CI contained a non-essential network failure point

The workflow manually posted commit statuses through the GitHub REST API even though GitHub Actions already creates native matrix checks. A transient status-API error could fail an otherwise successful quality run.

**Remediation:** rely on native Actions checks, keep immutable action pins and failure artifacts, add `pip check`, and remove the custom status-posting code and `statuses: write` permission.

### 5. New quality contracts needed direct regression tests

The existing 92 tests covered repository shape, visual governance, links, parsers, ML, HPC and scientific contracts, but not dependency drift or quality-gate timeout semantics.

**Remediation:** add focused root tests for valid and invalid dependency contracts, stage ordering, skip-tests behavior, timeout handling and invalid CLI timeout values.

## Acceptance criteria

The remediation is accepted only when the final `main` commit satisfies all of the following:

- Python 3.10, 3.12 and 3.13 GitHub Actions jobs pass;
- dependency contract validation passes offline;
- Ruff lint and formatting pass;
- repository, catalog, README, AI-cover and deterministic-asset gates pass;
- every discovered unittest suite runs at least one test;
- the expanded 100-test baseline reports zero failed suites;
- no branch or pull request is created.

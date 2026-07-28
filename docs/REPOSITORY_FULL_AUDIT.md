# TsaoDFT Full Repository and Agent Skill Audit

Date: 2026-07-28  
Audited branch: `main`  
Audited HEAD: `25ee4d778d634f5cbe518c16750b2c093032dff6`  
GitHub Actions run: `30327033195`  
Audit artifact SHA-256: `308b4056c817ad2a0272c55b71e22e83f4ac6b908ef7a101043437ff52e3a821`

## Audit rules

This document records the repository **before remediation**. A passing command is not treated as scientific correctness, real-engine execution evidence, or security proof. Capabilities that could not be queried with the GitHub App token are labelled `NOT VERIFIED` instead of inferred.

No branch or pull request was created. The user-mandated `main`-only policy remains unchanged.

## Baseline evidence

The native GitHub Actions matrix passed on Python 3.10, 3.12 and 3.13. The existing deterministic gate reported:

- 100 unit tests;
- 9 non-empty isolated suites;
- 0 failed suites;
- Ruff lint and formatting passing;
- repository, dependency, catalog, AI-cover, README visual and local-link validation passing.

This baseline does **not** establish L3 real-engine coverage. Gaussian, VASP, Quantum ESPRESSO, CP2K, Multiwfn, VMD, HPC scheduler and reactor execution remain bounded by the repository support-level documents.

## Tracked-file inventory

The audited tree contained **363 Git-tracked files**:

| Category | Files |
|---|---:|
| Skill implementation and references | 259 |
| Tests | 38 |
| Documentation | 20 |
| Assets | 14 |
| Root scripts | 12 |
| Root/other | 13 |
| Configuration | 6 |
| Workflow | 1 |

Inventory checks found:

- 0 empty tracked files;
- 0 files larger than 1 MB;
- 0 binary tracked files;
- 0 tracked cache/build directories;
- 2 duplicate-content groups;
- 21 `noqa` / `type: ignore` markers;
- no test skip/xfail marker discovered by the inventory scanner.

The duplicate-content groups are six copies each of `audit_skill.py` and `utils.py` under different Skills. They are currently self-contained Skill files rather than an accidental generated cache. Consolidation is deferred because each installed Skill must remain independently usable; the duplication is recorded as maintenance debt, not silently deleted.

## Findings by severity

### Critical

No Critical finding was confirmed.

### High — installer can delete a foreign directory

**Evidence:** `scripts/install.py:83-109`; hosted destructive-install test in run `30327033195`.

`--force` removes an existing destination using `unlink()` or `shutil.rmtree()` without proving that TsaoDFT created or owns the destination. The audit created a foreign `tsao-dft-suite` directory containing `FOREIGN_DATA.txt`; `--force` returned success and the sentinel did not survive.

**Risk:** irreversible deletion of unrelated user data that happens to use a Skill directory name.

**Required remediation:** installation ownership record, root/home protection, refusal to overwrite or uninstall unowned targets, staged/atomic copy, exact symlink ownership checks, and negative regression tests.

### High — all eight Skills lack an explicit prompt-injection boundary

**Evidence:** every `skills/*/SKILL.md` in the audited tree.

The Skills contain scientific guardrails and approval gates, but none explicitly states that instructions embedded in web pages, PDFs, logs, README files, retrieved documents or tool output are untrusted data.

**Risk:** an Agent could treat external content as authority, disclose secrets, weaken scientific gates, execute unapproved tools, or promote unsupported evidence.

**Required remediation:** a common untrusted-content contract applied to all Skills, a repository Agent security model, and deterministic positive/negative evals.

### High — open-source security response policy is missing

**Evidence:** standard-file audit.

The following were absent:

- `SECURITY.md`;
- `CONTRIBUTING.md`;
- `CODE_OF_CONDUCT.md`;
- `.github/CODEOWNERS`;
- issue templates and configuration;
- pull-request template;
- `THIRD_PARTY.md`.

`CITATION.cff` exists and passed parsing.

**Risk:** no documented private vulnerability-reporting route, response expectations, contribution evidence requirements, ownership map, or third-party attribution process.

### Medium — XML parsing uses unsafe standard-library entry points

**Evidence:** Bandit 1.9.4, four `B314` findings with High confidence:

- `scripts/generate_readme_demos.py:69`;
- `scripts/validate_ai_assets.py:26`;
- `scripts/validate_readme_visuals.py:64`;
- `scripts/validate_repo.py:227`.

All four use `xml.etree.ElementTree.fromstring`. Although the current files are repository assets, validators may receive modified/untrusted SVG during review or installation.

**Required remediation:** use `defusedxml`, preserve exact validation behavior, update dependency contracts and add malicious-XML regression tests.

### Medium — static typing is not yet clean

**Evidence:** mypy 2.3.0, 14 errors after per-directory module isolation.

Confirmed files include:

- `scripts/validate_repo.py` — 5 errors;
- `scripts/validate_dependencies.py` — 1 error;
- `skills/tsao-dft-researcher/scripts/parse_gaussian.py` — 4 errors;
- `skills/tsao-dft-researcher/scripts/build_energy_profile.py` — 1 error;
- `skills/tsao-dft-suite/scripts/route_dft_task.py` — 1 error;
- `skills/tsao-periodic-dft-materials/scripts/preflight_vasp.py` — 1 error;
- `skills/tsao-structure-prep/scripts/validate_atom_mapping.py` — 1 error.

Additional first-pass findings from broader module inference were discarded where duplicate top-level script names made the invocation invalid. The listed 14 errors are the clean isolated result.

### Medium — trigger collisions lack an explicit precedence contract

**Evidence:** 30 repeated trigger terms in Skill manifests.

Expected root-orchestrator overlap includes `Gaussian`, `VASP`, `QE`, `CP2K`, `surface`, `defect`, `machine learning` and `microkinetics`. Peer-Skill collisions include `AiiDA`, `barrier`, `campaign`, `conformer`, `descriptor`, `diffusion`, `provenance`, `slab`, `uncertainty`, and several ML terms.

**Risk:** ambiguous activation or incorrect specialised-profile routing.

**Required remediation:** deterministic routing precedence and eval cases. Triggers must not be blindly removed when multi-Skill collaboration is scientifically correct.

### Medium — project metadata resembles a package but does not build

**Evidence:** `python -m build` with build 1.5.0 failed because setuptools discovered multiple top-level directories (`skills`, `assets`).

**Classification:** **B — repository-style Skill collection**, not a wheel-ready Python distribution.

**Required remediation:** explicitly document repository-only packaging, prevent unsupported wheel claims, and validate Skill installation instead of manufacturing a misleading wheel.

### Medium — no persistent Agent eval suite

The repository has deterministic Python tests but no versioned eval schema covering prompt injection, scope isolation, approval gates, support-level escalation, provenance loss, ambiguous routing, interruption/recovery and idempotency.

### Low — Bandit subprocess and randomness findings require review

Production-only Bandit found 14 Low-severity findings:

- fixed internal `subprocess` calls in benchmark, installer, quality-gate and test-runner scripts;
- one partial executable path in a benchmark fixture;
- one non-cryptographic RNG use in the ML baseline.

The RNG is used for reproducible scientific splitting, not security. Subprocess calls require argument-origin documentation and targeted tests; they must not be globally ignored.

### Low — ignore markers require explicit rationale

The inventory found 21 markers, mostly `# noqa: E402` after intentional script-directory path injection. Two `# type: ignore` comments are on optional PyYAML imports. Each marker must either gain a precise reason or be removed; blanket ignore expansion is prohibited.

## Dependency and supply-chain evidence

- `pip check`: PASS.
- Runtime `pip-audit` 2.10.1: 0 known vulnerabilities.
- Development `pip-audit` 2.10.1: 0 known vulnerabilities.
- CycloneDX JSON SBOM generation: PASS.
- GitHub Actions references in the single workflow are pinned to full commit SHAs.
- Dangerous triggers (`pull_request_target`, `workflow_run`, issue-triggered write workflows): none detected.
- Releases API: no GitHub Releases found.
- Git tags: none found in the full checkout.

The repository metadata API did not expose `security_and_analysis` state. Branch protection, CodeQL default setup and Dependabot-alert endpoints returned `403 Resource not accessible by integration`; these settings are therefore **NOT VERIFIED**, not assumed disabled or enabled.

## GitHub governance exception

The repository intentionally works directly on `main` and does not use feature/fix branches or PRs. This is a user-mandated governance exception to common protected-branch review practice. The audit must preserve that decision while documenting its residual risk. Protection against force-push/deletion and required signed/status checks could not be verified through the available App permission.

## Acceptance plan

Automatic remediation will address:

1. installer ownership and destructive-operation safety;
2. prompt-injection boundaries and Agent security model;
3. deterministic Agent evals and routing precedence;
4. unsafe XML parsing;
5. mypy findings and a permanent isolated type gate;
6. Bandit production scanning and targeted justifications;
7. security/contribution/governance documents;
8. repository-only packaging declaration;
9. persistent pip-audit/SBOM evidence without turning transient network failure into a false deterministic green/red result;
10. removal of all one-time audit harness files before final acceptance.

Settings inaccessible to the GitHub App will remain `NOT VERIFIED` unless another authoritative interface becomes available.

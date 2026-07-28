# TsaoDFT Full Repository and Agent Skill Audit

Date: 2026-07-28  
Branch: `main`  
Final validated source commit before documentation sync: `e61146cec6dfc842e80c8415fa0bd95453ab8551`  
Final validation run: `30332229705`

## Audit rule

A passing command is not treated as scientific correctness, real-engine execution evidence or proof that every GitHub account setting is enabled. Capabilities that could not be inspected through the available GitHub App remain `NOT VERIFIED` rather than inferred.

No branch or pull request was created. The user-mandated `main`-only policy was preserved throughout the remediation.

## Final acceptance summary

The final hosted run passed:

- Python 3.10 quality and security gate;
- Python 3.12 quality and security gate;
- Python 3.13 quality and security gate;
- 118 unit tests across nine non-empty suites;
- Ruff lint and formatting;
- isolated mypy checks across 18 targets;
- Bandit production audit with 14 exact reviewed findings;
- repository, dependency, packaging, catalog, Agent-eval, governance, ignore-marker, AI-cover, visual and link gates;
- CodeQL Python `security-extended`;
- runtime and development `pip-audit`;
- CycloneDX JSON SBOM generation and artifact upload.

No failure artifact was generated for the final run because all blocking gates passed.

## Repository inventory and architecture

The repository is intentionally a **repository-style Agent Skill collection**, not a wheel-ready Python library. It contains eight independently installable Skills, shared root tooling, deterministic tests, scientific demo assets, governance files and one permanent GitHub Actions workflow.

The duplicated `audit_skill.py` and `utils.py` files under different Skills are recorded maintenance debt, not accidental cache files: each installed Skill must remain self-contained. Consolidation may only occur through a packaging model that preserves independent installation.

## Closed findings

### High — destructive installer ownership

**Original risk:** `--force` could remove an existing foreign directory that happened to share a Skill name.

**Remediation:**

- installation ownership records under `.tsao-skill-ownership`;
- target-root protection;
- refusal to modify or uninstall unowned destinations;
- exact symlink-target checks;
- staged copy and atomic replacement;
- modified-copy detection;
- optional backup before replacement;
- negative regression tests for foreign data, home-directory targets, stale records and changed symlinks.

The production `assert` in the copy-install path was replaced by an explicit `InstallSafetyError`, so safety behavior remains active under optimized Python execution.

### High — prompt-injection boundary

**Original risk:** content retrieved from web pages, PDFs, logs, README files or tool output could be mistaken for authoritative instructions.

**Remediation:** every Skill now contains an explicit **Untrusted content and instruction hierarchy** section. External content is data, cannot override system/developer/user authority, cannot request secrets, cannot weaken scientific gates and cannot authorize expensive or destructive execution.

A repository-level Agent security model and deterministic eval contracts cover prompt injection, scope isolation, approval gates, evidence escalation, routing ambiguity and destructive-operation ownership.

### High — open-source security and contribution governance

Added and validated:

- `SECURITY.md`;
- `CONTRIBUTING.md`;
- `CODE_OF_CONDUCT.md`;
- `THIRD_PARTY.md`;
- `.github/CODEOWNERS`;
- Dependabot policy compatible with the main-only exception;
- issue templates and configuration;
- pull-request template;
- Agent security, packaging and supply-chain policy documents.

`CITATION.cff` remains present and parseable.

### Medium — unsafe XML parsing

The four SVG/XML validators now use `defusedxml` instead of unsafe standard-library parsing entry points. Regression tests reject a return to `xml.etree.ElementTree` in those validators.

### Medium — static typing

The isolated mypy gate now covers root scripts/tests and every Skill script/test space independently. This avoids invalid duplicate-top-level-module inference while still type-checking all 18 targets. The final run reports zero mypy failures.

### Medium — Bandit findings

Confirmed code findings were repaired:

- unsafe YAML workflow parsing replaced by `yaml.safe_load`, with explicit support for YAML 1.1 interpreting `on` as Boolean `True`;
- production installer assertion replaced by a runtime safety error.

The remaining 14 low-risk findings are exact `(path, test_id)` contracts with non-empty rationales. They cover fixed internal subprocess argv calls and one seeded non-cryptographic RNG used for reproducible scientific splitting. The allowlist is regression-tested as an exact set; new or stale allowances fail CI.

### Medium — trigger collisions and Agent evaluation

Trigger overlap is not blindly removed because multi-Skill collaboration is scientifically valid. Routing precedence, root-orchestrator authority, specialised-profile scope and support-level escalation are now represented in deterministic Agent eval contracts.

### Medium — packaging ambiguity

The repository is explicitly classified as a Skill collection. Validation prevents unsupported wheel claims and tests the real installer instead of manufacturing a misleading Python distribution.

### Medium — dependency and supply-chain drift

The deterministic dependency contract synchronizes:

- `requirements.txt`;
- `requirements-dev.txt`;
- `pyproject.toml`;
- `VERSION` and PEP 440 version;
- Python minimum version and Ruff target.

Hosted CI adds `pip check`, runtime/development `pip-audit`, CycloneDX SBOM generation and CodeQL analysis. Reusable Actions are pinned to full commit SHAs.

## Permanent quality gate

The final gate order is:

```text
versioned demo assets
→ dependency and version contract
→ repository-only packaging model
→ DFT catalog
→ Agent eval contracts
→ governance and workflow policy
→ explained ignore markers
→ governed AI cover
→ bilingual README visuals
→ offline local links
→ Ruff lint
→ Ruff formatting
→ isolated mypy type checks
→ Bandit production audit
→ strict repository audit
→ all non-empty test suites
```

Each stage has a deterministic timeout. Test discovery must report at least one test per suite. JSON mode captures child output so automation receives a single valid document.

## Hosted workflow policy

`.github/workflows/ci.yml` is the only permanent workflow. It runs on `main` pushes, pull requests and manual dispatch. The blocking authority is the native GitHub Actions job result. Compatibility status publication is best-effort and cannot turn passing code into a false failure.

The permanent workflow does not use `pull_request_target`, issue-triggered writes or unpinned third-party Actions.

## Final test distribution

| Suite | Tests |
|---|---:|
| Root repository and security contracts | 43 |
| `tsao-dft-suite` | 4 |
| `tsao-dft-researcher` | 16 |
| `tsao-structure-prep` | 5 |
| `tsao-periodic-dft-materials` | 11 |
| `tsao-dft-ml-active-learning` | 16 |
| `tsao-dft-hpc-provenance` | 13 |
| `tsao-dft-kinetics-multiscale` | 5 |
| `tsao-dft-catalysis-profile` | 5 |
| **Total** | **118** |

## GitHub settings not verified

The available GitHub App did not expose authoritative state for:

- branch protection and force-push/deletion rules;
- signed-commit requirements;
- CodeQL default setup outside the versioned workflow;
- Dependabot alert settings;
- private vulnerability-reporting configuration.

These settings remain **NOT VERIFIED**. The repository files and hosted workflow compensate where possible, but they do not prove account-level configuration.

## Scientific non-claims

The audit validates repository engineering and deterministic adapters. It does not establish real licensed execution of Gaussian, VASP, Quantum ESPRESSO, CP2K, Multiwfn, VMD, Slurm/PBS, DeepChem/GNN or Cantera. Selected capabilities remain `L2_VALIDATED_ADAPTER` until immutable engine/version/site evidence supports a scoped `L3_EXECUTION_TESTED` claim.

## Residual risks and future work

- Main-only direct writes reduce review separation; this is a deliberate user governance exception.
- Real-engine and real-HPC regressions remain external.
- Self-contained utility duplication requires disciplined synchronized maintenance.
- External-link availability is not tested by deterministic CI; local links are fully validated offline.
- Security and dependency data can change after the recorded run and should be re-audited before release.

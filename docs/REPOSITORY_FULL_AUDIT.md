# TsaoDFT Full Repository and Agent Skill Audit

Date: 2026-07-28  
Branch: `main`  
Final validated source commit before documentation sync: `360046f4edc680dd4f50421ad9dd4c7576eaa763`  
Final validation run: `30338083011`

## Audit rule

A passing command is not treated as scientific correctness, real-engine execution evidence or proof that every GitHub account setting is enabled. Capabilities that could not be inspected through the available GitHub App remain `NOT VERIFIED` rather than inferred.

No branch or pull request was created. The user-mandated `main`-only policy was preserved throughout the remediation.

## Final acceptance summary

The final hosted run passed:

- locked Python 3.10 quality and security gate;
- locked Python 3.12 quality and security gate;
- locked Python 3.13 quality and security gate;
- 127 unit tests across nine non-empty suites;
- Ruff lint and formatting;
- isolated mypy checks across 18 targets;
- Bandit production audit with exact reviewed allowances;
- repository, dependency, constraints, packaging, catalog, Agent-eval, governance, capability-claim, secret-pattern, ignore-marker, AI-cover, visual and link gates;
- CodeQL Python `security-extended`;
- runtime, development and exact locked-environment `pip-audit`;
- locked CycloneDX JSON SBOM generation and artifact upload.

No failure artifact was generated for the final run because all blocking gates passed.

## Repository inventory and architecture

The repository is intentionally a **repository-style Agent Skill collection**, not a wheel-ready Python library. It contains eight independently installable Skills, shared root tooling, deterministic tests, scientific demo assets, governance files, three Python-version constraint snapshots and one permanent GitHub Actions workflow.

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

**Remediation:** every Skill contains an explicit **Untrusted content and instruction hierarchy** section. External content is data, cannot override system/developer/user authority, cannot request secrets, cannot weaken scientific gates and cannot authorize expensive or destructive execution.

A repository-level Agent security model and deterministic eval contracts cover prompt injection, scope isolation, approval gates, evidence escalation, routing ambiguity and destructive-operation ownership. `live_model_execution` remains `NOT_VERIFIED` until model/version traces and grader evidence are recorded.

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
- Agent security, packaging, scientific-claim and supply-chain policy documents.

`CITATION.cff` remains present and parseable.

### High — dependency reproducibility and security evidence

The library-facing dependency declarations keep compatible version ranges, while CI now consumes exact reviewed snapshots for Python 3.10, 3.12 and 3.13. Every constraint file:

- uses exact `name==version` pins;
- records the CPython version and source GitHub Actions run;
- includes every direct runtime and development requirement;
- rejects duplicate, non-exact and bootstrap-tool pins.

Hosted CI installs against the matching constraint, runs `pip check`, audits runtime/development ranges and the exact locked Python 3.12 environment, and generates an SBOM from the locked environment. A weekly scheduled run refreshes vulnerability and CodeQL evidence without silently changing constraints.

### Medium — scientific and capability claim escalation

A machine-readable claim policy now defines the exact L0–L3 levels, forbidden public claim phrases and immutable L3 evidence fields. `scripts/validate_capability_claims.py` cross-checks:

- every capability ID, Skill and implementation script;
- the declared support level;
- prohibition of `execution_evidence` below L3;
- required engine, version, site, run ID and artifact SHA-256 for L3;
- public README and Skill wording against forbidden unsupported claims.

Parser tests, scheduler completion and synthetic fixtures cannot promote a capability to `L3_EXECUTION_TESTED`.

### Medium — deterministic secret detection

A high-confidence offline scanner rejects private-key headers, GitHub/OpenAI/AWS/Google/Slack credential patterns, secret-bearing filenames and oversized unreviewed text inputs. Tests construct synthetic patterns at runtime so the repository never embeds literal credential-like fixtures. GitHub secret scanning and push protection remain account-level settings and are still `NOT VERIFIED`.

### Medium — unsafe XML parsing

The four SVG/XML validators use `defusedxml` instead of unsafe standard-library parsing entry points. Regression tests reject a return to `xml.etree.ElementTree` in those validators.

### Medium — static typing

The isolated mypy gate covers root scripts/tests and every Skill script/test space independently. This avoids invalid duplicate-top-level-module inference while still type-checking all 18 targets. The final run reports zero mypy failures.

### Medium — Bandit findings

Confirmed code findings were repaired:

- unsafe YAML workflow parsing replaced by `yaml.safe_load`, with explicit support for YAML 1.1 interpreting `on` as Boolean `True`;
- production installer assertion replaced by a runtime safety error.

The remaining low-risk findings are exact `(path, test_id)` contracts with non-empty rationales. They cover fixed internal subprocess argv calls and one seeded non-cryptographic RNG used for reproducible scientific splitting. The allowlist is regression-tested as an exact set; new or stale allowances fail CI.

### Medium — trigger collisions and Agent evaluation

Trigger overlap is not blindly removed because multi-Skill collaboration is scientifically valid. Routing precedence, root-orchestrator authority, specialised-profile scope and support-level escalation are represented in deterministic Agent eval contracts.

### Medium — packaging ambiguity

The repository is explicitly classified as a Skill collection. Validation prevents unsupported wheel claims and tests the real installer instead of manufacturing a misleading Python distribution.

## Permanent quality gate

The final gate order is:

```text
versioned demo assets
→ dependency and version contract
→ cross-version exact CI constraints
→ repository-only packaging model
→ DFT catalog
→ Agent eval contracts
→ governance and workflow policy
→ capability and scientific-claim boundaries
→ high-confidence secret patterns
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

`.github/workflows/ci.yml` is the only permanent workflow. It runs on `main` pushes, pull requests, manual dispatch and a weekly schedule. The blocking authority is the native GitHub Actions job result. Compatibility status publication is best-effort and cannot turn passing code into a false failure.

The permanent workflow does not use `pull_request_target`, `workflow_run`, issue-triggered writes, `contents: write` or unpinned third-party Actions.

## Final test distribution

| Suite | Tests |
|---|---:|
| Root repository and security contracts | 52 |
| `tsao-dft-suite` | 4 |
| `tsao-dft-researcher` | 16 |
| `tsao-structure-prep` | 5 |
| `tsao-periodic-dft-materials` | 11 |
| `tsao-dft-ml-active-learning` | 16 |
| `tsao-dft-hpc-provenance` | 13 |
| `tsao-dft-kinetics-multiscale` | 5 |
| `tsao-dft-catalysis-profile` | 5 |
| **Total** | **127** |

## GitHub settings not verified

The available GitHub App did not expose authoritative state for:

- branch protection and force-push/deletion rules;
- signed-commit requirements;
- CodeQL default setup outside the versioned workflow;
- Dependabot alert settings;
- secret scanning and push protection;
- private vulnerability-reporting configuration.

These settings remain **NOT VERIFIED**. The repository files and hosted workflow compensate where possible, but they do not prove account-level configuration.

## Scientific non-claims

The audit validates repository engineering and deterministic adapters. It does not establish real licensed execution of Gaussian, VASP, Quantum ESPRESSO, CP2K, Multiwfn, VMD, Slurm/PBS, DeepChem/GNN or Cantera. Selected capabilities remain `L2_VALIDATED_ADAPTER` until immutable engine/version/site evidence supports a scoped `L3_EXECUTION_TESTED` claim.

## Residual risks and future work

- Main-only direct writes reduce review separation; this is a deliberate user governance exception.
- Real-engine and real-HPC regressions remain external.
- Live-model Agent eval execution and cross-model stability remain `NOT_VERIFIED`; current evals are deterministic policy contracts.
- GitHub account-level branch protection, signed commits, Dependabot alerts, secret scanning, push protection and private reporting remain `NOT VERIFIED`.
- Self-contained utility duplication requires disciplined synchronized maintenance.
- External-link availability is not tested by deterministic CI; local links are fully validated offline.
- Security and dependency data can change after the recorded run and are re-audited weekly and before release.

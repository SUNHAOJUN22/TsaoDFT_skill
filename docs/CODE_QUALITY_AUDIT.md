# Code Quality and Test Audit

Date: 2026-07-28  
Branch: `main`  
Validated source commit before documentation sync: `360046f4edc680dd4f50421ad9dd4c7576eaa763`  
GitHub Actions run: `30338083011`

## Evidence rule

A passing parser, fixture, static analysis or scheduler test is engineering evidence, not proof of scientific correctness or legal real-engine execution. Unsupported or account-level facts remain `UNKNOWN` / `NOT VERIFIED`.

## Scope reviewed

- every permanent GitHub Actions job, permission, trigger and failure-log path;
- `scripts/quality_gate.py`, `scripts/run_all_tests.py` and all root validators;
- all root tests and all eight per-Skill test suites;
- installer copy, symlink, force, backup and uninstall paths;
- subprocess, deletion, path, XML/YAML, random seed, timeout and serialization behavior;
- runtime/development ranges and Python 3.10/3.12/3.13 exact constraints;
- capability, support-level, Agent-eval, prompt-injection and scientific-claim contracts;
- README, visual, asset, link, governance, packaging and supply-chain evidence.

## Closed findings

### Dependency and resolver drift

`requirements.txt`, `requirements-dev.txt`, `pyproject.toml`, `VERSION`, Python floor and Ruff target are cross-checked offline. Exact reviewed constraints now lock every CI environment and are validated for provenance, direct dependency coverage, uniqueness and exact pins.

### Quality-stage hangs and false JSON

Every quality stage has an explicit timeout; the test stage has a larger bound. Timeout returns code 124 with a deterministic record. `--json` captures child output and emits one machine-readable document.

### CI false failures

Native GitHub Actions jobs remain the blocking authority. Compatibility statuses retry and use `continue-on-error`. Failure logs upload only for a real gate failure. Each matrix job installs against its matching constraint and runs `pip check`.

### Static quality and security

- Ruff lint and formatter are blocking;
- mypy covers 18 isolated module spaces;
- Bandit scans production sources against exact reviewed allowances;
- all Python files compile during strict repository audit;
- `defusedxml` replaces unsafe SVG/XML parsers;
- high-confidence secret patterns and secret-bearing filenames are rejected;
- all reusable Actions are pinned to complete commit SHAs.

### Installer safety

The installer proves ownership through records and content hashes before replacement or uninstall. It refuses foreign directories, root/home targets, changed symlinks and modified copies without an explicit backup/removal decision. Copy installation is staged and atomically replaced.

### Agent and scientific integrity

Deterministic policy evals cover routing, ambiguity, multi-Skill conflicts, profile isolation, prompt injection, unauthorized tools, destructive actions, support escalation, fabrication, provenance loss, recovery, idempotency and version stability. Live-model execution remains `NOT_VERIFIED`.

The capability validator prevents public unsupported claims and requires immutable engine/version/site/run/artifact evidence for any L3 declaration.

## Final quality gate

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

## Acceptance result

- Python 3.10 hosted gate: PASS;
- Python 3.12 hosted gate: PASS;
- Python 3.13 hosted gate: PASS;
- CodeQL `security-extended`: PASS;
- runtime/development/locked `pip-audit`: PASS;
- locked CycloneDX SBOM: PASS;
- tests: 127 across nine non-empty suites, zero failed suites;
- no branch or pull request created.

## Remaining limits

- GitHub account-level branch protection, signed commits, secret scanning, push protection, Dependabot alerts and private reporting are `NOT VERIFIED` through the available App.
- Real-engine/site execution and live-model Agent eval traces remain external and must not be inferred from repository tests.
- The main-only policy is a deliberate review-separation exception.

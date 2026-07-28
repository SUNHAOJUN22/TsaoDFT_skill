# Code Quality and Test Audit

Date: 2026-07-28  
Branch: `main`  
Validated source commit before documentation sync: `bcdfca6e81ae977287702fd6f4aba9f8cfa93e46`  
GitHub Actions run: `30344814556`

## Evidence rule

A passing parser, fixture, static analysis, scheduler test or acceleration planner is engineering evidence, not proof of scientific correctness, legal real-engine execution or measured speedup. Unsupported or account-level facts remain `UNKNOWN` / `NOT VERIFIED`.

## Scope reviewed

- every permanent GitHub Actions job, permission, trigger and failure-log path;
- `scripts/quality_gate.py`, `scripts/run_all_tests.py` and all root validators;
- all root tests and all eight per-Skill test suites;
- installer copy, symlink, force, backup and uninstall paths;
- subprocess, deletion, path, XML/YAML, random seed, timeout and serialization behavior;
- runtime/development ranges and Python 3.10/3.12/3.13 exact constraints;
- capability, support-level, Agent-eval, prompt-injection and scientific-claim contracts;
- README, visual, asset, link, governance, packaging and supply-chain evidence;
- GPU/CUDA-X/native-code/edge planning decisions, deterministic output and invalid-profile handling.

## Closed findings

### Dependency and resolver drift

`requirements.txt`, `requirements-dev.txt`, `pyproject.toml`, `VERSION`, Python floor and Ruff target are cross-checked offline. Exact reviewed constraints lock every CI environment and are validated for provenance, direct dependency coverage, uniqueness and exact pins.

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

The capability validator prevents public unsupported claims and requires immutable engine/version/site/run/artifact evidence for any L3 declaration. GPU allocation, CUDA-X selection and generated plans remain below L3 until real engine/build/hardware benchmarks exist.

### Acceleration planner quality

The new planner:

- validates engine, execution stage, target class, GPU vendor/topology, precision policy and requested acceleration libraries;
- distinguishes engine-native GPU builds, CPU MPI/OpenMP, atomistic-ML surrogate and edge-orchestrated routes;
- records explicit `recommended`, `benchmark`, `engine-build`, `not-drop-in` and `not-applicable` decisions;
- keeps Python on the control plane and native code behind tested, narrow interfaces with a CPU fallback;
- rejects an NVIDIA engine build without an NVIDIA GPU;
- produces deterministic reports from the same profile;
- never launches an engine or promotes a plan into a measured performance claim.

Ten new unit tests cover the VASP, Quantum ESPRESSO, CP2K, equivariant-ML, cuTENSOR, edge, CPU fallback, invalid GPU-build and determinism branches.

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
- tests: 137 across nine non-empty suites, zero failed suites;
- one permanent workflow: `.github/workflows/ci.yml`;
- no branch or pull request created.

## Remaining limits

- GitHub account-level branch protection, signed commits, secret scanning, push protection, Dependabot alerts and private reporting are `NOT VERIFIED` through the available App.
- Real-engine/site/GPU execution and live-model Agent eval traces remain external and must not be inferred from repository tests.
- The main-only policy is a deliberate review-separation exception.

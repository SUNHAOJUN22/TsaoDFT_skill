# Test Report

Date: 2026-07-28  
Version: `0.4.0-alpha.1`  
Validated source commit before documentation sync: `bcdfca6e81ae977287702fd6f4aba9f8cfa93e46`  
GitHub Actions run: `30344814556`

## Result

**PASS — 137 unit tests across 9 isolated suites, 0 failed suites.**

| Suite | Tests | Result |
|---|---:|---|
| Root repository, installer safety, Agent evals, constraints, capability claims, secret scanning, dependency/packaging/governance/security contracts, visual and link validation | 52 | PASS |
| `tsao-dft-suite` | 4 | PASS |
| `tsao-dft-researcher` | 16 | PASS |
| `tsao-structure-prep` | 5 | PASS |
| `tsao-periodic-dft-materials` | 11 | PASS |
| `tsao-dft-ml-active-learning` | 16 | PASS |
| `tsao-dft-hpc-provenance` | 23 | PASS |
| `tsao-dft-kinetics-multiscale` | 5 | PASS |
| `tsao-dft-catalysis-profile` | 5 | PASS |

Every discovered suite must execute at least one test. A missing, unparseable or zero-test suite fails the repository quality gate instead of producing a false green result.

## Permanent deterministic quality gate

The one-command gate executes, in order:

1. all eight versioned deterministic demo assets;
2. dependency, Python-version and release contracts;
3. exact Python 3.10, 3.12 and 3.13 CI constraint contracts;
4. repository-only packaging model;
5. DFT catalog validation;
6. Agent eval contracts;
7. governance and workflow policy;
8. capability and scientific-claim boundaries;
9. high-confidence secret patterns and secret-bearing filenames;
10. explained ignore-marker audit;
11. governed AI cover integrity;
12. bilingual README visual completeness;
13. offline local-link validation;
14. Ruff lint;
15. Ruff formatting;
16. isolated mypy checks across 18 targets;
17. Bandit production audit with exact reviewed allowances;
18. strict repository audit;
19. all nine non-empty unittest suites.

Each stage has an explicit timeout. JSON mode captures child output and remains machine-readable.

## Hosted CI evidence

Run `30344814556` completed successfully with:

- locked Python 3.10 quality gate: PASS;
- locked Python 3.12 quality gate: PASS;
- locked Python 3.13 quality gate: PASS;
- CodeQL Python `security-extended`: PASS;
- runtime dependency-range `pip-audit`: PASS;
- development dependency-range `pip-audit`: PASS;
- exact locked-environment `pip-audit`: PASS;
- locked CycloneDX JSON SBOM generation and upload: PASS;
- no failure-log artifact, because every blocking gate passed.

The GitHub Actions workflow is the only permanent workflow, runs weekly as well as on `main`, PR and manual triggers, and pins every reusable Action to a full commit SHA. The one-shot formatter workflow used during remediation was deleted after its exact output was committed.

## Security and Agent coverage

The root suite includes deterministic checks for:

- installer ownership records, atomic copy, safe replacement, backup and uninstall behavior;
- refusal to overwrite or uninstall foreign directories;
- refusal to use the home directory or repository root as an installation target;
- exact symlink ownership and modified-copy handling;
- prompt-injection and untrusted-content boundaries in all eight Skills;
- Agent eval categories, unique identifiers and evidence requirements;
- capability scripts, support levels, forbidden public claims and immutable L3 evidence fields;
- exact constraints, provenance headers, direct dependency inclusion and forbidden bootstrap pins;
- high-confidence private-key/token patterns and secret-bearing filenames;
- `defusedxml` use in SVG/XML validators;
- governance files, main-only exception, scheduled workflow, trigger and action-pin policy;
- exact Bandit allowance contracts and non-empty justifications;
- dependency drift, Python floor, Ruff target and PEP 440 version consistency;
- quality-stage timeout and `--skip-tests` behavior;
- deterministic AI/demo asset integrity and offline README links.

## Static quality and repository hygiene

- Ruff is pinned and enforced for lint and formatting;
- mypy runs in isolated repository and per-Skill module spaces;
- Bandit scans production code and rejects unreviewed findings;
- unsafe `xml.etree.ElementTree` entry points were replaced by `defusedxml`;
- unsafe YAML workflow parsing was replaced by `yaml.safe_load` with explicit handling of YAML 1.1's `on` key behavior;
- production installer assertions were replaced by runtime safety errors;
- runtime and development dependencies retain compatible ranges in project metadata;
- exact Python-version constraints make CI resolution reproducible;
- obsolete bootstrap, patch-bundle, repair and workflow-probe files are forbidden;
- `.github/workflows/ci.yml` is the only permanent workflow;
- `pip check` validates each installed CI environment.

## Scientific and performance coverage

The 137 tests cover DFT-first routing, method fingerprints, cross-Skill handoffs, Gaussian preflight and synthetic parsing, minimum/TS/IRC acceptance, Multiwfn recipes, uncertainty budgets, structure mapping, VASP/QE/CP2K adapters, convergence and compatibility gates, provenance-safe DFT datasets, leakage controls, adaptive ridge solvers, HPC scripts and arrays, restart lineage, thermodynamic closure, uncertainty propagation, Cantera-oriented handoff, catalyst scope, figure manifests and deterministic scientific demonstrations.

The ten new acceleration tests cover:

- engine-native VASP GPU planning with the OpenACC, one-rank-per-GPU, `NCORE=1`, `KPAR` and NCCL starting points;
- Quantum ESPRESSO pools, task groups, diagonalization and empirical decomposition;
- CP2K CUDA, DBCSR/GRID/DBM/PW and ELPA planning;
- cuEquivariance only for equivariant atomistic ML;
- cuTENSOR rejection as a drop-in VASP flag;
- edge orchestration for production DFT;
- CPU fallback and CUDA-X non-applicability;
- rejection of a GPU engine build without a GPU;
- deterministic repeatability.

Performance regression coverage also protects memory-mapped periodic parsers, streaming SHA-256, bounded canonical dataset hashing, primal/dual ridge equivalence and Slurm-array compaction.

## Commands

```bash
python -m pip install -c constraints/py312.txt -r requirements-dev.txt
python -m pip check
python scripts/quality_gate.py
```

Focused diagnostics:

```bash
python scripts/generate_readme_demos.py
python scripts/validate_dependencies.py
python scripts/validate_constraints.py
python scripts/validate_packaging_model.py
python scripts/validate_catalog.py
python scripts/validate_agent_evals.py
python scripts/validate_governance.py
python scripts/validate_capability_claims.py
python scripts/validate_secrets.py
python scripts/validate_ignore_markers.py
python scripts/validate_ai_assets.py
python scripts/validate_readme_visuals.py --strict
python scripts/validate_readme_links.py
python -m ruff check .
python -m ruff format --check .
python scripts/run_type_checks.py
python scripts/run_bandit.py
python scripts/validate_repo.py --strict
python scripts/run_all_tests.py
python skills/tsao-dft-hpc-provenance/scripts/plan_acceleration.py \
  skills/tsao-dft-hpc-provenance/templates/acceleration-profile.yaml
```

## Important non-claims

The tests use deterministic fixtures and synthetic output excerpts. They do not establish licensed real-engine execution or measured GPU acceleration for Gaussian, VASP, Quantum ESPRESSO, CP2K, Multiwfn, VMD, Slurm/PBS, DeepChem/GNN or Cantera. Selected capabilities therefore remain **L2 validated adapters**, not L3 execution-tested engines. L3 requires immutable evidence from the legal engine, version, build, hardware and site.

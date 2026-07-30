# Test Report

Date: 2026-07-30  
Version: `0.4.0-alpha.1`  
Code qualification source commit before documentation closure: `3f43bb8266dd3e218b3df6f0e48d7f4861113908`  
Code qualification GitHub Actions run: `30557385623`

## Result

**PASS — 325 unit tests across 9 isolated suites, 0 failed suites.**

| Suite | Tests | Result |
|---|---:|---|
| Root repository, installer transactions, governance, capability claims, coverage infrastructure and security contracts | 99 | PASS |
| `tsao-dft-suite` | 4 | PASS |
| `tsao-dft-researcher` | 32 | PASS |
| `tsao-structure-prep` | 5 | PASS |
| `tsao-periodic-dft-materials` | 11 | PASS |
| `tsao-dft-ml-active-learning` | 16 | PASS |
| `tsao-dft-hpc-provenance` | 148 | PASS |
| `tsao-dft-kinetics-multiscale` | 5 | PASS |
| `tsao-dft-catalysis-profile` | 5 | PASS |
| **Total** | **325** | **PASS** |

Every discovered suite must execute at least one test. Missing, unparseable, timed-out or zero-test suites fail the quality gate.

## Permanent quality gate

The one-command gate executes, in order:

1. all eight deterministic demo assets;
2. dependency, Python-version and release contracts;
3. exact Python 3.10, 3.12 and 3.13 CI constraints;
4. repository-only packaging model;
5. catalog and Agent-eval contracts;
6. governance, capability and scientific-claim boundaries;
7. secret and ignore-marker audits;
8. governed AI cover, bilingual visuals and offline links;
9. Ruff lint and formatting;
10. isolated mypy checks across 18 targets;
11. strict mypy for the four trust-boundary modules;
12. statement and branch coverage;
13. Bandit production audit;
14. strict repository audit;
15. all nine unittest suites.

All stages have explicit timeouts. JSON mode captures child output and remains machine-readable.

## Coverage

| Scope | Statement | Branch |
|---|---:|---:|
| Entire repository | **92.48%** | **80.18%** |
| Required minimum | 90.00% | 80.00% |

Trust-boundary core modules:

| Module | Statement | Branch |
|---|---:|---:|
| `shell_contract.py` | 100.00% | 100.00% |
| `trust_boundary.py` | 100.00% | 100.00% |
| `engine_parser_contract.py` | 100.00% | 100.00% |
| `benchmark_bridge.py` | 100.00% | 100.00% |
| `generate_job_script.py` | 100.00% | 98.53% |
| `validate_hpc_manifest.py` | 100.00% | 98.57% |

Coverage is collected across the nine isolated test subprocesses, including subprocess-launched production CLIs. Each Python matrix job uploads a machine-readable `coverage-report.json` artifact.

## Hosted CI evidence

Run `30557385623` completed successfully with:

- Python 3.10 quality gate: PASS;
- Python 3.12 quality gate: PASS;
- Python 3.13 quality gate: PASS;
- Ruff lint and formatting: PASS;
- isolated mypy across 18 targets: PASS;
- trust-boundary strict mypy across four targets: PASS;
- statement/branch coverage: PASS;
- Bandit: PASS;
- strict repository audit: PASS;
- 325 tests across nine suites: PASS;
- CodeQL Python `security-extended`: PASS;
- runtime dependency-range `pip-audit`: PASS;
- development dependency-range `pip-audit`: PASS;
- exact locked-environment `pip-audit`: PASS;
- locked CycloneDX JSON SBOM generation and upload: PASS.

`.github/workflows/ci.yml` is the only permanent workflow. It uses read-only repository contents permission and contains no code-push step.

## Trust-boundary coverage

The hardened execution and evidence tests include:

- structured argv rendering and rejection of raw shell command fields;
- scheduler-header, path, environment-variable and control-character injection boundaries;
- Manifest-bound execution approval;
- Ed25519 attestation verification, key fingerprint, scope, time and binding failures;
- executable Draft 2020-12 Schemas before semantic validation;
- executable Policy fields and multi-plan isolation;
- atomic content-addressed evidence publication, reuse, collision, tamper and rollback paths;
- Gaussian Link1 final-job precedence;
- VASP fatal-marker and convergence precedence;
- Quantum ESPRESSO routine-error and non-convergence precedence;
- CP2K abort and non-convergence precedence;
- deterministic parser-to-benchmark bridges with explicit missing fields;
- installer marker-write rollback and concurrent installation locking;
- root capability enforcement for generic L3 and signed acceleration L3 contracts.

## Scientific non-claims

The test suite uses deterministic fixtures and synthetic output excerpts. It does not establish licensed real-engine execution or measured GPU acceleration for Gaussian, VASP, Quantum ESPRESSO, CP2K, Multiwfn, VMD, Slurm/PBS, DeepChem/GNN or Cantera.

The public capability remains `L2_VALIDATED_ADAPTER`. `QUALIFIED_FOR_SCOPED_L3_PERFORMANCE_EVIDENCE` is only evidence-package eligibility. Public L3 additionally requires legal real-engine/site execution, versioned build and hardware identity, repeated numerical equivalence, a verified content-addressed evidence root, an Ed25519-signed independent review bound to policy/plan/candidates, and explicit capability registration.

## Commands

```bash
python -m pip install -c constraints/py312.txt -r requirements-dev.txt
python -m pip check
python scripts/quality_gate.py
```

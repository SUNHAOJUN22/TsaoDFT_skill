# Test Report

Date: 2026-07-24  
Version: `0.4.0-alpha.1`

## Result

**PASS — 63 unit tests across 9 isolated suites, 0 failed suites.**

| Suite | Tests | Result |
|---|---:|---|
| Repository, catalog, installer, plugin, AI-image governance, README assets and strict validator | 10 | PASS |
| `tsao-dft-suite` | 4 | PASS |
| `tsao-dft-researcher` | 16 | PASS |
| `tsao-structure-prep` | 4 | PASS |
| `tsao-periodic-dft-materials` | 7 | PASS |
| `tsao-dft-ml-active-learning` | 5 | PASS |
| `tsao-dft-hpc-provenance` | 7 | PASS |
| `tsao-dft-kinetics-multiscale` | 5 | PASS |
| `tsao-dft-catalysis-profile` | 5 | PASS |

## Deterministic coverage

- AI-generated README asset manifest, SHA-256 integrity, dimensions, generation provenance, visible disclosure and non-quantitative policy;
- DFT-first routing, cross-Skill handoff and method fingerprint validation;
- Gaussian input preflight and rich synthetic log parsing;
- minimum/TS evidence, TS/IRC manifest rules, thermochemistry, S², orbital, dipole, NMR and TD fields;
- Multiwfn semantic recipe and DFT uncertainty-budget validation;
- XYZ geometry audit and atom-order mapping;
- VASP INCAR/POSCAR/KPOINTS preflight and OUTCAR parsing;
- QE `pw.x` input/output parsing;
- CP2K Quickstep input/output parsing;
- periodic project and energy-compatibility gates plus convergence analysis;
- DFT-labelled dataset provenance/leakage checks, grouped NumPy ridge baseline and model card;
- engine-aware Slurm/PBS/local script generation, site profile, resource estimate and restart lineage;
- reaction-network element/charge/site balance, Eyring rates, thermodynamic closure, barrier uncertainty and Cantera-oriented handoff;
- scoped catalyst coordination campaign and claim-strength validation;
- research/figure manifests, VMD Tcl generation, energy-profile figures and synthetic README figure determinism.

## Commands

```bash
python -m pip install -r requirements.txt
python scripts/generate_readme_demos.py
python scripts/validate_catalog.py
python scripts/validate_ai_assets.py
python scripts/validate_repo.py --strict
python scripts/run_all_tests.py
```

## Important non-claims

The tests use deterministic source fixtures and synthetic output excerpts. The current environment did not execute licensed Gaussian or VASP calculations, a real Quantum ESPRESSO/CP2K campaign, Multiwfn menu jobs, VMD/Tachyon ray tracing, Slurm/PBS submissions, DeepChem/GNN training, or Cantera reactor simulations.

Therefore the release records selected capabilities as **L2 validated adapters**, not L3 execution-tested engines. L3 requires immutable real-engine/version/site regression evidence supplied legally by the user or laboratory.

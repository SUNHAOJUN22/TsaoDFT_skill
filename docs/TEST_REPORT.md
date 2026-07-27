# Test Report

Date: 2026-07-27  
Version: `0.4.0-alpha.1`

## Result

**PASS — 92 unit tests across 9 isolated suites, 0 failed suites.**

| Suite | Tests | Result |
|---|---:|---|
| Repository, catalog, installer, plugin, minimal AI-cover governance, demo-asset integrity, curated README visual completeness, offline link integrity and strict validator | 17 | PASS |
| `tsao-dft-suite` | 4 | PASS |
| `tsao-dft-researcher` | 16 | PASS |
| `tsao-structure-prep` | 5 | PASS |
| `tsao-periodic-dft-materials` | 11 | PASS |
| `tsao-dft-ml-active-learning` | 16 | PASS |
| `tsao-dft-hpc-provenance` | 13 | PASS |
| `tsao-dft-kinetics-multiscale` | 5 | PASS |
| `tsao-dft-catalysis-profile` | 5 | PASS |

Every discovered suite must execute at least one test. A missing, unparseable or zero-test suite fails the repository quality gate instead of producing a false green result.

## Static quality and repository hygiene

- Ruff is pinned in `requirements-dev.txt` and enforced for both lint and formatting;
- the initial full-repository Ruff audit identified 1,173 findings across 94 Python files;
- automated normalization was followed by exact review and repair of the remaining semantic and robustness findings;
- the final enforced Ruff result is zero findings;
- runtime dependencies have explicit compatible upper bounds;
- obsolete bootstrap, patch-bundle and workflow-probe files were removed;
- strict validation rejects private root bundles, workflow probes, backup/editor files, empty files and large encoded bootstrap payloads;
- `.github/workflows/ci.yml` is the only permitted workflow file;
- GitHub Actions dependencies are pinned to immutable Node 24-compatible commit SHAs.

## Efficiency coverage

- VASP, Quantum ESPRESSO and CP2K parsers remain memory-mapped and are protected against regression to `Path.read_text`;
- provenance and structure hashes stream file bytes and preserve exact SHA-256 values;
- the DFT dataset hash preserves historical canonical bytes with a one-shot/small and bounded-batch/large hybrid;
- ridge tests cover primal/dual equivalence, automatic selection, `alpha = 0`, non-finite rejection, data shape and constant-feature metadata;
- Slurm array tests cover 1,000-task compaction, concurrency limits, non-Slurm rejection, thread oversubscription, per-node capacity and runtime approval guards;
- `scripts/benchmark_performance.py` reproduces implementation-only comparisons against the frozen baseline;
- measured results, sources and rejected candidates are recorded in `docs/PERFORMANCE_AUDIT.md` and `docs/PERFORMANCE_GUIDE.md`.

## Visual, link and deterministic coverage

- exactly one governed AI-assisted README cover, with SHA-256 integrity, dimensions, provenance, visible disclosure and non-quantitative policy;
- no AI module-card gallery or deprecated `assets/ai/modules/` references;
- curated bilingual README embedding of the cover and five representative deterministic demonstrations;
- strict read-only validation of all eight versioned demo SVGs, including XML, exact dimensions, titles, accessible descriptions and visible synthetic-data notices;
- offline validation of every bilingual README local file, directory and Markdown-anchor link, while external URLs are never requested;
- explicit failure for missing, unsafe or unsupported local link targets;
- explicit failure for missing, degraded or placeholder demo assets, with no automatic fallback writes;
- explicit rejection of wording that presents conceptual illustrations as calculated orbitals, surfaces or scientific results;
- local full-width and half-width raster review of the `uiux_pro_v7_dark_scientific_os` overview and all eight dark deterministic demo assets before publication;
- one documented dark scientific README design system with consistent palette, typography, density, accessible status labels and anti-pattern controls;
- complete bilingual README rewrite with the same governed overview, required deterministic figures, documentation map and scientific-boundary language.

## Scientific and workflow coverage

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
- research/figure manifests, VMD Tcl generation, energy-profile figures and synthetic README figure integrity.

## Commands

```bash
python -m pip install -r requirements-dev.txt
python scripts/quality_gate.py
```

Focused diagnostics:

```bash
python scripts/generate_readme_demos.py
python scripts/validate_catalog.py
python scripts/validate_ai_assets.py
python scripts/validate_readme_visuals.py --strict
python scripts/validate_readme_links.py
python scripts/benchmark_performance.py --quick
python -m ruff check .
python -m ruff format --check .
python scripts/validate_repo.py --strict
python scripts/run_all_tests.py
```

## Important non-claims

The tests use deterministic source fixtures and synthetic output excerpts. The current environment did not execute licensed Gaussian or VASP calculations, a real Quantum ESPRESSO/CP2K campaign, Multiwfn menu jobs, VMD/Tachyon ray tracing, Slurm/PBS submissions, DeepChem/GNN training, or Cantera reactor simulations.

Therefore the release records selected capabilities as **L2 validated adapters**, not L3 execution-tested engines. L3 requires immutable real-engine/version/site regression evidence supplied legally by the user or laboratory.

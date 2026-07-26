# Changelog

## Unreleased — README visual and CI hardening

- Rebuilt the README visual system as the governed `premium_scientific_v3` hero and seven-module gallery, with local raster review, dimensions and SHA-256 records.
- Added bilingual README cross-validation against the governed AI asset manifest and all eight deterministic demo assets.
- Replaced the old demo placeholder fallback with a strict, read-only SVG integrity validator; missing or degraded figures now fail CI instead of silently generating low-quality artwork.
- Hardened CI with Python 3.10/3.12/3.13, pip caching, concurrency control, failure-log artifacts, commit statuses and manual dispatch.
- Removed obsolete issue-triggered bootstrap, README-patch, clean-rebuild and self-attestation workflows; `ci.yml` is the single permanent quality gate.
- Removed stale maintenance payloads and closed the obsolete bootstrap-probe issue.
- Expanded the repository test count from 63 to 68 with AI-governance, bilingual visual-completeness and read-only demo-validator coverage.

## 0.4.0-alpha.1 — 2026-07-24

- Added `tsao-dft-suite`, a DFT-first root orchestrator that routes molecular, periodic, ML, HPC, kinetics, and scoped catalysis work without hiding scientific decisions.
- Introduced explicit engine support levels (`L0_REFERENCE` through `L3_EXECUTION_TESTED`) and machine-readable capability status.
- Added cross-Skill handoff and method-fingerprint validators.
- Deepened Gaussian parsing with method/solvent/grid/dispersion inference, orbital energies, dipole, NMR, TD transition contributions, final coordinates, spin diagnostics, IRC direction records, and structured error taxonomy.
- Deepened structure preparation with XYZ geometry inspection and atom-order/mapping validation.
- Added deterministic VASP, Quantum ESPRESSO, and CP2K input preflight/output parsers plus convergence analysis. These are validation adapters; no licensed POTCAR or pseudopotentials are distributed.
- Added DFT-specific dataset validation, a NumPy ridge baseline, model-card validation, and active-learning provenance checks.
- Added HPC site-profile, resource-estimate, and restart-lineage validation.
- Added thermodynamic-closure, uncertainty-propagation, and Cantera-handoff tools for DFT-derived kinetics.
- Deepened the optional catalysis profile with coordination-campaign generation and claim-scope validation.
- Expanded tests, documentation, plugin metadata, and CI. Repository policy remains `main` only.

## 0.3.0-alpha.1 — 2026-07-24

- Indexed the uploaded AI for Science Skill catalog and integrated DFT/computational-chemistry entries into a seven-Skill suite.

## 0.2.0-alpha.1 — 2026-07-23

- Integrated Gaussian/Multiwfn/VMD research, evidence and publication-figure workflows.

## 0.1.0-alpha.1

- Initial packaged computational-chemistry Skill.

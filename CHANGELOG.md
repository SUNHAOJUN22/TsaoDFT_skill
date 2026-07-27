# Changelog

## Unreleased — compute efficiency, README visual, CI and repository hardening

- Added a second performance-audit pass with chunked file hashes, bounded canonical dataset hashing, Slurm-array compaction and reproducible baseline microbenchmarks.
- Added approval-gated Slurm array generation, streamed JSONL task tables, unique per-task Gaussian scratch paths and OpenMP/BLAS/per-node oversubscription validation.
- Added finite-value, data-shape and constant-feature provenance to the adaptive NumPy ridge baseline without introducing SciPy.
- Added `docs/PERFORMANCE_AUDIT.md` with measured tradeoffs, primary sources, deferred candidates and real-node validation boundaries.
- Expanded the test baseline from 78 to 92 while preserving all nine isolated suites.
- Replaced repeated full-file VASP, Quantum ESPRESSO and CP2K output decoding with read-only memory-mapped evidence scans; selected fields and acceptance boundaries remain unchanged.
- Added automatic primal/dual ridge selection so wide DFT descriptor matrices solve the smaller sample-space system, with stable least squares for `alpha = 0` and solver provenance in the model card.
- Removed repeated duplicate-signature field sorting from the DFT dataset validator.
- Added eight regression tests for streaming parsers and adaptive ridge solvers, increasing the test count from 70 to 78.
- Added `docs/PERFORMANCE_GUIDE.md` with implementation benchmarks and official NumPy, Python, ASE and Slurm execution guidance.
- Upgraded pinned GitHub Actions to Node 24-compatible `checkout` v6, `setup-python` v6 and `upload-artifact` v7 commits.
- Refined the single README cover into the `premium_scientific_v5_editorial` composition: larger typography, one evidence rail, one electronic-structure core and one integrated molecular/periodic/provenance panel.
- Replaced the dense `premium_scientific_v3` module-card gallery with one restrained conceptual cover and a curated set of five deterministic README visuals.
- Deleted seven redundant AI module-card SVGs and prohibited deprecated `assets/ai/modules/` references from returning.
- Kept all eight deterministic demo assets under strict, read-only integrity validation while decoupling asset validation from README curation.
- Added bilingual README cross-validation for the single governed cover and the curated scientific demonstrations.
- Added an offline bilingual README link gate for local files, directories and Markdown anchors; external URLs are never requested by CI.
- Replaced the old demo placeholder fallback with strict SVG integrity checks; missing or degraded figures fail CI instead of generating low-quality artwork.
- Hardened CI with Python 3.10/3.12/3.13, pinned Ruff lint/format gates, dependency bounds, concurrency control, failure-log artifacts, commit statuses and manual dispatch.
- Removed obsolete issue-triggered bootstrap, README-patch, clean-rebuild and self-attestation workflows; `ci.yml` is the single permanent quality gate.
- Removed stale maintenance payloads, root patch bundles and workflow probes; closed obsolete maintenance issues.

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

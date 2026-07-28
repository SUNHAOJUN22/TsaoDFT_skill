# Changelog

## Unreleased — compute efficiency, README visual, CI and repository hardening

- Added a versioned real-benchmark result Schema, example record and performance-qualification policy covering engine/build/runtime, CPU/GPU identity, scheduler/site, method fingerprints, artifacts, scientific observables and performance metrics.
- Added deterministic JSON/YAML/JSONL/CSV evidence import, artifact SHA-256 verification, duplicate-run rejection, parser/build/hardware identity checks and optional non-invoking `sacct`, GNU `time -v`, NVIDIA, ROCm, Intel, Nsight and engine-parser adapters.
- Added numerical-equivalence-first comparison for input, method, model, convergence, energy, forces, stress and declared properties before any effective speedup is calculated.
- Added median/min/max/quartile/IQR/MAD/outlier statistics, CPU-to-GPU and single-to-multi-GPU speedups, strong-scaling efficiency, GPU-hours, CPU-core-hours, memory, SCF, I/O and optional energy-to-solution summaries.
- Added immutable benchmark evidence bundles and scoped L3 qualification states while ignoring self-reported support levels and prohibiting automatic public capability promotion.
- Expanded the deterministic baseline to 177 tests across nine suites; the HPC suite now contains 63 tests, including 29 real-evidence, negative-status, import, metric-adapter and immutable-bundle tests.
- Added an evidence-bounded DFT acceleration planner for workstation, HPC and edge targets, with deterministic routes for VASP, Quantum ESPRESSO, CP2K, Gaussian, atomistic ML surrogates and custom native kernels.
- Added explicit applicability decisions for cuBLAS, cuSOLVER, cuSOLVERMp, cuFFT, cuFFTMp, cuSPARSE, NCCL, NVSHMEM, cuTENSOR, cuEquivariance and CUTLASS instead of treating CUDA-X names as universal drop-in acceleration switches.
- Defined the Python control-plane and C++/Fortran/CUDA/OpenACC native-kernel boundary, CPU fallback, mixed-precision validation, MPI-rank/GPU mapping, edge orchestration and immutable real-engine benchmark requirements.
- Added acceleration Manifest contracts for backend/vendor compatibility, rank-per-GPU topology, oversubscription approval, CPU/GPU binding, precision, build fingerprints and benchmark-plan identity.
- Added Slurm `srun` generation with explicit CPU/GPU binding, one-GPU-per-task allocation for one-rank-per-GPU layouts, bad-exit propagation and scheduler-owned device visibility.
- Added runtime acceleration provenance for scheduler rank identity, visible-device mapping, NVIDIA GPU UUID, PCI bus ID, driver version, memory, acceleration profile, build fingerprint and benchmark-plan identity.
- Added deterministic acceleration campaign materialization that combines a matching engine Manifest and profile into an accelerated Manifest, an FP64 CPU reference, GPU scaling candidates and a CSV matrix; every candidate remains `pending` and no submission is performed.
- Preserved the earlier 148-test acceleration-planning and bound-execution baseline before adding the real-evidence qualification layer.
- Closed the extended hardening pass with exact Python 3.10/3.12/3.13 constraints, weekly hosted security runs, locked-environment `pip-audit`, locked CycloneDX SBOM, capability-claim enforcement and deterministic secret-pattern checks.
- Closed the full repository audit with hosted green runs on Python 3.10, 3.12 and 3.13, CodeQL `security-extended`, runtime/development/locked `pip-audit`, CycloneDX SBOM generation, isolated mypy and Bandit.
- Replaced unsafe workflow YAML loading with `yaml.safe_load` while handling YAML 1.1's Boolean interpretation of `on`, and replaced the production installer assertion with an explicit safety error.
- Converted the Bandit exception list into an exact reviewed `(path, test_id)` contract with substantive reasons; new, duplicate or stale entries fail regression tests.
- Completed a tracked-file, code, Skill, installer, governance, dependency, packaging and supply-chain audit with evidence recorded in `docs/REPOSITORY_FULL_AUDIT.md`.
- Rebuilt the installer around explicit ownership records, atomic staged copies, foreign-directory refusal, modified-install protection, safe backups and symlink-target verification.
- Added explicit untrusted-content and prompt-injection boundaries to all eight Skills plus `docs/AGENT_SECURITY_MODEL.md`.
- Added 13 versioned positive/adversarial Agent eval contracts and deterministic schema graders while retaining live cross-model execution as `NOT_VERIFIED`.
- Replaced standard-library SVG parsing with `defusedxml` and added permanent mypy and Bandit gates with exact low-risk justifications.
- Added `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, CODEOWNERS, issue/PR templates, third-party notices and supply-chain/packaging policies.
- Classified the project explicitly as a repository-style Skill suite rather than claiming an unsupported wheel/sdist distribution model.
- Added blocking runtime/development `pip-audit`, CycloneDX SBOM generation and CodeQL Python `security-extended` analysis to the pinned GitHub Actions workflow.
- Added an offline dependency contract across `requirements.txt`, `requirements-dev.txt`, `pyproject.toml`, `VERSION`, the Python floor and the Ruff target.
- Hardened `quality_gate.py` with per-stage timeouts, deterministic timeout records and machine-clean JSON output.
- Added regression tests for dependency drift and quality-gate semantics.
- Kept native GitHub Actions matrix jobs as the only blocking CI authority, added `pip check`, and changed compatibility status summaries to retried best-effort observability that cannot fail a passing job.
- Added `docs/CODE_QUALITY_AUDIT.md` with the repository-wide analysis, findings, remediation and acceptance criteria.
- Rebuilt the governed cover as `uiux_pro_v8_hero_evidence_bento`, using fresh AI-generated visual direction beneath deterministic vector typography, capability cards, workflow gates and evidence bento.
- Rewrote both README files from first principles around a Hero-Centric + Trust & Authority structure: 30-second positioning, evidence workflow, eight-Skill map, curated deterministic figures, support levels, quick start, quality gate and scientific boundaries.
- Updated both README files with the executable acceleration entry point, test baseline and the same GPU/CUDA-X/native-code/edge scientific boundaries.
- Updated the UI/UX Pro Max design-system record, generation provenance and AI manifest; verified the 1600×900 cover at full and half README widths.
- Regenerated all eight deterministic SVG demonstrations as high-contrast dark evidence dashboards with fixed dimensions, accessible titles/descriptions and visible synthetic-data labels.
- Added a second performance-audit pass with chunked file hashes, bounded canonical dataset hashing, Slurm-array compaction and reproducible baseline microbenchmarks.
- Added approval-gated Slurm array generation, streamed JSONL task tables, unique per-task Gaussian scratch paths and OpenMP/BLAS/per-node oversubscription validation.
- Added finite-value, data-shape and constant-feature provenance to the adaptive NumPy ridge baseline without introducing SciPy.
- Added `docs/PERFORMANCE_AUDIT.md` with measured tradeoffs, primary sources, deferred candidates and real-node validation boundaries.
- Replaced repeated full-file VASP, Quantum ESPRESSO and CP2K output decoding with read-only memory-mapped evidence scans; selected fields and acceptance boundaries remain unchanged.
- Added automatic primal/dual ridge selection so wide DFT descriptor matrices solve the smaller sample-space system, with stable least squares for `alpha = 0` and solver provenance in the model card.
- Removed repeated duplicate-signature field sorting from the DFT dataset validator.
- Added `docs/PERFORMANCE_GUIDE.md` with implementation benchmarks and official NumPy, Python, ASE, Slurm, CUDA-X and engine-acceleration guidance.
- Upgraded pinned GitHub Actions to Node 24-compatible `checkout` v6, `setup-python` v6 and `upload-artifact` v7 commits.
- Deleted seven redundant AI module-card SVGs and prohibited deprecated `assets/ai/modules/` references from returning.
- Kept all eight deterministic demo assets under strict, read-only integrity validation while decoupling asset validation from README curation.
- Added bilingual README cross-validation and an offline local-link gate; external URLs are never requested by deterministic CI.
- Removed obsolete issue-triggered bootstrap, README-patch, clean-rebuild, self-attestation and one-time repair workflows; `ci.yml` is the single permanent workflow.
- Removed stale maintenance payloads, root patch bundles and workflow probes; closed obsolete maintenance issues.

## 0.4.0-alpha.1 — 2026-07-24

- Added `tsao-dft-suite`, a DFT-first root orchestrator that routes molecular, periodic, ML, HPC, kinetics, and scoped catalysis work without hiding scientific decisions.
- Introduced explicit engine support levels (`L0_REFERENCE` through `L3_EXECUTION_TESTED`) and machine-readable capability status.
- Added cross-Skill handoff and method-fingerprint validators.
- Deepened Gaussian parsing with method/solvent/grid/dispersion inference, orbital energies, dipole, NMR, TD transition contributions, final coordinates, spin diagnostics, IRC direction records, and structured error taxonomy.
- Deepened structure preparation with XYZ geometry inspection and atom-order mapping validation.
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

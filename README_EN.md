# TsaoDFT Skill

<p align="center">
  <strong>DFT-first, evidence-locked and auditable research workflows for molecular and periodic systems</strong><br>
  Structure review → method fingerprint → execution → technical validation → analysis → multiscale handoff → figure and claim audit
</p>

<p align="center">
  <a href="README.md">中文</a> · <a href="README_EN.md">English</a>
</p>

<p align="center">
  <a href="https://github.com/SUNHAOJUN22/TsaoDFT_skill/actions/workflows/ci.yml"><img src="https://github.com/SUNHAOJUN22/TsaoDFT_skill/actions/workflows/ci.yml/badge.svg?branch=main" alt="CI"></a>
  <img src="https://img.shields.io/badge/Python-3.10%20%7C%203.12%20%7C%203.13-3776AB" alt="Python 3.10, 3.12 and 3.13">
  <img src="https://img.shields.io/badge/tests-92%20passing-16A34A" alt="92 tests passing">
  <img src="https://img.shields.io/badge/support-L0%E2%80%93L3-6D5DFB" alt="Support levels L0 to L3">
  <img src="https://img.shields.io/badge/license-MIT-16A34A" alt="MIT license">
</p>

> **AI image declaration | AI-GENERATED CONCEPTUAL ILLUSTRATION:** the cover below is an AI-assisted concept used only to communicate project identity. It is not a molecular structure, orbital, electrostatic potential, band structure, free-energy profile, mechanism, or experimental result. Quantitative claims require accepted source data, validated calculations and reproducible scripts.

<p align="center">
  <img src="assets/ai/hero/tsao-dft-hero.svg" width="100%" alt="TsaoDFT AI-assisted conceptual cover">
</p>

## What TsaoDFT is

`TsaoDFT_skill` is organised around the **DFT evidence chain**. A normal termination, an attractive surface plot, or a high model score is not silently promoted into a scientific conclusion. Work moves through explicit states:

```text
planned → prepared → completed → technically validated → scientifically accepted → claim accepted
```

The governing rule is simple: **calculations, artifacts and publication claims must remain traceable, while unresolved assumptions stay visible.**

<p align="center">
  <img src="assets/demo/workflow-architecture.svg" width="100%" alt="Auditable DFT research loop synthetic demo">
</p>

## Eight composable Skills

| Skill | Purpose | Boundary |
|---|---|---|
| [`tsao-dft-suite`](skills/tsao-dft-suite/) | DFT-first orchestration, task DAGs, support-level routing, cost and approval gates | Coordinates work; it does not replace engine-level judgement |
| [`tsao-structure-prep`](skills/tsao-structure-prep/) | Molecular, crystal, surface, defect and adsorption candidates plus atom mapping | Never silently chooses charge, spin, oxidation state or termination |
| [`tsao-dft-researcher`](skills/tsao-dft-researcher/) | Gaussian molecular DFT/TDDFT, Opt/Freq, TS/IRC, thermochemistry, NMR, Multiwfn and VMD | The deepest molecular adapter; real software remains external |
| [`tsao-periodic-dft-materials`](skills/tsao-periodic-dft-materials/) | VASP, Quantum ESPRESSO and CP2K, including surfaces, defects, bands/DOS, NEB and convergence | Does not distribute POTCAR, pseudopotentials or restricted databases |
| [`tsao-dft-hpc-provenance`](skills/tsao-dft-hpc-provenance/) | Local/Slurm/PBS execution, estimates, checkpoints, restart lineage and hashes | Scheduler success is not scientific acceptance |
| [`tsao-dft-ml-active-learning`](skills/tsao-dft-ml-active-learning/) | DFT-label audit, leakage prevention, applicability domain, uncertainty and active learning | Correlation and SHAP do not prove causality or mechanism |
| [`tsao-dft-kinetics-multiscale`](skills/tsao-dft-kinetics-multiscale/) | Eyring/TST, networks, detailed balance, uncertainty and microkinetic handoff | Consumes only accepted thermochemistry with explicit standard states |
| [`tsao-dft-catalysis-profile`](skills/tsao-dft-catalysis-profile/) | DCS/MCSOMe/DMOS, Si–O/Si–C, Ti/TEA, Ziegler–Natta and polyolefin catalysis | A scoped profile, never auto-applied to unrelated chemistry |

## Selected scientific demonstrations

The landing page now follows the **UI/UX Pro Max** design-system workflow: product classification, pattern, style, colors, typography, anti-pattern filtering and accessibility checks govern every asset. The resolved system is Hero-Centric + Evidence Bento, Swiss Modernism 2.0 and Accessible Minimalism. All eight deterministic demo SVGs remain versioned and validated; the README shows four representative figures plus the workflow overview above.

<table>
<tr>
<td width="50%"><img src="assets/demo/wavefunction-esp-gallery.svg" width="100%" alt="Wavefunction and ESP figure contract"></td>
<td width="50%"><img src="assets/demo/periodic-dft-materials.svg" width="100%" alt="Periodic DFT evidence"></td>
</tr>
<tr>
<td><img src="assets/demo/dft-ml-dashboard.svg" width="100%" alt="DFT ML evidence dashboard"></td>
<td><img src="assets/demo/multiscale-kinetics.svg" width="100%" alt="DFT to kinetics multiscale handoff"></td>
</tr>
</table>

Every demonstration is labelled `SYNTHETIC DEMO · NOT SCIENTIFIC DATA`. Visual tokens, anti-patterns and the pre-delivery checklist are recorded in [`docs/README_VISUAL_DESIGN_SYSTEM.md`](docs/README_VISUAL_DESIGN_SYSTEM.md). The compatibility command [`scripts/generate_readme_demos.py`](scripts/generate_readme_demos.py) is a strict read-only validator and never creates placeholder artwork.

## Support levels

| Level | Meaning |
|---|---|
| `L0_REFERENCE` | Scientific documentation and boundaries only |
| `L1_HANDOFF` | Structured manifest or downstream handoff |
| `L2_VALIDATED_ADAPTER` | Deterministic preflight/parser/validator with repository tests |
| `L3_EXECUTION_TESTED` | L2 plus immutable regression evidence from the real engine, version and environment |

Gaussian, VASP, Quantum ESPRESSO and CP2K currently expose selected-field **L2 adapters**. TsaoDFT does not claim L3 without legal real-engine regression evidence.

## Compute-efficiency architecture

- VASP, Quantum ESPRESSO and CP2K adapters retain read-only memory mapping; a full Gaussian streaming rewrite was not shipped because the measured gain was modest and the context-compatibility risk was higher.
- Provenance and structure files use chunked SHA-256. Large DFT datasets emit the historically identical canonical hash in bounded 256-row batches, while small datasets retain the one-shot fast path.
- The DFT-ML ridge baseline selects primal/dual from training shape and records finite-value checks, data shape and constant features; it does not add an expensive condition-number SVD to every fit.
- HPC manifests reject obvious OpenMP/BLAS thread oversubscription and optional per-node CPU overflow. Pending/rejected scripts stop with `exit 64` before the engine command.
- Homogeneous Slurm campaigns can use one array script and one JSONL task table with a `%` concurrency cap. The generator never submits jobs.
- Reproducible microbenchmarks, primary sources, rejected candidates and real-node boundaries are documented in [`docs/PERFORMANCE_AUDIT.md`](docs/PERFORMANCE_AUDIT.md) and [`docs/PERFORMANCE_GUIDE.md`](docs/PERFORMANCE_GUIDE.md).

In this revision's implementation benchmark, Python peak allocation for a 64 MiB file hash fell from about 64 MiB to 2 MiB; the canonical 50,000-row dataset hash fell from about 49.6 MiB to 0.51 MiB while preserving exactly the same SHA-256. These are repository-side Python/I/O measurements, not universal DFT-engine speedups.

## Installation

```bash
python scripts/install.py --list
python scripts/install.py --agent codex --scope user --skill all --dry-run --validate
python scripts/install.py --agent codex --scope user --skill all
```

## One-command quality gate

```bash
python -m pip install -r requirements-dev.txt
python scripts/quality_gate.py
```

```text
validate all versioned demo assets
→ catalog validation
→ minimal AI-cover integrity and provenance
→ curated README visual completeness
→ offline bilingual README local-link validation
→ Ruff lint
→ Ruff formatting check
→ strict repository audit
→ all non-empty unittest suites
```

For focused diagnostics:

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

## Scientific boundaries

The repository does not distribute Gaussian, VASP, Quantum ESPRESSO, CP2K, Multiwfn, VMD, POTCAR, pseudopotentials, or restricted basis/potential libraries, and it does not bypass licensing. Production calculations require a legally configured user environment.

Read next:

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- [`docs/ENGINE_SUPPORT_MATRIX.md`](docs/ENGINE_SUPPORT_MATRIX.md)
- [`docs/CAPABILITY_STATUS.yaml`](docs/CAPABILITY_STATUS.yaml)
- [`docs/SCIENTIFIC_BOUNDARIES.md`](docs/SCIENTIFIC_BOUNDARIES.md)
- [`docs/PERFORMANCE_GUIDE.md`](docs/PERFORMANCE_GUIDE.md)
- [`docs/PERFORMANCE_AUDIT.md`](docs/PERFORMANCE_AUDIT.md)
- [`docs/AI_IMAGE_GOVERNANCE.md`](docs/AI_IMAGE_GOVERNANCE.md)
- [`docs/TEST_REPORT.md`](docs/TEST_REPORT.md)

Repository policy: work directly on `main`; use Tags/Releases for publication snapshots rather than feature, fix or temporary branches.

# TsaoDFT Skill

<p align="center">
  <strong>A DFT-first, evidence-locked and auditable research operating system for molecular and periodic science</strong><br>
  From structure preparation, execution and technical validation to wavefunction analysis, machine learning, kinetics, multiscale handoff and publication-claim audit
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

> **AI image declaration | AI-GENERATED CONCEPTUAL ILLUSTRATION:** the dark overview below is an AI-assisted concept used only to communicate project identity, capability boundaries and workflow structure. Its molecules, lattices, servers, orbitals and charts are not results from Gaussian, VASP, Quantum ESPRESSO, CP2K, Multiwfn, VMD or experiment. Quantitative claims require accepted source files, calculation artifacts and reproducible scripts.

<p align="center">
  <img src="assets/ai/hero/tsao-dft-hero.svg" width="100%" alt="TsaoDFT dark scientific research operating system conceptual overview">
</p>

## Why TsaoDFT

`TsaoDFT_skill` is not a loose collection of prompts. It never silently promotes normal termination, an attractive plot or a high model score into a scientific conclusion. Work moves through an explicit evidence chain:

```text
planned
→ prepared
→ completed
→ technically validated
→ scientifically accepted
→ claim accepted
```

| Principle | TsaoDFT treatment |
|---|---|
| **Model identity stays explicit** | Structure, charge, spin, atom order, method fingerprint and reference state are recorded |
| **Results remain auditable** | Inputs, actual scripts, versions, outputs, hashes, restart lineage and failed attempts stay traceable |
| **Technical and scientific acceptance are separate** | Normal termination alone does not accept geometry, energy, frequency, electronic state or mechanism |
| **Claim strength follows evidence strength** | Figures, tables, explanations and manuscript claims retain source, scope and uncertainty |
| **Automation does not bypass approval** | Expensive execution, scheduler submission, method changes and destructive actions remain gated |

## Research operating system

<p align="center">
  <img src="assets/demo/workflow-architecture.svg" width="100%" alt="TsaoDFT auditable research loop synthetic demonstration">
</p>

Every state transition should answer four questions:

1. **Who owns acceptance?**
2. **Which artifact supports the decision?**
3. **Which method fingerprint and software environment were used?**
4. **Which assumptions and claim boundaries remain unresolved?**

## Eight composable Skills

| Skill | Purpose | Scientific boundary |
|---|---|---|
| [`tsao-dft-suite`](skills/tsao-dft-suite/) | DFT-first entry point, task DAG, cross-Skill routing, cost and approval gates | Coordinates work; it does not replace engine-level scientific judgement |
| [`tsao-structure-prep`](skills/tsao-structure-prep/) | Molecules, conformers, crystals, surfaces, defects, adsorption candidates and atom mapping | Never silently chooses charge, spin, oxidation state, termination or protonation |
| [`tsao-dft-researcher`](skills/tsao-dft-researcher/) | Gaussian molecular DFT/TDDFT, Opt/Freq, TS/IRC, thermochemistry, NMR, Multiwfn and VMD | Real executables and licences remain external; adapters do not fabricate execution |
| [`tsao-periodic-dft-materials`](skills/tsao-periodic-dft-materials/) | VASP, Quantum ESPRESSO and CP2K, including surfaces, defects, bands/DOS, NEB and convergence | Does not distribute POTCAR, pseudopotentials or restricted databases; incompatible energies cannot be mixed |
| [`tsao-dft-hpc-provenance`](skills/tsao-dft-hpc-provenance/) | Local/Slurm/PBS execution, estimates, arrays, checkpoints, restart lineage and hashes | Scheduler success only means the process ended |
| [`tsao-dft-ml-active-learning`](skills/tsao-dft-ml-active-learning/) | DFT-label audit, leakage prevention, applicability domain, uncertainty, active learning and inverse design | High R², SHAP or acquisition score does not prove mechanism, causality or synthesizability |
| [`tsao-dft-kinetics-multiscale`](skills/tsao-dft-kinetics-multiscale/) | Eyring/TST, networks, detailed balance, uncertainty, microkinetics and reactor handoff | Consumes only thermochemistry with explicit standard and reference states |
| [`tsao-dft-catalysis-profile`](skills/tsao-dft-catalysis-profile/) | DCS/MCSOMe/DMOS, Si–O/Si–C, Ti/TEA, Ziegler–Natta and polyolefin catalysis | A scoped profile that is never auto-applied to unrelated catalysis |

## Support levels

| Level | Meaning |
|---|---|
| `L0_REFERENCE` | Scientific documentation and boundaries only |
| `L1_HANDOFF` | Structured manifest or downstream handoff |
| `L2_VALIDATED_ADAPTER` | Deterministic preflight/parser/validator plus repository tests |
| `L3_EXECUTION_TESTED` | L2 plus immutable regression evidence from the real engine, version and site |

Gaussian, VASP, Quantum ESPRESSO and CP2K currently expose selected-field **L2 adapters**. TsaoDFT does not claim L3 without legal real-engine regression evidence.

## Selected scientific demonstrations

The following figures are generated from fixed synthetic data and repository scripts. Every asset is labelled `SYNTHETIC DEMO · NOT SCIENTIFIC DATA`. They demonstrate figure contracts, evidence gates and result organisation, not production results.

<table>
<tr>
<td width="50%"><img src="assets/demo/wavefunction-esp-gallery.svg" width="100%" alt="Wavefunction and ESP figure contract"></td>
<td width="50%"><img src="assets/demo/periodic-dft-materials.svg" width="100%" alt="Periodic DFT evidence chain"></td>
</tr>
<tr>
<td><img src="assets/demo/dft-ml-dashboard.svg" width="100%" alt="DFT ML provenance-aware dashboard"></td>
<td><img src="assets/demo/multiscale-kinetics.svg" width="100%" alt="DFT to kinetics multiscale handoff"></td>
</tr>
</table>

Additional deterministic assets:

- [`free-energy-profile.svg`](assets/demo/free-energy-profile.svg): free energy, TS, IRC and standard-state acceptance;
- [`active-learning-loop.svg`](assets/demo/active-learning-loop.svg): objectives, constraints, batch selection and stop criteria;
- [`hpc-provenance.svg`](assets/demo/hpc-provenance.svg): HPC execution, checkpoints, parsing and immutable lineage;
- [`workflow-architecture.svg`](assets/demo/workflow-architecture.svg): the cross-stage evidence ledger.

The full visual system, palette, typography, density, anti-patterns and accessibility checklist are documented in [`docs/README_VISUAL_DESIGN_SYSTEM.md`](docs/README_VISUAL_DESIGN_SYSTEM.md).

## Compute-efficiency architecture

Implemented and tested optimisations include:

| Hotspot | Current implementation | Boundary |
|---|---|---|
| Large VASP / QE / CP2K outputs | Read-only `mmap`, byte regexes and last-value aggregation instead of repeated full decoding | Scientific fields and acceptance rules remain unchanged |
| DFT-ML Ridge | Automatic primal/dual selection by training shape; stable least squares for `alpha = 0` | A baseline model is not presented as mechanistic evidence |
| File and dataset hashing | Chunked SHA-256 and bounded canonical encoding | Cache identity cannot survive content or method-fingerprint changes |
| Homogeneous HPC campaigns | Slurm Job Array, JSONL task table and concurrency cap | The generator never submits real jobs |
| Thread and resource layout | Explicit OpenMP, BLAS, MPI and node-capacity checks | Resources and walltime are never increased silently |

Read next:

- [`docs/PERFORMANCE_AUDIT.md`](docs/PERFORMANCE_AUDIT.md)
- [`docs/PERFORMANCE_GUIDE.md`](docs/PERFORMANCE_GUIDE.md)

## Quick start

List installable Skills:

```bash
python scripts/install.py --list
```

Validate a user-scoped Codex installation without writing:

```bash
python scripts/install.py \
  --agent codex \
  --scope user \
  --skill all \
  --dry-run \
  --validate
```

Install all Skills:

```bash
python scripts/install.py \
  --agent codex \
  --scope user \
  --skill all
```

Production execution still requires legally configured engines, licences, pseudopotentials or basis libraries, a site guide and user authorisation.

## One-command quality gate

```bash
python -m pip install -r requirements-dev.txt
python scripts/quality_gate.py
```

Gate order:

```text
validate all versioned demo assets
→ catalog validation
→ governed AI-cover integrity and provenance
→ bilingual README visual completeness
→ offline README local-link validation
→ Ruff lint
→ Ruff formatting check
→ strict repository audit
→ all non-empty unittest suites
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

## Scientific boundaries

This repository:

- does not distribute Gaussian, VASP, Quantum ESPRESSO, CP2K, Multiwfn, VMD, POTCAR, pseudopotentials or restricted basis/potential libraries;
- does not bypass licences, site policy or software access controls;
- never describes conceptual AI imagery as an orbital, ESP, band structure, free-energy profile, transition state, mechanism or experiment;
- never equates normal termination, scheduler completion, model score or attractive graphics with scientific acceptance;
- never claims `L3_EXECUTION_TESTED` without immutable real-engine evidence.

## Documentation map

| Document | Purpose |
|---|---|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Architecture and state flow |
| [`docs/ENGINE_SUPPORT_MATRIX.md`](docs/ENGINE_SUPPORT_MATRIX.md) | Engine coverage and support levels |
| [`docs/CAPABILITY_STATUS.yaml`](docs/CAPABILITY_STATUS.yaml) | Machine-readable capability status |
| [`docs/SCIENTIFIC_BOUNDARIES.md`](docs/SCIENTIFIC_BOUNDARIES.md) | Scientific boundaries and non-claims |
| [`docs/CROSS_SKILL_HANDOFF.md`](docs/CROSS_SKILL_HANDOFF.md) | Cross-Skill handoff contract |
| [`docs/AI_IMAGE_GOVERNANCE.md`](docs/AI_IMAGE_GOVERNANCE.md) | AI-image governance |
| [`docs/README_VISUAL_DESIGN_SYSTEM.md`](docs/README_VISUAL_DESIGN_SYSTEM.md) | Dark scientific README design system |
| [`docs/TEST_REPORT.md`](docs/TEST_REPORT.md) | Test, visual and engineering gates |

Repository policy: work directly on `main`; use Tags/Releases for publication snapshots rather than long-lived feature, fix or temporary branches.

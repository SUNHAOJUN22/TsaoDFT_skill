# TsaoDFT Skill

[![CI](https://github.com/SUNHAOJUN22/TsaoDFT_skill/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/SUNHAOJUN22/TsaoDFT_skill/actions/workflows/ci.yml) ![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.12%20%7C%203.13-3776AB) ![License](https://img.shields.io/badge/license-MIT-green)

**Structure review → molecular/periodic DFT → technical validation → wavefunction/material properties → HPC provenance → ML/kinetics → evidence and figures**

<p align="center"><img src="assets/ai/hero/tsao-dft-hero.svg" alt="TsaoDFT AI-generated conceptual hero" width="100%"></p>

> **AI image declaration:** the hero and module scenes are AI-generated or AI-assisted conceptual illustrations. They are not molecular structures, orbitals, electrostatic potentials, band structures, free-energy profiles, mechanisms, or experimental results. Quantitative claims must come from validated calculations or deterministic source-data figures.

TsaoDFT is a DFT-centred Agent Skills suite. It distinguishes documentation, machine-readable handoff, deterministic adapters, and real-engine regression instead of treating every software mention as equal support.

![TsaoDFT workflow](assets/demo/workflow-architecture.svg)

## AI-generated research-scene gallery

The governed concept visuals cover molecular DFT, periodic DFT, DFT-labelled machine learning, kinetics, HPC provenance, catalysis, and the full ecosystem. Paths, generation provenance, hashes, allowed uses, and forbidden uses are recorded in [`assets/ai/manifest.yaml`](assets/ai/manifest.yaml).

<table>
<tr>
<td width="50%" align="center"><img src="assets/ai/modules/molecular-dft.svg" alt="AI molecular DFT concept" width="100%"><br><strong>Molecular DFT</strong></td>
<td width="50%" align="center"><img src="assets/ai/modules/periodic-dft.svg" alt="AI periodic DFT concept" width="100%"><br><strong>Periodic DFT</strong></td>
</tr>
<tr>
<td align="center"><img src="assets/ai/modules/dft-ml.svg" alt="AI DFT ML concept" width="100%"><br><strong>DFT + ML</strong></td>
<td align="center"><img src="assets/ai/modules/dft-kinetics.svg" alt="AI DFT kinetics concept" width="100%"><br><strong>DFT to kinetics</strong></td>
</tr>
<tr>
<td align="center"><img src="assets/ai/modules/hpc-provenance.svg" alt="AI HPC provenance concept" width="100%"><br><strong>HPC provenance</strong></td>
<td align="center"><img src="assets/ai/modules/catalysis.svg" alt="AI catalysis concept" width="100%"><br><strong>Catalysis profile</strong></td>
</tr>
<tr>
<td colspan="2" align="center"><img src="assets/ai/modules/ecosystem.svg" alt="AI TsaoDFT ecosystem concept" width="76%"><br><strong>DFT evidence ecosystem</strong></td>
</tr>
</table>

## Skills

| Skill | Purpose |
|---|---|
| `tsao-dft-suite` | DFT-first root orchestration, support-level routing, handoffs, cost and approval gates |
| `tsao-structure-prep` | molecular/periodic candidate structures, XYZ audit and atom mapping |
| `tsao-dft-researcher` | Gaussian molecular DFT/TDDFT, TS/IRC, thermochemistry, Multiwfn, VMD and evidence QA |
| `tsao-periodic-dft-materials` | VASP/QE/CP2K input preflight, output evidence, convergence and periodic-property contracts |
| `tsao-dft-hpc-provenance` | local/Slurm/PBS scripts, site profiles, resource estimates, provenance and restart lineage |
| `tsao-dft-ml-active-learning` | DFT-label leakage/fidelity audit, grouped baseline, model cards and active learning |
| `tsao-dft-kinetics-multiscale` | Eyring/TST, balance, thermodynamic closure, uncertainty and downstream handoff |
| `tsao-dft-catalysis-profile` | scoped DCS/MCSOMe/DMOS, Si–O/Si–C, Ti/TEA and polyolefin-catalysis profile |

## Support levels

- `L0_REFERENCE`: scientific documentation only.
- `L1_HANDOFF`: structured manifest or downstream handoff.
- `L2_VALIDATED_ADAPTER`: deterministic preflight/parser/validator with repository tests.
- `L3_EXECUTION_TESTED`: L2 plus recorded regression on the real engine/version/environment.

Gaussian, VASP, Quantum ESPRESSO and CP2K currently provide selected-field L2 adapters. The repository does not claim L3 without legal, immutable real-engine regression evidence.

## Deterministic scientific demonstrations

![Wavefunction and ESP](assets/demo/wavefunction-esp-gallery.svg)

![Periodic DFT](assets/demo/periodic-dft-materials.svg)

![Active learning](assets/demo/active-learning-loop.svg)

![HPC provenance](assets/demo/hpc-provenance.svg)

![Multiscale kinetics](assets/demo/multiscale-kinetics.svg)

These are generated from synthetic source data and are not production computational results.

## Installation

```bash
python scripts/install.py --list
python scripts/install.py --agent codex --scope user --skill all --dry-run --validate
python scripts/install.py --agent codex --scope user --skill all
```

## Validation

```bash
python -m pip install -r requirements.txt
python scripts/generate_readme_demos.py
python scripts/validate_catalog.py
python scripts/validate_ai_assets.py
python scripts/validate_readme_visuals.py --strict
python scripts/validate_repo.py --strict
python scripts/run_all_tests.py
```

The CI matrix runs on Python 3.10, 3.12 and 3.13 for every push to `main`. The main-only attestation workflow updates [`docs/CI_VERIFIED.md`](docs/CI_VERIFIED.md) only after all GitHub-hosted checks pass.

Repository policy: work directly on `main`; do not create feature, fix, or release branches. Tags and Releases are used for publication snapshots.

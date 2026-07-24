# TsaoDFT Skill

**Structure review → molecular/periodic DFT → technical validation → wavefunction/material properties → HPC provenance → ML/kinetics → evidence and figures**

TsaoDFT is a DFT-centred Agent Skills suite. It distinguishes documentation, machine-readable handoff, deterministic adapters, and real-engine regression instead of treating every software mention as equal support.

![TsaoDFT workflow](assets/demo/workflow-architecture.svg)

> Every README figure is deterministically generated from synthetic data and visibly labelled `SYNTHETIC DEMO · NOT SCIENTIFIC DATA`.

## Skills

| Skill | Purpose |
|---|---|
| `tsao-dft-suite` | DFT-first root orchestration, support-level routing, handoffs, cost and approval gates |
| `tsao-structure-prep` | molecular/periodic candidate structures, XYZ audit and atom mapping |
| `tsao-dft-researcher` | Gaussian molecular DFT/TDDFT, TS/IRC, thermochemistry, Multiwfn, VMD and evidence QA |
| `tsao-periodic-dft-materials` | VASP/QE/CP2K input preflight, output evidence, convergence and periodic-property contracts |
| `tsao-dft-hpc-provenance` | local/Slurm/PBS scripts, site profiles, resource estimates, provenance and restart lineage |
| `tsao-dft-ml-active-learning` | DFT-label leakage/fidelity audit, grouped baseline, model cards and active learning |
| `tsao-dft-kinetics-multiscale` | TST/Eyring, network balance, detailed balance, uncertainty and external kinetics handoffs |
| `tsao-dft-catalysis-profile` | scoped DCS/MCSOMe/DMOS, Ti/TEA, Ziegler–Natta and polyolefin-catalysis profile |

## Support levels

- `L0_REFERENCE`: documentation only;
- `L1_HANDOFF`: structured handoff;
- `L2_VALIDATED_ADAPTER`: deterministic parser/preflight/validator with repository tests;
- `L3_EXECUTION_TESTED`: L2 plus immutable regression on a real engine/version/site.

Gaussian, VASP, Quantum ESPRESSO and CP2K are L2 for selected fields in this release. No L3 claim is made by the current delivery environment. See [ENGINE_SUPPORT_MATRIX](docs/ENGINE_SUPPORT_MATRIX.md) and [CAPABILITY_STATUS](docs/CAPABILITY_STATUS.yaml).

## DFT validation ladder

```text
planned -> prepared -> preflight passed -> program completed
-> technically validated -> scientifically accepted -> claim accepted
```

Scheduler completion, Gaussian `Normal termination`, VASP timing output, QE `JOB DONE`, and CP2K `PROGRAM ENDED AT` establish program completion only.

## Installation

```bash
python scripts/install.py --list
python scripts/install.py --agent codex --scope user --skill all --dry-run --validate
python scripts/install.py --agent codex --scope user --skill all
```

## Example

```text
Use $tsao-dft-suite.
Build a DFT-first task graph for molecular and periodic reaction paths. Define structure campaigns, method fingerprints, convergence plans, handoffs, resource estimates, and acceptance gates. Stop before submission.
```

## Validation

```bash
python -m pip install -r requirements.txt
python scripts/generate_readme_demos.py
python scripts/validate_catalog.py
python scripts/validate_repo.py --strict
python scripts/run_all_tests.py
```

Repository policy: work directly on `main`; do not create feature, repair, or release branches. Runtime state belongs in `.research/`; releases use tags.

Scientific engines, licensed data and external libraries are not distributed. The current environment tested scripts, manifests and synthetic fixtures, not licensed production calculations. Human scientific acceptance remains mandatory.

# TsaoDFT Skill

TsaoDFT consolidates the computational-chemistry and DFT entries found in the uploaded AI-for-Science Skill catalog into seven bounded, composable and testable Agent Skills. The repository is maintained on `main` only.

![Workflow](assets/demo/workflow-architecture.svg)

All README figures are deterministic synthetic demonstrations, visibly labeled as non-scientific data.

## Skills

- `tsao-dft-researcher`: universal molecular DFT entry point; deepest Gaussian/Multiwfn/VMD adapter.
- `tsao-structure-prep`: molecular and periodic model campaigns with provenance and model-review gates.
- `tsao-periodic-dft-materials`: VASP/QE/CP2K periodic DFT handoffs, convergence, electronic properties, surfaces, defects, NEB, phonons and high throughput.
- `tsao-dft-ml-active-learning`: leakage-aware DFT ML, uncertainty, applicability domain, active learning and inverse design.
- `tsao-dft-hpc-provenance`: local/Slurm/PBS execution plans, monitoring, recovery, provenance and scientific CI.
- `tsao-dft-kinetics-multiscale`: TST rates, reaction networks, microkinetics and DFT-to-reactor handoffs.
- `tsao-dft-catalysis-profile`: optional DCS/MCSOMe/DMOS, Ti/TEA, Ziegler-Natta and polyolefin-catalysis profile.

Catalog traceability is documented in [`docs/DFT_SKILL_CATALOG_MAPPING.md`](docs/DFT_SKILL_CATALOG_MAPPING.md).

```bash
python scripts/install.py --list
python scripts/install.py --agent codex --scope user --skill all --dry-run --validate
python scripts/install.py --agent codex --scope user --skill all
python scripts/validate_catalog.py
python scripts/validate_repo.py --strict
python scripts/run_all_tests.py
```

![Periodic DFT](assets/demo/periodic-dft-materials.svg)
![Active learning](assets/demo/active-learning-loop.svg)
![HPC provenance](assets/demo/hpc-provenance.svg)
![Multiscale kinetics](assets/demo/multiscale-kinetics.svg)

Licensed engines, pseudopotentials, manuals and external scientific libraries are not distributed. A successful program termination or rendered figure is not scientific acceptance.

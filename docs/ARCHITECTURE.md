# Architecture

## Seven-Skill design

```text
tsao-dft-researcher (entry and molecular DFT evidence controller)
├── tsao-structure-prep
├── tsao-periodic-dft-materials
├── tsao-dft-ml-active-learning
├── tsao-dft-hpc-provenance
├── tsao-dft-kinetics-multiscale
└── tsao-dft-catalysis-profile (optional, scoped)
```

Every handoff carries structure/artifact IDs, hashes, validation state, method fingerprint, units, unresolved assumptions and requested downstream observable.

## Support levels

1. **Deep adapter** — local input/parser/validation scripts exist (Gaussian/Multiwfn/VMD path).
2. **Validated handoff** — structured manifests, templates and semantic checks exist (VASP/QE/CP2K, HPC, kinetics).
3. **Optional external backend** — library is used when installed (RDKit, DeepChem, AiiDA, atomate2, Cantera, RMG, Pyomo, MDAnalysis).
4. **Profile** — domain assumptions load only on explicit activation.

## Validation ladder

`files exist → program completed → technically validated → scientifically accepted`.

Operational `.research/` state remains separate from release-layer research and figure manifests. Accepted claims consume accepted artifacts by default.

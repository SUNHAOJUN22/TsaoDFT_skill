# DFT Engine and Capability Support Matrix

Support levels are evidence labels, not marketing labels:

- **L0_REFERENCE** — scientific documentation only;
- **L1_HANDOFF** — structured manifest or downstream handoff;
- **L2_VALIDATED_ADAPTER** — deterministic preflight/parser/validator with repository tests;
- **L3_EXECUTION_TESTED** — L2 plus recorded regression on the real engine/version and execution environment.

| Engine/capability | Level in v0.4 | Deterministic implementation | Important limitation |
|---|---|---|---|
| Gaussian molecular DFT | L2 | input preflight, rich log parser, TS/IRC/thermochemistry/evidence validators | no licensed-engine regression in this delivery environment |
| Multiwfn | L1–L2 | semantic recipe validation, provenance/isovalue/fragment checks | menu execution and numerical regression require a real versioned installation |
| VMD/Tachyon | L2 for script generation | Tcl generation and figure-manifest validation | no real cube rendering regression here |
| VASP | L2 selected fields | INCAR/POSCAR/KPOINTS/POTCAR-TITEL preflight and OUTCAR parser | parser is intentionally partial; POTCAR is never distributed |
| Quantum ESPRESSO pw.x | L2 selected fields | namelist/card preflight and output parser | pseudopotentials remain external; advanced modules are not parsed |
| CP2K Quickstep | L2 selected fields | basis/potential/grid/KIND/PBC preflight and output parser | advanced properties and version-specific syntax remain external |
| ORCA / Psi4 | L0–L1 | method-routing references and handoff only | no deterministic engine adapter yet |
| Structure preparation | L2 for XYZ/manifests | geometry red flags, hashing, atom-order mapping, campaign expansion | no silent bond-order, charge, spin, oxidation-state or surface choice |
| DFT-labelled ML | L2 core validation/baseline | leakage/fidelity validation, grouped splitting, NumPy ridge baseline, model card, active-learning batch | DeepChem/GNN execution remains optional external backend |
| Slurm/PBS/local execution | L2 script/manifest; L1 site execution | engine-aware scripts, resource estimate, site/restart/provenance validators | no site is L3 until real scheduler regression is recorded |
| TST/Eyring and network validation | L2 | rates, balance, detailed-balance closure, uncertainty propagation | microkinetic/reactor results require downstream model validation |
| Cantera/RMG/Pyomo/CatMAP | L1 | provenance-rich handoff | export is not automatically a runnable validated mechanism |

A user or lab may promote a capability to L3 only by adding immutable regression artifacts, engine/version records, expected-value tolerances, and site information without credentials or licensed files.

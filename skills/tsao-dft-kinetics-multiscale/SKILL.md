---
name: tsao-dft-kinetics-multiscale
description: "Convert validated DFT thermochemistry into transition-state-theory rates, reaction networks, microkinetic and multiscale handoffs for Cantera, RMG-Py, Pyomo/CatMAP and downstream reactor or population-balance models."
license: MIT
compatibility: Python 3.10+. Cantera, RMG-Py, Pyomo, CatMAP and reactor/population-balance software are optional external backends.
metadata: {"version": "0.3.0-alpha.1", "author": "SUNHAOJUN22", "repository": "https://github.com/SUNHAOJUN22/TsaoDFT_skill"}
---

# Tsao DFT Kinetics and Multiscale

This Skill bridges quantum chemistry to kinetic models without pretending that an electronic-energy diagram is already a reactor model.

## Workflow

1. Import only accepted species/TS thermochemistry with explicit temperature, phase, standard state, reference state and method fingerprint.
2. Define species identities, site balance, stoichiometry, reaction direction, degeneracy and mechanism family.
3. Convert barriers to rate constants with declared TST/Eyring, tunneling and standard-state conventions.
4. Check detailed balance and thermodynamic consistency before fitting or simulation.
5. Build microkinetic, Cantera/RMG or Pyomo/CatMAP handoff tables with provenance to every DFT term.
6. Separate sensitivity/RDS metrics from causal statements. RDS, TDTS/TDI and degree-of-rate-control are model- and condition-dependent.
7. For polymerization/reactor coupling, declare chain-state representation, population-balance assumptions and fitted versus DFT-derived parameters.

## Routes

| Need | Route |
|---|---|
| Eyring/TST rates | `tst` |
| Reaction network and thermodynamic consistency | `network` |
| Microkinetic/CatMAP/Cantera/Pyomo handoff | `microkinetics` |
| BEP, volcano and descriptor analysis | `descriptors` |
| DFT → MD/kinetics/reactor/population balance | `multiscale` |

## Hard Guardrails

- Electronic energy, enthalpy and Gibbs free energy are different inputs.
- Gas 1 atm, solution 1 M and surface/site standard states are not interchangeable.
- Bimolecular and unimolecular rate constants have different units and concentration conventions.
- Barrier reference must specify separated reactants versus precomplex.
- Detailed balance violations block an accepted reversible network.
- A lowest DFT barrier is not automatically the experimental RDS under coverage, transport or pre-equilibrium effects.
- Fitted kinetic parameters remain distinguished from first-principles values.


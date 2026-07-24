---
name: tsao-dft-catalysis-profile
description: Optional domain profile for applying TsaoDFT to DCS/MCSOMe/DMOS substituent effects, Si-O/Si-C motifs, Ti/TEA coordination, Ziegler-Natta and polyolefin-catalysis mechanism questions, including coordination competition, catalyst poisoning hypotheses, open-shell Ti complexes, and project-specific figure matrices. Use only when the molecular system and research question fall inside this chemistry scope; otherwise use tsao-dft-researcher alone.
license: MIT
compatibility: Requires the tsao-dft-researcher skill. Gaussian/Multiwfn/VMD remain external tools.
metadata: {"version": "0.4.0-alpha.1", "author": "SUNHAOJUN22", "scope": "polyolefin-catalysis-profile"}
---

# TsaoDFT Catalysis Profile

This is a **domain profile**, not a universal DFT method selector. Load it only for work involving one or more of:

- DCS, MCSOMe, DMOS, or closely related Si-O/Si-C substituted monomers;
- Ti coordination complexes, Ti/TEA interactions, or open-shell Ti states;
- Ziegler-Natta/polyolefin catalyst coordination, poisoning, inhibition, or selectivity hypotheses;
- pi-versus-O coordination competition and associated thermodynamic/electronic evidence;
- project figure sets derived from the approved DCS/MCSOMe/DMOS reference-image family.

For unrelated organic reactions, photochemistry, medicinal chemistry, electrochemistry, or generic molecular property calculations, do **not** load this profile.

## Required Upstream Skill

Run `tsao-dft-researcher` as the lifecycle controller. This profile contributes domain-specific model checks, hypothesis boundaries, and figure routing. It does not replace Gaussian validation, Multiwfn provenance, or evidence manifests.

## Domain Guardrails

1. Do not infer catalyst poisoning from isolated-monomer HOMO/LUMO or ESP alone.
2. Compare balanced coordination or reaction cycles, not absolute energies of different stoichiometries.
3. Enumerate relevant monomer conformers and plausible coordination modes before ranking.
4. For Ti/open-shell structures, record multiplicity, S^2, stability, spin density, and alpha/beta frontier orbitals.
5. Distinguish TEA association, ligand exchange, monomer coordination, insertion, and irreversible deactivation.
6. Treat NBO, QTAIM, IRI/IGMH/NCI, ESP, and orbital plots as complementary evidence; none is a standalone poisoning metric.
7. Use explicit solvent or cluster models when specific coordination or ion pairing controls the result.
8. If method sensitivity changes the ordering, report the candidates as unresolved.

## Workflow

```text
system identity and composition
-> conformer/coordination-mode matrix
-> accepted minima and reference states
-> balanced thermochemistry and method sensitivity
-> open-shell/electronic-structure validation
-> interaction evidence
-> claim boundary and project-specific figures
```

Read `manifest.yaml` and only the needed references. The full 39-structure galleries, when applicable, belong in SI; the main text should contain only claim-bearing representative comparisons.

## DFT campaign and claim-depth controls

`build_coordination_campaign.py` expands substrate/additive × catalyst model × coordination mode × conformer × charge × multiplicity. `validate_claim_scope.py` prevents isolated-molecule DFT from being promoted beyond the available coordination, pathway, kinetic, experimental and process evidence.

# TsaoDFT Skill

<p align="center">
  <strong>A DFT-first, evidence-locked and auditable research operating system for molecular and periodic science</strong><br>
  From structure preparation and real-engine execution to wavefunctions, materials properties, machine learning, kinetics, GPU/HPC acceleration provenance and publication-claim audit
</p>

<p align="center">
  <a href="README.md">中文</a> · <a href="README_EN.md">English</a>
</p>

<p align="center">
  <a href="https://github.com/SUNHAOJUN22/TsaoDFT_skill/actions/workflows/ci.yml"><img src="https://github.com/SUNHAOJUN22/TsaoDFT_skill/actions/workflows/ci.yml/badge.svg?branch=main" alt="CI"></a>
  <img src="https://img.shields.io/badge/Python-3.10%20%7C%203.12%20%7C%203.13-3776AB" alt="Python 3.10, 3.12 and 3.13">
  <img src="https://img.shields.io/badge/tests-177%20passing-16A34A" alt="177 tests passing">
  <img src="https://img.shields.io/badge/support-L0%E2%80%93L3-6D5DFB" alt="Support levels L0 to L3">
  <img src="https://img.shields.io/badge/license-MIT-16A34A" alt="MIT license">
</p>

> **AI image declaration | AI-GENERATED CONCEPTUAL ILLUSTRATION:** the overview below was generated with the UI/UX Pro Max Hero-Centric + Evidence Bento workflow. Its molecules, lattice, orbital-like forms, servers and data interfaces communicate research context only; they are not outputs from Gaussian, VASP, Quantum ESPRESSO, CP2K, Multiwfn, VMD or experiment. Quantitative claims still require accepted source files, calculation artifacts and reproducible scripts.

<p align="center">
  <img src="assets/ai/hero/tsao-dft-hero.svg" width="100%" alt="TsaoDFT evidence-first DFT research operating system conceptual overview">
</p>

## TsaoDFT in 30 seconds

<table>
<tr>
<td width="25%" valign="top"><strong>DFT-first</strong><br><sub>A question is grounded in structure, method fingerprint, reference state and acceptance criteria before execution.</sub></td>
<td width="25%" valign="top"><strong>Evidence graph</strong><br><sub>Calculations, artifacts, figures and manuscript claims receive explicit support edges; failed attempts remain visible.</sub></td>
<td width="25%" valign="top"><strong>Multi-engine</strong><br><sub>Molecular work covers Gaussian / Multiwfn / VMD; periodic work covers VASP / QE / CP2K.</sub></td>
<td width="25%" valign="top"><strong>Scale with provenance</strong><br><sub>CPU/GPU, CUDA-X, ML, kinetics and HPC may consume accepted evidence but never bypass scientific boundaries.</sub></td>
</tr>
</table>

`TsaoDFT_skill` is not a loose prompt collection. It never promotes normal termination, an attractive plot or a high model score directly into a scientific conclusion. Work moves through an explicit state chain:

```text
planned
→ prepared
→ completed
→ technically validated
→ scientifically accepted
→ claim accepted
```

## From scientific question to defensible claim

<p align="center">
  <img src="assets/demo/workflow-architecture.svg" width="100%" alt="TsaoDFT auditable research loop synthetic demonstration">
</p>

Every state transition must answer:

1. **Who owns acceptance?**
2. **Which artifact supports the decision?**
3. **Which method fingerprint, software version and execution environment were used?**
4. **Which assumptions, uncertainties and claim boundaries remain open?**

## Eight Skills, one evidence chain

| Skill | Best used for | Boundary that must not be crossed |
|---|---|---|
| [`tsao-dft-suite`](skills/tsao-dft-suite/) | DFT-first entry point, task DAG, cross-Skill routing, cost and approval gates | Coordinates work; does not replace engine-level scientific judgement |
| [`tsao-structure-prep`](skills/tsao-structure-prep/) | Molecules, conformers, crystals, surfaces, defects, adsorption candidates and atom mapping | Never silently chooses charge, spin, oxidation state, termination or protonation |
| [`tsao-dft-researcher`](skills/tsao-dft-researcher/) | Gaussian molecular DFT/TDDFT, Opt/Freq, TS/IRC, thermochemistry, NMR, Multiwfn and VMD | Real executables, licences and environments remain external; adapters never fabricate execution |
| [`tsao-periodic-dft-materials`](skills/tsao-periodic-dft-materials/) | VASP, Quantum ESPRESSO and CP2K, including surfaces/defects, bands/DOS, NEB and convergence | Does not distribute POTCAR, pseudopotentials or restricted databases; incompatible energies cannot be mixed |
| [`tsao-dft-ml-active-learning`](skills/tsao-dft-ml-active-learning/) | DFT-label audit, leakage prevention, applicability domain, uncertainty, active learning and inverse design | High R², SHAP or acquisition score does not prove mechanism, causality or synthesizability |
| [`tsao-dft-kinetics-multiscale`](skills/tsao-dft-kinetics-multiscale/) | Eyring/TST, reaction networks, detailed balance, uncertainty, microkinetics and reactor handoff | Consumes only data with explicit and accepted standard/reference states |
| [`tsao-dft-hpc-provenance`](skills/tsao-dft-hpc-provenance/) | Local/Slurm/PBS execution, GPU planning/binding, candidate generation, real-result import, numerical equivalence, evidence bundles and scoped L3 qualification | GPU allocation, a fastest single run, a self-reported L3 label or scheduler completion proves neither speedup nor scientific acceptance |
| [`tsao-dft-catalysis-profile`](skills/tsao-dft-catalysis-profile/) | DCS/MCSOMe/DMOS, Si–O/Si–C, Ti/TEA, Ziegler–Natta and polyolefin catalysis | Scoped profile; never auto-applied to unrelated catalysis |

## Scientific figures: conceptual identity and deterministic evidence stay separate

The four figures below are generated from fixed synthetic data and repository scripts. Every asset is labelled `SYNTHETIC DEMO · NOT SCIENTIFIC DATA`. They demonstrate figure contracts, acceptance gates and evidence organisation—not production results.

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

The visual system follows UI/UX Pro Max product classification, Pattern, Style, Colors, Typography, Density, Anti-pattern and Accessibility stages. See [`docs/README_VISUAL_DESIGN_SYSTEM.md`](docs/README_VISUAL_DESIGN_SYSTEM.md). AI governance is recorded in [`docs/AI_IMAGE_GOVERNANCE.md`](docs/AI_IMAGE_GOVERNANCE.md).

## Support levels

| Level | Meaning | Reporting boundary |
|---|---|---|
| `L0_REFERENCE` | Method, boundary and reference material only | Method reference only |
| `L1_HANDOFF` | Structured manifest or downstream handoff | Requires downstream validation |
| `L2_VALIDATED_ADAPTER` | Deterministic preflight/parser/validator plus repository tests | May report adapter validation, not real-engine regression |
| `L3_EXECUTION_TESTED` | L2 plus immutable evidence from the real engine, version and site | May report real execution only within the documented scope |

Gaussian, VASP, Quantum ESPRESSO and CP2K currently expose selected-field **L2 adapters**. TsaoDFT does not claim L3 without legal real-engine regression evidence. The machine-readable claim boundary is in [`docs/SCIENTIFIC_CLAIM_POLICY.yaml`](docs/SCIENTIFIC_CLAIM_POLICY.yaml).

## Quick start

List installable Skills:

```bash
python scripts/install.py --list
```

Validate without writing:

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

## GPU, parallel and edge acceleration entry point

First generate the compatibility and library-applicability plan:

```bash
python skills/tsao-dft-hpc-provenance/scripts/plan_acceleration.py \
  skills/tsao-dft-hpc-provenance/templates/acceleration-profile.yaml \
  --out acceleration-plan.json
```

Then materialize a matching VASP base Manifest and acceleration Profile into approval-gated benchmark candidates:

```bash
python skills/tsao-dft-hpc-provenance/scripts/materialize_acceleration_campaign.py \
  skills/tsao-dft-hpc-provenance/templates/vasp-gpu-hpc-manifest.yaml \
  skills/tsao-dft-hpc-provenance/templates/acceleration-profile.yaml \
  --manifest-out build/vasp-h100.yaml \
  --matrix-out build/benchmark-matrix.csv \
  --candidate-dir build/candidates \
  --plan-out build/acceleration-plan.json
```

The materializer creates an FP64 CPU scientific reference, 1/2/4-GPU candidates, a CSV benchmark matrix and one YAML Manifest per candidate. Every candidate is forced to `approval: pending`; the tool writes files and never submits a job. Generated Slurm steps may use explicit `srun` CPU/GPU binding and record rank, visible devices, GPU UUID, PCI bus, driver, build fingerprint and benchmark-plan identity, but those records are still not measured speedup evidence.

After real runs finish, import and qualify the evidence:

```bash
python skills/tsao-dft-hpc-provenance/scripts/import_benchmark_evidence.py \
  results/* --artifact-root run-artifacts --out build/evidence.jsonl

python skills/tsao-dft-hpc-provenance/scripts/qualify_performance_evidence.py \
  build/evidence.jsonl \
  --policy skills/tsao-dft-hpc-provenance/templates/performance-qualification-policy.yaml \
  --artifact-root run-artifacts --review approved-review.yaml \
  --out-dir build/performance-evidence
```

Import supports JSON, YAML, JSONL and dotted-field CSV. Effective speedup is calculated only after input hash, method fingerprint, model, convergence, parser, energy, force, stress and property tolerances pass. Formal statistics use the median of at least three successful repeats and retain failed attempts. `QUALIFIED_FOR_SCOPED_L3_PERFORMANCE_EVIDENCE` means that a bundle is eligible for scoped L3 review; it never changes the public capability level automatically.

Core rule: **keep Python on the manifest, validation, scheduling, provenance and experiment-control plane; migrate only profiled numerical hotspots to C++/Fortran/CUDA/OpenACC or a portability backend.** Edge devices should preferentially run structure checks, preprocessing, queue control and validated surrogate inference, while production DFT normally returns to a workstation or HPC system.

## Engineering quality and one-command acceptance

```bash
python -m pip install -c constraints/py312.txt -r requirements-dev.txt
python -m pip check
python scripts/quality_gate.py
```

Current baseline: **177 unit tests, 9 isolated suites, 0 failed suites**. Every quality stage has an explicit timeout, and `--json` is safe for machine parsing. Gate order:

```text
versioned demo assets
→ dependency and version contract
→ cross-version exact CI constraints
→ repository-only packaging model
→ DFT catalog
→ Agent eval contracts
→ governance and workflow policy
→ capability and scientific-claim boundaries
→ high-confidence secret patterns
→ explained ignore markers
→ governed AI cover
→ bilingual README visuals
→ offline local links
→ Ruff lint
→ Ruff formatting
→ isolated mypy type checks
→ Bandit production audit
→ strict repository audit
→ all non-empty test suites
```

GitHub Actions runs separate Python 3.10 / 3.12 / 3.13 constraint snapshots and re-runs weekly CodeQL `security-extended`, runtime/development/locked-environment `pip-audit`, and a locked CycloneDX JSON SBOM build. Constraint refreshes must use the reviewed snapshot procedure rather than silent manual drift.

Engineering audit, supply-chain policy, Agent security and performance boundaries:

- [`docs/REPOSITORY_FULL_AUDIT.md`](docs/REPOSITORY_FULL_AUDIT.md)
- [`docs/CODE_QUALITY_AUDIT.md`](docs/CODE_QUALITY_AUDIT.md)
- [`docs/AGENT_SECURITY_MODEL.md`](docs/AGENT_SECURITY_MODEL.md)
- [`docs/SUPPLY_CHAIN_POLICY.md`](docs/SUPPLY_CHAIN_POLICY.md)
- [`docs/SCIENTIFIC_CLAIM_POLICY.yaml`](docs/SCIENTIFIC_CLAIM_POLICY.yaml)
- [`docs/PERFORMANCE_AUDIT.md`](docs/PERFORMANCE_AUDIT.md)
- [`docs/PERFORMANCE_GUIDE.md`](docs/PERFORMANCE_GUIDE.md)
- [`docs/TEST_REPORT.md`](docs/TEST_REPORT.md)

## Scientific boundaries

This repository:

- does not distribute Gaussian, VASP, Quantum ESPRESSO, CP2K, Multiwfn, VMD, POTCAR, pseudopotentials or restricted basis/potential libraries;
- does not bypass licences, site policy or software access controls;
- never presents conceptual AI imagery as an orbital, ESP, band structure, free-energy profile, transition state, mechanism or experiment;
- never equates normal termination, scheduler completion, model score or attractive graphics with scientific acceptance;
- never equates GPU allocation, a CUDA-X dependency, planner output or candidate benchmark files with measured acceleration;
- never claims `L3_EXECUTION_TESTED` without immutable real-engine evidence.

## Documentation map

| Document | Purpose |
|---|---|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Architecture and state flow |
| [`docs/ENGINE_SUPPORT_MATRIX.md`](docs/ENGINE_SUPPORT_MATRIX.md) | Engine coverage and support levels |
| [`docs/CAPABILITY_STATUS.yaml`](docs/CAPABILITY_STATUS.yaml) | Machine-readable capability status |
| [`docs/SCIENTIFIC_BOUNDARIES.md`](docs/SCIENTIFIC_BOUNDARIES.md) | Scientific boundaries and non-claims |
| [`docs/SCIENTIFIC_CLAIM_POLICY.yaml`](docs/SCIENTIFIC_CLAIM_POLICY.yaml) | Machine-readable claim-strength and L3 evidence contract |
| [`docs/CROSS_SKILL_HANDOFF.md`](docs/CROSS_SKILL_HANDOFF.md) | Cross-Skill handoff contract |
| [`docs/REPOSITORY_FULL_AUDIT.md`](docs/REPOSITORY_FULL_AUDIT.md) | Full repository security, supply-chain and Agent Skill audit |
| [`docs/CODE_QUALITY_AUDIT.md`](docs/CODE_QUALITY_AUDIT.md) | Repository-wide code, test and CI audit |
| [`docs/SUPPLY_CHAIN_POLICY.md`](docs/SUPPLY_CHAIN_POLICY.md) | Dependency locking, vulnerability audit, SBOM and release policy |
| [`docs/AI_IMAGE_GOVERNANCE.md`](docs/AI_IMAGE_GOVERNANCE.md) | AI-image governance |
| [`docs/README_VISUAL_DESIGN_SYSTEM.md`](docs/README_VISUAL_DESIGN_SYSTEM.md) | README visual design system |
| [`docs/PERFORMANCE_GUIDE.md`](docs/PERFORMANCE_GUIDE.md) | Compute, GPU, native-code and edge acceleration boundaries |
| [`docs/TEST_REPORT.md`](docs/TEST_REPORT.md) | Test, visual and engineering gates |

Repository policy: **work directly on `main`; do not create feature, fix or temporary branches. Use Tags / Releases for publication snapshots.**

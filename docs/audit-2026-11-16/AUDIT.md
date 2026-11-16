# Scientific reasonableness audit — 2026-11-16

Baseline: `f52107eaefcfe8ac05ba1544db0f0e917004e01e`. The coordinator verified that the live repository had only `main` and no open pull request. This review makes no new branch and preserves source evidence.

## Findings and corrections

### Reaction energies were disconnected from their species states

The baseline admitted an `accepted` network with species free energies `G(A)=0`, `G(B)=+20 kcal/mol`, while the declared reaction `A → B` had `ΔG=-2 kcal/mol`, forward barrier `15`, and reverse barrier `17`. The standalone closure checker also returned success: it only compared the two barriers with the independently declared reaction energy. Thus mutually consistent reaction fields could describe the opposite equilibrium direction from the species table. The network validator itself did not call the barrier closure checker.

The closure checker now computes `ΔG = Σ(products νᵢ Gᵢ) − Σ(reactants νᵢ Gᵢ)` from the written stoichiometry whenever a species table is supplied, and compares it with the declared reaction energy. Exact rational products and sums preserve the supplied binary64 values through stoichiometric cancellation. It then retains the existing independent barrier check `ΔG‡reverse = ΔG‡forward − ΔGreaction`. The network validator uses that same checker after structural and conservation checks succeed. Each comparison uses an explicit absolute tolerance in the declared `energy_unit`; the default remains `0.05`, and network CLI callers can set `--energy-tolerance`.

A standalone barrier-only table remains supported, with `species_energy_checked=false`. Supplying an incomplete or ambiguous state table does not silently fall back to barrier-only verification. The legacy optional `reversible` flag continues to default to false. Missing reverse barriers remain a derivation warning under the existing network acceptance policy; no missing state energy or barrier is fabricated, and input records are unchanged.

The regressions include weighted `2 A → B` stoichiometry, an element-reference shift that leaves balanced reaction energies unchanged, a three-edge cycle with a false free-energy gain, tolerance boundaries, malformed state identity, and rejection through the public network CLI. The existing conservation-scale fixture now uses zero species/reaction energies, so it tests conservation scaling without simultaneously changing thermodynamic reaction normalization.

### Concentration TST accepted unsupported activity models through the public API

The rate formula implements ideal concentration activity `a=c/c°`, with the standard concentration factor `c°^(1−molecularity)`. The public `StandardState` constructor nevertheless accepted any nonempty activity string, including pressure, mole-fraction and activity-coefficient models. Those labels could therefore produce concentration-based numerical rates without the required thermodynamic conversion. The CSV CLI already rejected unsupported models.

The public constructor now accepts only the four established spellings of the implemented concentration convention. The CLI also accepts the canonical spelling `dimensionless_activity_c_over_c0`, aligning both entry points. The tests independently evaluate the Eyring equation and verify that explicitly converting a bimolecular activation free energy between two concentration reference states preserves the physical rate. No pressure-to-concentration or nonideal conversion is inferred from a label.

## Additional paths reviewed

The review inspected data admission, splitting, training and evaluation in `validate_dft_dataset.py`, `group_split.py`, `train_ridge_baseline.py` and `select_active_learning_batch.py`. Group-disjoint splitting, train-only standardization, ridge intercept handling and the prior reference-invariant metric correction were consistent with the declared baseline model; no speculative change was made. `check_energy_compatibility.py`, `build_energy_profile.py`, `export_cantera_handoff.py`, the kinetics example and reference contracts were also reviewed. Cantera handoff remains review-required, and a matching method fingerprint is not treated as proof of physically correct thermochemistry.

## Validation

The initial new regression file, run against unchanged baseline source, had **11 failed and 6 passed** assertions. Those failures include missing diagnostic fields as well as the scientific contract failures described above; they are not eleven independent scientific defects. Six additional CLI, malformed-state and legacy-compatibility cases were added while implementing the correction.

The complete `python scripts/quality_gate.py --report-dir <local-evidence-directory>` run passed **all 29 stages** after the scientific source was frozen. Runtime-dependent quality/coverage/release reports were kept separate from archived repository acceptance evidence.

- Nine suites: **1,353 passed; 3 skipped; 1,117 subtests passed; no failed suites**.
- Existing coverage configuration: **93.03% statements; 83.13% branches**, above the 90%/80% requirements.
- Six trust-core files: 100% statements and 99.29–100% branches, above the 95% branch requirement.
- Dependency/constraint, acceleration, engine/compute, catalog, evaluation, governance and packaging contracts: passed.
- Ruff lint/format, 18 mypy targets, four strict trust-boundary targets, Bandit, secret checks, README visuals/links and strict repository checks: passed.

[validation.json](validation.json) records the baseline reproductions, executed gate stages, exact counts, source hashes and limits. Final staged documentation and deterministic evidence were checked separately before commit; no scientific source changed after the full run.

## Scientific limits and sources

These checks establish arithmetic consistency conditional on the declared common temperature, phase, reference state and energy basis. They do not establish the authenticity of DFT artifacts, the accuracy of a functional, diffusion/transport validity, nonideal kinetics, or scientific acceptance of a mechanism. No DFT engine, paid service, remote scientific job or experimental calibration was executed. Local validation uses Python 3.12; platform and Python-version coverage comes from the repository's exact-head CI.

The governing identities were checked against primary documentation:

- [Cantera ThermoPhase: chemical potential, activities and standard states](https://www.cantera.org/stable/cxx/dc/d38/classCantera_1_1ThermoPhase.html).
- [Cantera stoichiometric property differences](https://www.cantera.org/2.5/doxygen/html/d4/dc8/group__Stoichiometry.html).
- [IUPAC transition-state theory](https://goldbook.iupac.org/terms/view/T06470).

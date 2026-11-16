# Scientific numerical audit — 2026-11-15

Base commit: `6b0c6c5aa405880b3c8d0847aee9e8fec66ce17d`. The coordinator verified that `main` was the sole remote branch and that no PR was open.

## Corrections

1. **Conservation under arbitrary stoichiometric normalization.** Reaction validation uses exact products and separate relative scales for element, charge and site balances. Small coefficients cannot hide an imbalance; intermediate overflow cannot turn the decision into a false pass. Balanced cases and trace species are tested from the smallest positive binary64 value to `1e308`.
2. **Physical species counts.** Negative atom counts and site occupancies fail validation. Signed ionic charge remains supported.
3. **Thermodynamic closure arithmetic.** Huge integers and overflow in reverse-barrier or closure-residual calculation produce structured errors, without invalid numerical rows.
4. **Reference-invariant regression metrics.** A common energy offset no longer changes MAE, RMSE or R². Residuals and target spread use separate scales, preserving a small nonzero prediction error in a dataset with a very large target range. The tests also cover subnormal target variance and representable aggregate error despite an overflowing individual subtraction.

The review added 15 regression test methods. Baseline failures were reproduced before correction; both valid and invalid boundary cases remain covered.

## Executed validation

The complete `python scripts/quality_gate.py` run passed all **29 stages** on the final frozen code, including repository contracts, catalogs, governance, secret scanning, visual/link validation, Ruff lint/format, 18 mypy targets, four strict trust targets, branch coverage, Bandit and all test suites.

- Nine suites: **1,330 passed; 3 skipped; 1,117 subtests passed; no failed suites**.
- Existing coverage configuration: **93.06% statements; 83.09% branches**, exceeding the 90%/80% gates.
- Six trust-core files: 100% statement coverage, with branch coverage from 99.29% to 100%, above the 95% requirement.
- The three skipped checks require a PowerShell executable unavailable in this Linux environment.
- Bandit passed the repository's existing reviewed finding policy; its 21 reviewed raw findings are not described as zero findings.

The local Python 3.12.14 environment used NumPy 2.3.5 and matplotlib 3.10.8, within the declared runtime ranges. The CI Python 3.12 constraint file pins NumPy 2.5.1 and matplotlib 3.11.1. Lint, typing, security and test tools used their declared exact versions. This run verifies the complete local gate; it does not substitute for the exact-constraint cross-platform CI jobs.

[validation.json](validation.json) records stage results, suite counts, dependency versions, tested content hashes and scope. No real DFT/HPC execution or scientific-acceptance claim was introduced.

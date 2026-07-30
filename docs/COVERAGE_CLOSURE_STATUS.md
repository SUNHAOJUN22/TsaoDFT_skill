# Coverage Closure Status

This document records the current release-qualification coverage closure work without changing production behavior or quality thresholds.

- Baseline before the acceleration edge batch: 89.47% statement coverage and 75.06% branch coverage.
- Trust-core requirement remains 100% statement coverage and at least 95% branch coverage per file.
- The current batch adds deterministic boundary tests for performance evidence, cross-vendor acceleration planning, and engine-specific autotuning.
- Simulated hardware and engine fixtures are test inputs only and are not real performance evidence.
- The three acceleration-edge test files are being normalized with the repository's locked Ruff version and validated with mypy and targeted unit tests.
- Release qualification remains blocked until the permanent Python 3.10, 3.12, and 3.13 matrix, CodeQL, dependency audits, SBOM, and the 90%/80% whole-repository coverage gates pass on the same commit.

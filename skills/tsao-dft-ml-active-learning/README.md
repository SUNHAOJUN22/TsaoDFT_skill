# Tsao DFT + ML and Active Learning

For DFT descriptors, molecular/material ML, surrogate models, uncertainty, applicability domain, active learning and inverse design. DeepChem/RDKit are optional; deterministic validation and split scripts use standard Python.

```bash
python scripts/validate_ml_manifest.py examples/molecular/ml-project.yaml
python scripts/group_split.py examples/molecular/dataset.csv --group parent_id --out-dir split
python scripts/select_active_learning_batch.py examples/active-learning/pool.csv --batch-size 3 --out selected.csv
```

Group splitting rejects any output that aliases the input, including hard links
and symbolic links, and rejects output targets that alias each other. All three
CSV files are staged and checked before publication. Existing output files are
backed up, individual replacements are atomic, and a caught publication failure
restores the previous set. Unrelated files remain intact. A cooperative output
lock prevents simultaneous split writers. If rollback itself fails, recovery
files are retained and the error reports their location. The three replacements
are not a filesystem-wide transaction; interruption by process termination or
power loss requires reviewing retained staging files before reusing the output.

## v0.4 depth

See `SKILL.md`, `manifest.yaml`, `scripts/`, `templates/`, and `tests/` for the deterministic DFT adapters and scientific gates introduced in v0.4.0-alpha.1.

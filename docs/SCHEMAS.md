# Manifest Schemas

TsaoDFT uses small release-layer manifests around immutable scientific files. Deterministic validators enforce semantic rules beyond lightweight YAML/JSON schemas.

## Core research and figure manifests

`tsao-dft-researcher` retains:

- `research-manifest.json`: calculations → artifacts → claims;
- `figure-manifest.json`: artifacts → panels → comparison groups → outputs.

Accepted minima, TS/IRC, open-shell work, evidence grades, shared ESP scales and AI-schematic labeling are enforced.

## Structure manifest

Records identity, model type, source/hash, units, periodicity, charge/multiplicity candidates, transformations and review status. Periodic surfaces/defects/adsorbates add cell, vacuum and image-separation fields.

## Periodic DFT manifest

Records engine/version, task type, structure/model review IDs, method fingerprint, convergence and status. Separate energy-expression manifests require compatible method fingerprints across every term.

## ML manifest

Records target/unit, independent sample unit, group column, split policy, train-only preprocessing, seeds/folds, metrics, applicability domain and status.

## HPC manifest

Records engine/executable/input, scheduler, resources, environment, expected outputs, checkpoint policy and approval.

## Kinetics network

Records temperature, phase/standard state, species/artifacts, elementary reactions, barriers/free energies, site balance and status.

Templates are located inside each Skill under `templates/`.

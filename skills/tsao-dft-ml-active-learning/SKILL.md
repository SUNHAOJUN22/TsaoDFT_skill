---
name: tsao-dft-ml-active-learning
description: "Build leakage-aware DFT descriptor, surrogate, GNN, uncertainty, applicability-domain, active-learning, Bayesian/multi-objective optimization and inverse-design workflows with optional DeepChem, RDKit and scikit-learn backends."
license: MIT
compatibility: Python 3.10+. DeepChem, RDKit, scikit-learn and graph frameworks are optional external backends.
metadata: {"version": "0.3.0-alpha.1", "author": "SUNHAOJUN22", "repository": "https://github.com/SUNHAOJUN22/TsaoDFT_skill"}
---

# Tsao DFT + ML and Active Learning

Use only after the independent scientific sample unit is defined. A conformer, spin state, charge state, duplicate calculation or repeated seed is not automatically a new molecule/material.

## Workflow

1. Define the prediction target, scientific decision and independent grouping unit.
2. Register structures, labels, method fingerprints, fidelity level, parent IDs and uncertainty/source flags.
3. Choose split policy before feature engineering: scaffold/group/time/composition/extrapolation as appropriate.
4. Fit preprocessing, feature selection and calibration on training data only.
5. Report train/validation/test metrics across seeds or folds, applicability domain and uncertainty.
6. For active learning, freeze the acquisition objective, constraints, diversity rule, batch size and stop criterion before selecting new DFT jobs.
7. Route selected candidates back through structure review, DFT execution and acceptance; do not feed unvalidated calculations into the training set.

## Routes

| Need | Route |
|---|---|
| Descriptor/fingerprint or graph data | `dataset` |
| Baseline, GNN or surrogate model | `model` |
| Leakage, split, calibration, uncertainty and AD | `validation` |
| Active learning and Bayesian optimization | `active_learning` |
| Multi-objective/inverse/generative design | `inverse_design` |

## Hard Guardrails

- Parent structures and close derivatives must not leak across train/test without an explicit interpolation study.
- DFT method/fidelity is a feature and provenance field; mixed labels cannot be pooled silently.
- The test set never drives feature selection, hyperparameters, stopping, threshold selection or explanation filtering.
- SHAP/feature importance is model explanation, not causal mechanism.
- Active-learning acquisition scores do not establish synthesizability, stability or novelty.
- Report uncertainty calibration and applicability domain; a single high R² is insufficient.


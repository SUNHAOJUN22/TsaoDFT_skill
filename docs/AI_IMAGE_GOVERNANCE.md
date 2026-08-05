# AI Image Governance

TsaoDFT keeps AI-assisted conceptual imagery, deterministic explanatory graphics and accepted scientific results on separate evidence tracks.

## Directory contract

```text
assets/ai/
├── hero/        # the single governed README conceptual overview
├── prompts/     # generation intent, visual direction and boundary record
└── manifest.yaml

assets/demo/      # repository-controlled deterministic SVG demonstrations
```

A separate AI raster gallery or AI module-card collection is not maintained. The single hero remains the only asset registered in `assets/ai/manifest.yaml`. Architecture, workflow and acceleration diagrams under `assets/demo/` may use an AI-assisted visual direction, but their actual SVG markup is repository-controlled, deterministic and reviewed as source code.

## Mandatory metadata for the governed hero

The governed overview records:

- repository path and role;
- generation identifier;
- prompt / visual-direction record;
- integer dimensions;
- SHA-256 digest;
- AI-assisted and illustrative-only flags;
- quantitative and computed-surface prohibitions;
- explicit allowed and forbidden uses.

## Visual labelling

The governed overview contains a visible footer stating:

```text
AI-ASSISTED CONCEPTUAL ILLUSTRATION · NOT COMPUTATIONAL DATA
```

Both README files repeat the disclosure immediately before the image.

Every deterministic SVG in `assets/demo/` contains the visible notice:

```text
SYNTHETIC DEMO · NOT SCIENTIFIC DATA
```

Its accessible `<desc>` must also explicitly state that it is synthetic and not scientific data.

## Prohibited representations

No conceptual or deterministic explanatory visual may be described as:

- an optimised molecular geometry;
- a HOMO/LUMO/SOMO, NTO, ESP, ELF, IRI, IGMH, QTAIM or ICSS result;
- a VASP/QE/CP2K band structure, DOS, charge density, defect or slab result;
- a transition state, IRC, free-energy profile or microkinetic output;
- an experiment, hardware benchmark, measured speedup or mechanistic proof;
- evidence that CUDA-X, C++, GPU, edge inference or an external engine has been used successfully.

Cropped or recomposed motifs from earlier user-approved TsaoDFT concept art remain conceptual. Their reuse does not convert them into scientific data.

## Deterministic architecture gallery

All files in `assets/demo/` are standalone deterministic SVGs. They must:

- keep the exact dimensions and titles listed in `scripts/generate_readme_demos.py`;
- include `role="img"`, an accessible `<title>`, a useful `<desc>` and the visible synthetic-data notice;
- contain no embedded AI raster imagery, remote image reference, executable content or opaque binary payload;
- remain reproducible from repository-controlled vector definitions or fixed source data;
- be embedded in both README files when listed in `REQUIRED_DEMOS`;
- distinguish recommendations and evidence gates from measured results.

The acceleration gallery covers:

- Python control plane versus native/GPU/external-engine compute planes;
- workload-bounded CUDA-X library selection;
- edge inference with uncertainty/OOD routing to remote DFT;
- profile-gated Python → vectorised CPU → C++ → GPU migration;
- scoped L3 evidence qualification without automatic public capability promotion.

These diagrams explain contracts. They neither execute nor qualify acceleration.

## Validation

```bash
python scripts/validate_ai_assets.py
python scripts/generate_readme_demos.py
python scripts/validate_readme_visuals.py --strict
```

The validators check paths, dimensions, titles, accessible descriptions, XML validity, AI-manifest digests, README embedding, visible disclosure and deterministic-demo contracts. They cannot infer scientific meaning from pixels; human review remains required.

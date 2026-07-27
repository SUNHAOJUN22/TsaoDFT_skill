# AI Image Governance

TsaoDFT uses AI-assisted imagery only for one conceptual README overview. Deterministic demonstration figures and accepted scientific results remain separate.

## Directory contract

```text
assets/ai/
├── hero/        # the single README conceptual overview
├── prompts/     # generation intent, source direction and boundary record
└── manifest.yaml
```

A separate AI module-card gallery is not maintained. The single dark overview may contain multiple conceptual research motifs, but it remains one governed asset with one provenance record and one explicit scientific boundary.

## Mandatory metadata

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

The overview contains a visible footer stating:

```text
AI-ASSISTED CONCEPTUAL ILLUSTRATION · NOT COMPUTATIONAL DATA
```

Both README files repeat the disclosure immediately before the image.

## Prohibited representations

The conceptual overview must never be described as:

- an optimised molecular geometry;
- a HOMO/LUMO/SOMO, NTO, ESP, ELF, IRI, IGMH, QTAIM or ICSS result;
- a VASP/QE/CP2K band structure, DOS, charge density, defect or slab result;
- a transition state, IRC, free-energy profile or microkinetic output;
- an experiment, benchmark or mechanistic proof.

Cropped or recomposed motifs from earlier user-approved TsaoDFT concept art remain conceptual. Their reuse does not convert them into scientific data.

## Deterministic figures

All files in `assets/demo/` are standalone deterministic SVGs. They must:

- keep the exact dimensions and titles listed in `scripts/generate_readme_demos.py`;
- include `role="img"`, a useful description and a visible synthetic-data notice;
- contain no embedded AI raster imagery;
- remain reproducible from repository-controlled vector definitions or source data.

## Validation

```bash
python scripts/validate_ai_assets.py
python scripts/generate_readme_demos.py
python scripts/validate_readme_visuals.py --strict
```

The validators check path, dimensions, digest, metadata, README embedding, visible disclosure and deterministic-demo contracts. They cannot infer scientific meaning from pixels; human review remains required.

# AI Image Governance

TsaoDFT limits AI-assisted imagery to one conceptual README cover. Deterministic demonstration figures and accepted scientific results remain separate.

## Directory contract

```text
assets/ai/
├── hero/        # the single README conceptual cover
├── prompts/     # generation intent and boundary record
└── manifest.yaml
```

A module-card gallery is deliberately not maintained. Module identity is communicated through text and deterministic figures rather than repeated conceptual artwork.

## Mandatory metadata

The governed cover records its repository path, role/topic, source generation ID, prompt record, dimensions, SHA-256 digest, AI/illustrative flags and explicit allowed/forbidden uses.

## Visual labeling

The cover contains a visible footer stating that it is an AI-assisted conceptual illustration and not computational data. The README repeats the disclosure beside the image.

## Prohibited representations

The cover must never be described as an optimized molecular geometry; a HOMO/LUMO/SOMO, NTO, ESP, ELF, IRI, IGMH, QTAIM or ICSS result; a VASP/QE/CP2K band structure, DOS, charge density, defect or slab result; a transition state, IRC, energy profile or microkinetic output; an experiment; or mechanistic proof.

## Deterministic validation

```bash
python scripts/validate_ai_assets.py
```

The validator requires exactly one governed hero, verifies file existence, SVG dimensions, SHA-256 integrity, prompt provenance, README embedding and the non-quantitative policy. It cannot prove scientific meaning from pixels; human review remains required.

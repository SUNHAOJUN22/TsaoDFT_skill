# AI Image Governance

TsaoDFT uses AI-generated images only for conceptual communication. AI images are deliberately separated from deterministic demonstration figures and accepted scientific results.

## Directory contract

```text
assets/ai/
├── hero/        # README cover visual
├── modules/     # module-level conceptual illustrations
├── prompts/     # generation intent and boundary record
└── manifest.yaml
```

## Mandatory metadata

Every AI asset records its repository path, role/topic, source generation ID, prompt record, dimensions, SHA-256 digest, AI/illustrative flags, and explicit allowed/forbidden uses.

## Visual labeling

README-facing derivatives contain a visible footer stating that the image is an AI-generated conceptual illustration and not computational data. The source generation ID and prompt record are retained for provenance; README assets remain non-quantitative.

## Prohibited representations

An AI image must never be described as an optimized molecular geometry; a HOMO/LUMO/SOMO, NTO, ESP, ELF, IRI, IGMH, QTAIM or ICSS result; a VASP/QE/CP2K band structure, DOS, charge density, defect or slab result; a transition state, IRC, energy profile or microkinetic output; an experiment; or mechanistic proof.

## Deterministic validation

```bash
python scripts/validate_ai_assets.py
```

The validator checks manifest completeness, file existence, SVG dimensions, SHA-256 integrity, prompt provenance and the non-quantitative policy. It cannot prove scientific meaning from pixels; human review remains required.

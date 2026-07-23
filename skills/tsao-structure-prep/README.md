# Tsao Structure Prep

General structure-preparation Skill for molecular and periodic DFT projects. It is suitable for molecules, organometallic complexes, crystals, surfaces, interfaces, defects and adsorption campaigns. It is not a geometry generator that silently decides chemistry.

```bash
python scripts/validate_structure_manifest.py examples/molecule-campaign/structure-manifest.yaml
python scripts/expand_structure_campaign.py examples/molecule-campaign/campaign.yaml --out candidates.csv
```

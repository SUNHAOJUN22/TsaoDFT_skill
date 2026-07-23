# Tsao Periodic DFT and Materials

Use for periodic crystals, surfaces, defects, adsorption, electronic structure, phonons, elastic properties, NEB and high-throughput DFT. It complements the molecular Gaussian-centered core.

```bash
python scripts/validate_periodic_manifest.py examples/adsorption/periodic-project.yaml
python scripts/build_convergence_matrix.py examples/convergence/convergence.yaml --out convergence.csv
python scripts/check_energy_compatibility.py examples/adsorption/energy-terms.yaml
```

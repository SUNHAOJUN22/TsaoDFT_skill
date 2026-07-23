# Tsao DFT Kinetics and Multiscale

Use for DFT free energies → TST rates → reaction networks → microkinetic, Cantera/RMG, Pyomo/CatMAP, reactor or population-balance handoffs.

```bash
python scripts/validate_reaction_network.py examples/catalysis/network.yaml
python scripts/eyring_rates.py examples/catalysis/barriers.csv --temperature 298.15 --out rates.csv
```

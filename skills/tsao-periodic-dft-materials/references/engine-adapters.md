# Engine Adapters

VASP, QE and CP2K use different syntax but the same scientific contract. Do not translate settings by keyword analogy alone. Preserve exact pseudopotential/basis identifiers, version, parallel layout and actual input files.

The VASP preflight resolves POSCAR scaling before reporting geometry: `raw_lattice_vectors` preserves the input vectors, `lattice_vectors` contains the scaled vectors in angstroms, and `cell_volume_angstrom3` reports the resulting cell volume. A negative scalar scale is treated as a target cell volume; three positive scale values apply to Cartesian components, and `scale` is `null` for that three-factor form. Cartesian atom coordinates are interpreted with the same resolved factors during validation. These checks validate input structure only; `scientific_acceptance` remains pending until the actual engine result is independently reviewed.

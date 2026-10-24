# Deterministic Periodic-DFT Adapters

The included VASP, Quantum ESPRESSO and CP2K scripts perform input preflight and output evidence extraction. They are `L2_VALIDATED_ADAPTER` only for the fields exercised by repository tests; they are not full replacements for each engine's parser or manual.

- VASP: INCAR/POSCAR/KPOINTS and POTCAR TITEL mapping; OUTCAR energy/convergence/force/timing evidence.
  POSCAR geometry follows the [official VASP specification](https://vasp.at/wiki/POSCAR):
  a blank first comment record is preserved, and equivalent raw-vector/scale
  representations produce the same physical cell. Singularity checks use
  normalized lattice directions after positive component scaling; the raw
  volume is needed only for a negative target-volume factor. Volume calculations avoid overflowing an
  unscaled determinant before a compensating scale can be applied. Both Direct
  and Cartesian positions must remain finite after conversion to Angstrom.
  These input checks do not establish physical suitability or scientific acceptance.
- QE: pw.x namelists/cards/pseudopotential filenames; total energy, convergence, force, pressure and Fermi evidence.
- CP2K: Quickstep RUN_TYPE, basis/potential, grid, KIND, PBC and SCF checks; total energy and convergence evidence.

Every production site must record engine/version and run a site smoke/regression test before claiming `L3_EXECUTION_TESTED`.

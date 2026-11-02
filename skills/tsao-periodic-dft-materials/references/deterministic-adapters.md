# Deterministic Periodic-DFT Adapters

The included VASP, Quantum ESPRESSO and CP2K scripts perform input preflight and output evidence extraction. They are `L2_VALIDATED_ADAPTER` only for the fields exercised by repository tests; they are not full replacements for each engine's parser or manual.

- VASP: INCAR/POSCAR/KPOINTS and POTCAR TITEL mapping; OUTCAR energy/convergence/force/timing evidence.
  The INCAR reader follows the [documented flat statement syntax](https://vasp.at/wiki/INCAR):
  semicolon-separated tags, terminal-backslash continuations and multiline
  double-quoted values. Comments and quoted content cannot create additional
  global tags. This preserves ionic-task, spin and DFT+U checks when statements
  share a line. Explicit slash-qualified tags remain distinct; brace-scoped
  blocks are not interpreted and cause preflight failure. Unterminated quotes,
  dangling continuations and empty assignments also fail without changing the
  input. A malformed INCAR leaves the inferred task `unknown` and scientific
  acceptance `PENDING`.
  The selected integer controls `NSW`, `IBRION` and `ISPIN` require complete
  signed decimal integers; fractional/exponential forms are rejected instead
  of truncated or replaced by zero. The reader preserves leading signs and
  supports the signed 64-bit range without float conversion. Values beyond
  that explicit adapter limit produce a structured error. This is not an
  assertion about an engine build's integer kind or suitable run length; see
  the official [NSW](https://vasp.at/wiki/NSW) and [IBRION](https://vasp.at/wiki/IBRION)
  specifications and review the actual engine interpretation at the site.
  Task inference remains limited to `static`, `relax` and `unknown`. Positive
  `NSW` implies `relax` only with explicit `IBRION=1`, `2` or `3`; `IBRION=-1`
  means no structural update. Molecular dynamics (including the default
  `IBRION=0` for positive `NSW`), phonons and other unhandled modes produce
  `unknown` with a mode-specific review warning, even when their input is
  syntactically valid. This preflight does not certify those modes as static or
  relaxed, and scientific acceptance remains `PENDING`.
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

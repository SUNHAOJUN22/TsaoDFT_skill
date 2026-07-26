# Compute Efficiency Guide

This guide separates **software overhead**, **scheduler throughput** and **electronic-structure cost**. A faster parser cannot make an unconverged DFT method scientifically acceptable, and more MPI ranks do not guarantee a faster calculation.

## Implemented repository optimizations

### Memory-mapped periodic-output parsing

`parse_vasp.py`, `parse_qe.py` and `parse_cp2k.py` scan output files through read-only memory maps. They retain only the last accepted values and small terminal blocks instead of decoding the entire output into one Python string.

| Property | Previous approach | Current approach |
|---|---|---|
| File traversal | full decode plus repeated whole-file regular expressions | one mapped file with marker and compiled-pattern scans |
| Python heap | proportional to output-file size and match lists | near-constant, except the final VASP force block |
| Scientific fields | selected evidence fields | unchanged |

A local synthetic 12.75 MB VASP-output benchmark used during this revision measured approximately `0.694 s / 41.9 MB` peak Python allocation for the previous parser and `0.555 s / 0.012 MB` for the mapped parser. This is an implementation benchmark, not an engine-runtime claim; performance depends on filesystem, operating system and output structure.

### Adaptive ridge solver

The NumPy ridge baseline now chooses the smaller regularized linear system:

- **primal** when features are not wider than the training set;
- **dual** when the feature count exceeds the training-sample count;
- stable `numpy.linalg.lstsq` when `alpha = 0`.

For `n` training samples and `p` features, this avoids always forming and solving a `(p + 1) × (p + 1)` system. The dual path instead solves an `n × n` system and maps the coefficients back to feature space. The model card records the requested solver, selected solver and solve dimension.

A local synthetic `100 × 800` benchmark measured about `47.5×` lower solver time for the automatic dual path, with a maximum prediction difference of `2.2 × 10⁻¹⁵` relative to the previous formulation. Real gains depend on BLAS, matrix shape and hardware.

## High-impact execution guidance

### Use true array operations

`numpy.vectorize` is a convenience wrapper whose implementation is essentially a Python loop; it is not a performance primitive. Prefer broadcasting, ufuncs, matrix operations and reductions when the operation can be expressed on arrays.

Official reference: <https://numpy.org/doc/stable/reference/generated/numpy.vectorize>

### Batch independent Python work deliberately

For CPU-bound, picklable tasks, `ProcessPoolExecutor` can bypass the GIL. For long iterables, a non-trivial `chunksize` can substantially reduce scheduling overhead. Do not wrap external MPI engines in uncontrolled nested process pools.

Official reference: <https://docs.python.org/3.13/library/concurrent.futures.html>

### Avoid duplicate atomistic work

ASE database reservations can prevent multiple workers from performing the same calculation. ASE also provides MPI-aware I/O so large structures are read once by the master and broadcast rather than independently parsed by every rank.

Official references:

- <https://wiki.fysik.dtu.dk/ase/ase/db/db.html>
- <https://wiki.fysik.dtu.dk/ase/ase/parallel.html>

### Reuse persistent engine processes when valid

For repeated geometry steps, file-based calculators may repeatedly launch an external engine and perform heavy I/O. ASE socket communication can keep a supported engine alive and exchange coordinates, energies, forces and stress without restarting at every step. This must be supported and validated for the selected engine and site.

Official reference: <https://wiki.fysik.dtu.dk/ase/ase/calculators/socketio/socketio.html>

### Use scheduler arrays for homogeneous campaigns

Large collections of independent, similarly resourced calculations are normally better represented as scheduler arrays than as thousands of individually generated submission scripts. Keep per-task manifests, immutable inputs, output directories and failure states separate.

Official reference: <https://slurm.schedmd.com/job_array.html>

## Engine-runtime checklist

Before increasing CPU count, test the actual engine and model:

1. converge basis, cutoff, k-mesh, supercell and vacuum before production campaigns;
2. reuse compatible checkpoints or wavefunctions without crossing method-fingerprint boundaries;
3. avoid oversubscribing MPI ranks and OpenMP threads;
4. stage scratch-heavy work on the site-approved fast filesystem;
5. measure wall time, CPU efficiency, memory high-water mark and I/O volume;
6. use job arrays or workflow engines for independent tasks, and engine-native MPI for one parallel calculation;
7. stop or quarantine repeated failures instead of automatically consuming more resources;
8. record all performance changes in the run provenance.

## Non-claims

The repository does not claim universal speedups for Gaussian, VASP, Quantum ESPRESSO, CP2K, Multiwfn, Cantera or any HPC site. Engine-level tuning depends on executable version, compilation, BLAS/FFT/MPI libraries, pseudopotentials or basis sets, model size, network topology and filesystem. Only measurements from the legal target environment can establish an L3 performance result.

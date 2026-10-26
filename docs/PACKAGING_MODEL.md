# Packaging Model

## Classification

TsaoDFT is **B — a repository-style Agent Skill collection**.

The repository contains eight independently installable Skill directories, validators, documentation and governed assets. It is not currently a conventional importable Python library and does not claim that `python -m build` should produce a publishable wheel.

`pyproject.toml` is used for dependency, Python-version and tool configuration. The absence of a `[build-system]` table is intentional. Adding a build backend without an explicit package layout would incorrectly package top-level directories such as `skills/` and `assets/`.

## Supported distribution

Supported installation uses:

```bash
python scripts/install.py --agent codex --scope user --skill all --dry-run --validate
python scripts/install.py --agent codex --scope user --skill all
```

The installer writes an ownership record and refuses to overwrite or uninstall foreign destinations. Copy and symlink methods are tested in temporary Agent directory layouts.

For a selected copy installation, the installer also stages the selected Skill's
parser runtime dependencies under `scripts/_shared/`. The periodic Skill needs
`engine_scan_core.py`; the researcher Skill needs that scanner plus
`engine_parser_contract_v4.py`, `_load_v18_core.py`, and
`scientific_contracts_core_v18.py`. These files are copied from the authoritative
HPC provenance sources in this repository, before the owned destination is
replaced. Their SHA-256 digests are recorded in the ownership marker and the
installed tree digest covers them. This allows either Skill's public parsers to
run without installing a sibling Skill. Repository and symlink execution use the
authoritative sibling sources directly. Use `scripts/install.py` for a selected
copy installation so that this runtime closure is included; copying only a raw
Skill directory by hand does not assemble its parser dependencies.

## Release artifacts

A future release may publish a source archive containing the repository tree, checksum, SBOM, test report and audit report. A wheel or sdist must not be advertised until a real Python package layout, build backend, clean-environment installation test and import/CLI smoke test are implemented.

## Non-claims

Repository installation does not install Gaussian, VASP, Quantum ESPRESSO, CP2K, Multiwfn, VMD, schedulers, pseudopotentials, basis libraries or licensed scientific content.

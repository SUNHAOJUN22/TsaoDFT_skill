# Supply-Chain Policy

## Deterministic blocking gate

Every `main` update must pass the offline quality gate on Python 3.10, 3.12 and 3.13. It validates dependency declarations, Agent eval contracts, governed assets, local links, Ruff, mypy, Bandit, repository structure and all non-empty unittest suites.

GitHub Actions are pinned to complete commit SHAs. Workflow permissions are minimized per job. Dangerous write-capable triggers such as `pull_request_target`, `workflow_run`, issue comments or issue-triggered write jobs are prohibited.

## Network-dependent security evidence

`pip-audit` checks runtime and development dependency sets and generates a CycloneDX JSON SBOM. This job is security-significant but network-dependent. A service outage must be reported as `NOT VERIFIED` rather than transformed into a successful vulnerability result.

A zero-vulnerability report means no matching advisories were returned for the resolved environment at that time. It does not prove that the dependency set contains no undiscovered vulnerability.

## Dependabot governance exception

`.github/dependabot.yml` records the `pip` and `github-actions` ecosystems, but `open-pull-requests-limit: 0` intentionally prevents automated update PRs because the repository owner requires a `main`-only, no-PR workflow. Dependency updates are reviewed and applied directly to `main` with complete CI evidence.

Dependabot alerts, secret scanning, push protection, CodeQL default setup and branch protection are repository settings. The audit GitHub App could not read those endpoints and records them as `NOT VERIFIED`; configuration must be confirmed by an administrator in the GitHub UI.

## Releases and provenance

Release snapshots should include:

- source archive and SHA-256;
- `VERSION`, `CITATION.cff` and `CHANGELOG.md` alignment;
- test and repository audit reports;
- CycloneDX SBOM;
- exact GitHub Actions run and commit SHA;
- an honest list of real-engine/site capabilities that remain unverified.

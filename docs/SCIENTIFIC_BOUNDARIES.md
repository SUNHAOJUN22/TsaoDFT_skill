# Scientific Boundaries

Automation can verify schemas, files, hashes, declared compatibility, parser output, convergence records, split leakage and figure parameters. It cannot decide the correct chemical model, functional, pseudopotential, spin state, standard state, transition-state mode, mechanism, causal interpretation or industrial relevance without scientific evidence and human review.

## Predictive model validation and authorization

`validate_predictive_model_card()` validates the structure of a mapping, including its declared accepted status, issuer, model hash, scope and current dates. A nonempty signature string is not authenticated. A structurally valid mapping returns `structure_valid: true`, `status: HOLD`, `predictive_use_allowed: false`, and `APPROVAL_UNVERIFIED`.

The legacy public `ml_provenance_contract.validate_model_card()` (v4) also performs
structural checks only and returns HOLD with `predictive_use_allowed: false` and
`APPROVAL_UNVERIFIED`. `scientific_contracts_v16.model_acceptance()` never returns
ACCEPTED: even `independent_approval: true` returns
`HOLD_UNVERIFIED_APPROVAL_USE_V5`. Existing mappings remain usable as inputs to
these structural checks, but approval-shaped text or a Boolean cannot authorize
prediction. Migrate to `model_acceptance_v5.assess_model_card()` with the typed
card, authenticated dataset artifact, bound independent approval and both
caller-supplied trusted key resolvers described below. This is an intentional
authorization change, not a claim that old signature strings have been verified.

The typed `assess_model_card()` API requires a separate trusted dataset issuer resolver (`dataset_key_resolver`) as well as the model approval key resolver. The caller supplies these trust stores; putting an issuer name in an artifact does not create trust. `DatasetValidationArtifact.unsigned()` contains every validation field except its signature, including schema, validator, split, quantity, unit, method, sample count, issuer and issue time. That payload is authenticated with HMAC-SHA256 using the dataset issuer's resolved key. Missing signature or key keeps the chain on hold; a signature mismatch rejects the chain. Future-issued artifacts cannot be accepted. No implicit expiration period is invented.

`ModelApproval.dataset_validation_sha256` binds the model review to the canonical SHA-256 of the full unsigned dataset validation artifact. It is itself covered by the approval signature. The schema is checked against `card.schema_sha256`, and model approval against `card.model_sha256`; environment and split hashes are distinct identities. Legacy approvals without the new binding remain constructible and retain their old unsigned serialization, but stay on hold. A fresh signature on changed validation content still requires a fresh, correctly bound model review.

The same approval must also carry `model_card_sha256 = card.digest()`. This digest
identifies every `ModelCard` field: model ID, dataset, weights, predictor code,
runtime environment, input schema, complete applicability domain, uncertainty
evidence, holdout metrics and trainer identity. Its payload is
`{"contract":"tsao.dft.model-card-review.v1","card":<all card fields>}`,
encoded as UTF-8 JSON with sorted string keys, compact separators, literal Unicode
and no nonfinite numbers. Mapping order does not affect identity; changed content
does. No approval is embedded in this payload, so the binding has no signature cycle.

The digest is covered by the model review's HMAC along with its existing purpose,
audience, reviewer, role and time bounds. Changing code, environment, evidence or
the allowed prediction domain requires a new independently signed review.
Retargeting a digest while keeping the old signature is rejected. Both optional
binding fields remain omitted from `ModelApproval.unsigned()` when absent, preserving
legacy constructor and signature payload compatibility; an absent model-card
binding produces `MODEL_CARD_BINDING_MISSING` and HOLD. A wrong binding produces
`MODEL_CARD_BINDING_MISMATCH` and HOLD. Caller-supplied trust resolvers remain
required; a card cannot supply its own trusted key.

## Execution-manifest review identity

`shell_contract.manifest_sha256()` now hashes
`{"contract":"tsao.execution-manifest-review.v2","manifest":<reviewed manifest>}`.
The manifest contains **all fields except `approval_attestation`**, including
the executable, launcher argv, stdout/stderr destinations, scratch configuration,
environment, resource requests, input, work directory, parser, preflight,
checkpoint policy, approval state and public-key locator. Extension fields are
included too. Only the attestation is excluded to avoid a signature cycle.
The payload uses canonical UTF-8 JSON with sorted string keys, compact separators
and literal Unicode; nonfinite or non-JSON content cannot be approved.

The existing externally supplied Ed25519 review key, signature verification,
review purpose and time checks still apply. The attestation covers this digest.
Changing an execution field requires a new signed review; changing only the
digest invalidates the old signature. Old approvals over the incomplete
selected-field digest are intentionally rejected. Review the complete manifest
and issue a fresh signature through the same trusted review process; no legacy
digest fallback or self-declared verification flag is accepted. This binding
identifies configuration content, not the contents of external input files or
executables unless their hashes are separately included in that configuration.

## Final-job parser identity

The public researcher Gaussian parser extracts energies, frequencies, orbitals,
coordinates, route metadata and other observations from the same final job used
for its canonical status decision. An absent final-job observation remains absent,
even if a prior job supplied it. A failed prior job cannot poison an independently
completed later job, and a fatal marker within the selected job still defeats its
normal-termination marker. The existing whole-log `normal_termination_count` and
`parser_segment_count` remain diagnostic metadata, not scientific observations.

Within the final Gaussian job, orbitals are restricted to the final `SCF Done`
record and the last contiguous population orbital block after it. Consecutive
wrapped rows of the same channel are joined; a return to an earlier channel
starts a new block. Occupied and virtual alpha values must be present; an
unrestricted SCF or observed beta output also requires both beta channels.
A following nonblank non-orbital record closes the block. An EOF inside a block,
invalid token or missing required channel produces empty `orbital_energies` and
`orbital_block.status: HOLD_INCOMPLETE_ORBITAL_BLOCK`. A final SCF with no orbital
block produces `NOT_OBSERVED`. No earlier SCF or earlier complete block fills a
partial final block. `orbital_block` records the selection policy and SCF index;
completeness here is a syntax condition, not a claim that all basis orbitals were
printed or that the electronic state is scientifically accepted.

The reason for separating optimization populations is documented by Gaussian's
official [Population reference](https://gaussian.com/population/): population
analysis may be printed at the initial and final optimization steps, or every
step with `Always`. The official [Opt reference](https://gaussian.com/opt/)
identifies the final optimization step as the source of the optimized energy.
These references support the multiple-step boundary; the conservative truncated
block handling above is this parser's explicit policy. The regression fixtures
are synthetic software probes, not Gaussian execution evidence. During the
2026-10-26 review the official search index was accessible, while direct retrieval
of these two pages returned HTTP 502; no additional output-format guarantee is
inferred from inaccessible page content.

VASP and CP2K text, mapped and streaming entry points share startup/version pairing
and fatal-marker recognition. A VASP `running on ... cores/ranks` banner or a
star-decorated CP2K `PROGRAM STARTED AT` begins the next job; its version header
does not discard intervening errors. Column-zero `ABORT` is a failure. VASP's
normal `aborting loop because EDIFF is reached` message remains an explicit
exception. The periodic streaming parser retains its bounded line/file reads,
per-observation byte/line witnesses, energy units and separate convergence checks.

These are evidence and authorization contracts. Acceptance does not prove that an external DFT engine ran, that a model is scientifically correct, or that industrial parameters can be released.

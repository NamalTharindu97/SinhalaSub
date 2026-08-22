# ADR 0005: Evaluation Corpus Readiness Gate

- Status: Accepted
- Date: 2026-08-22
- Owner: Project team

## Context

The experiment cannot be credible if corpus volume, rights, references, holdout isolation, genre coverage, or challenge annotations are tracked informally. Synthetic protocol fixtures must not be mistaken for a ready evaluation corpus.

## Decision

Use a versioned local corpus manifest and deterministic audit before freezing any experiment.

Every asset records:

- A unique ID, required genre, and development/private-holdout split.
- Source, independent reference, and adjudicated-reference subtitle paths with identical cue IDs and timing.
- Provenance, rights basis, and an existing licence/contributor-agreement evidence file.
- At least two unique pseudonymous annotator IDs, an adjudicator ID, independent annotation files, and a hash-linked adjudication file as defined by ADR 0006.
- Explicit confirmation that the reference was authored independently and that holdout assets remain private.
- Challenge cue IDs and controlled phenomenon tags.

The readiness gate remains fixed at:

- 1,500-2,000 total cues.
- 150-250 unique challenge cues.
- Coverage of all six planned genres and all nine challenge phenomena.
- At least one development asset and one isolated private-holdout asset.
- No duplicate source content across assets.

The audit distinguishes `valid` from `ready`. A small synthetic dry run may be valid, but cannot pass readiness thresholds.

## Consequences

- Corpus expansion cannot silently lower the experiment thresholds.
- Normalized source/reference hashes and a canonical manifest hash support freezing and later audit.
- The tool verifies annotation records and evidence-file presence, not the legal sufficiency or authenticity of a licence; counsel and project owners remain responsible for that review.
- Audit reports retain manifest-relative paths rather than exposing absolute workstation paths.

## Security, Privacy, Legal, And Cost

- Annotator IDs in manifests are pseudonyms; identity/consent/payment records remain separately protected.
- Holdout files remain private and must not enter prompts, provider logs, examples, or public packages.
- Rights evidence must be retained with the corpus and reviewed before real use.
- Auditing is offline and has no provider cost.

## Reversal Trigger

Version the manifest/audit schemas before corpus freeze if counsel, annotators, or the statistical protocol require additional controls. Do not change readiness thresholds after seeing system results.

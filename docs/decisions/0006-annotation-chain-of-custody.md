# ADR 0006: Annotation Chain Of Custody

- Status: Accepted
- Date: 2026-08-22
- Owner: Project team

## Context

Annotator IDs and checkboxes in a corpus manifest do not prove that independent annotations exist, cover the challenge cues, or were used during adjudication. The experiment needs an inspectable chain from the frozen source to each independent judgement and the final adjudicated reference.

## Decision

Require two versioned record types for every corpus asset:

- One annotation record per declared pseudonymous annotator, independently binding corpus ID, asset ID, normalized source hash, challenge cue order, translation, acceptable alternatives, phenomenon tags, and notes.
- One adjudication record binding the same source and cues, the declared adjudicator, and the canonical SHA-256 of every independent annotation record.

The corpus audit rejects missing, duplicate, stale, substituted, incomplete, or identity-mismatched records. Canonical record hashes use sorted compact JSON plus one trailing newline; source hashes continue to use normalized serialized subtitle content.

The local annotation workflow command generates one source-bound template per declared annotator. After independent records are complete, it validates every input before generating an adjudication template with neutral candidate labels; annotator IDs are not copied into that template.

These files record experiment evidence, not annotator identity, consent, contracts, or payment details.

## Consequences

- A manifest assertion alone can no longer satisfy annotation readiness.
- Changing an annotation after adjudication invalidates the hash link and requires explicit re-adjudication.
- The checked-in records are synthetic protocol fixtures and provide no product-quality evidence.
- Real annotations may contain sensitive linguistic judgements and must remain in controlled corpus storage.

## Security, Privacy, Legal, And Cost

- Use pseudonymous annotator IDs and keep the identity mapping outside the corpus.
- Limit private-holdout records to authorised experiment staff and do not include them in evaluator packages.
- Human commissioning, consent, compensation, and legal review remain operational responsibilities outside this validator.
- Validation is local and has no provider cost.

## Reversal Trigger

Version both record schemas before corpus freeze if the approved evaluator protocol requires per-field confidence, disagreement categories, signatures, or a different adjudication model. Do not rewrite frozen records in place.

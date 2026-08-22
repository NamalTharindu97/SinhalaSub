# ADR 0002: Provider-Neutral Translation Contract

- Status: Accepted
- Date: 2026-08-22
- Owner: Project team

## Context

The experiment must compare multiple translation systems without allowing a provider to change cue identity, timing, confirmed names, or factual values. No provider has yet been approved for Sinhala quality, data handling, or cost.

## Decision

Prepare translation requests behind a provider-neutral Python protocol.

- Group cues deterministically by cue limit and time gap, with bounded neighboring cue IDs.
- Replace confirmed names, numbers, dates, currencies, and URLs with typed placeholders before provider dispatch.
- Require one ordered response candidate for every requested cue ID.
- Reject responses that omit, duplicate, add, or reorder cue IDs.
- Reject responses that omit or duplicate protected placeholders.
- Restore protected values only after response validation.
- Use a deterministic echo provider for contract tests; it is not a translation baseline.

## Consequences

- A live provider cannot be connected until its adapter satisfies the same contract tests.
- Timing is absent from provider output and remains owned by the canonical subtitle model.
- Confirmed character names are supplied by the user and matched case-sensitively for now so names such as “Will” do not capture lowercase common words; automated contextual entity detection remains future work.
- Placeholder extraction is deliberately conservative and will expand from rights-clean challenge fixtures.

## Security, Privacy, Legal, And Cost

- No external request is made by this decision.
- Future adapters must document content retention, training use, region, model/version, usage, and cost.
- Only the bounded context block and approved project context may be sent to a provider.

## Reversal Trigger

Revise the contract if the controlled experiment proves that a required provider cannot preserve structured IDs/placeholders, or if protected placeholders materially reduce translation quality and a safer equivalent is validated.

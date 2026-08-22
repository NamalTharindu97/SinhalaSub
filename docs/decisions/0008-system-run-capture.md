# ADR 0008: Frozen System Run Capture

- Status: Accepted
- Date: 2026-08-22
- Owner: Project team

## Context

A valid system freeze identifies what should run, but does not prove that every frozen system produced an output for every corpus asset, preserved subtitle structure, or recorded comparable operational evidence. Blinded packaging must not accept output files that were substituted after metering.

## Decision

Use a versioned system-run capture manifest and deterministic audit between system execution and blinded packaging.

The manifest binds the exact system-freeze hash and contains one record for every corpus-asset/system pair. Each record identifies its output file, timezone-aware generation timestamp, non-negative duration, input/output usage and unit, and USD cost. The audit:

- Requires the complete Cartesian product of frozen systems and corpus assets with no duplicates or extras.
- Parses every output and verifies format, cue IDs, order, and timestamps against the corpus source.
- Hashes normalized outputs and retains source/output hashes in the audit.
- Aggregates duration and cost globally while grouping usage by unit so characters and tokens are never added together.
- Inherits readiness from the system freeze; synthetic captures may be valid but remain not ready.

Blinded packaging audits the capture, selects the records matching its corpus source, verifies each output hash, and places run identity, metering, and hashes only in the confidential key.

## Consequences

- Missing, duplicate, structurally changed, or post-capture substituted outputs cannot enter an experiment package.
- Provider-specific usage units remain explicit and are not presented as directly comparable totals.
- Real execution tooling must write these records after each provider response; this decision does not introduce or approve a provider adapter.
- The synthetic fixture tests the protocol but provides no quality, latency, or cost evidence.

## Security, Privacy, Legal, And Cost

- Capture records contain paths, hashes, identifiers, and aggregate metering; they must not contain provider credentials or raw request logs.
- Output subtitle text remains in controlled files rather than being duplicated into the audit report.
- Provider policy approval and disabled training remain enforced by the linked freeze.
- Auditing is local and incurs no provider cost.

## Reversal Trigger

Version the schema before a real run if approved providers require request IDs, retries, cache accounting, multiple billing units, or additional cost attribution. Do not rewrite a captured run after evaluator access begins.

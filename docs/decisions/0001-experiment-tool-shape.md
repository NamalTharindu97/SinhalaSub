# ADR 0001: Phase 0 Experiment Tool Shape

- Status: Accepted
- Date: 2026-08-22
- Owner: Project team

## Context

The first implementation must prove subtitle structural integrity and support a controlled translation experiment. Building the production web stack now would add authentication, infrastructure, and UI work that does not test the core quality claim.

The development environment currently provides Python 3.9.6. The repository has no existing runtime or dependency constraints.

## Decision

Build the Phase 0 experiment as a Python 3.9+ standard-library package and command-line tool under `experiment/`.

The first slice will:

- Parse SRT and WebVTT into one canonical cue model.
- Serialize the canonical model back to its source format.
- Preserve cue identity, count, ordering, timestamps, text, and WebVTT cue settings.
- Normalize working text to Unicode NFC.
- Fail clearly on malformed or unsupported input.
- Use synthetic fixtures and `unittest` so no third-party dependency is required.

## Consequences

- The experiment can run locally and in future CI without provider credentials.
- Python is selected only for the experiment harness; this ADR does not approve the production Next.js/FastAPI/PostgreSQL/Redis candidates.
- Normalized round-trip output is expected to be structurally equivalent, not byte-for-byte identical.
- Advanced WebVTT blocks such as `STYLE` and `REGION` remain unsupported until fixtures and product requirements justify them.

## Security, Privacy, Legal, And Cost

- Automated fixtures must be synthetic, commissioned, licensed, or public-domain.
- The parser performs no network access and sends no content to an AI provider.
- File and cue limits will be added before processing untrusted pilot uploads.
- This slice creates no inference or infrastructure cost.

## Reversal Trigger

Replace or split this tool only if the experiment requires capabilities Python cannot provide reproducibly, or if measured parser compatibility requires an established library with acceptable licensing.

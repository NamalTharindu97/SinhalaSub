# System Architecture

## Status

This is the proposed MVP architecture from the research report, not an implemented or final stack. Confirm it through an architecture decision record before scaffolding. Optimize for a small team and replaceable AI providers, not premature microservices.

## Proposed Shape

- Browser editor: Next.js with TypeScript.
- Application/API: Python FastAPI modular monolith.
- Background work: worker processes backed by Redis-compatible queueing.
- Transactional data: PostgreSQL; enable vector search only when approved memory retrieval proves useful.
- File data: encrypted object storage with short-lived signed URLs and lifecycle deletion.
- External AI and metadata: provider adapters selected by project policy.

The initial deployable units may be web, API, worker, database, queue, and object store, while business logic remains organized by domain inside one backend codebase.

## Domain Boundaries

| Domain | Responsibility |
| --- | --- |
| Identity and organisations | Authentication, membership, roles, tenant isolation |
| Projects and rights | Media identity, rights declaration, style, privacy and retention policy |
| Subtitle ingestion | Upload validation, parsing, normalization, canonical cues, source hash |
| Profile and terminology | Characters, aliases, relationships, glossary, knowledge provenance |
| Translation | Block construction, provider routing, prompts, retries, structured drafts |
| Quality | Deterministic invariants, semantic/context checks, warning severity, scoring |
| Review | Edits, approval, alternatives, comments, version history, audit |
| Export and deletion | Format reconstruction, final validation, download, lifecycle purge |
| Evaluation and usage | Prompt/model versions, latency, cost, benchmark and quality telemetry |

## End-To-End Data Flow

1. The API authorizes a project and issues a short-lived upload target.
2. Upload processing validates type, size, malware status, encoding, and parseability.
3. The parser stores an immutable original and canonical cue records with stable IDs and timestamps.
4. The user confirms media identity, rights, style, entities, and glossary.
5. The orchestrator creates deterministic context blocks and an idempotent job key.
6. Workers send only policy-allowed minimum context to selected providers.
7. Provider responses are schema-validated and rejected if cue IDs or protected invariants are missing.
8. Deterministic QA runs first; model-assisted checks run selectively based on risk and policy.
9. The editor presents drafts and warnings; every accepted edit creates a version and audit event.
10. Export reconstructs the requested format from canonical timestamps and approved text, then runs blocking integrity validation.
11. Deletion removes active copies and queues object, cache, and derived-record cleanup under the documented retention policy.

## Hard Technical Invariants

- Canonical timestamps are immutable in translation-only mode.
- Provider payloads contain cue IDs and text/context, never authority to mutate timing.
- Export cue count and timing must match canonical source exactly unless a future explicit retiming mode creates a separate version.
- All mutable user-facing translation data is versioned.
- Jobs are idempotent across project, source hash, block, prompt version, model, glossary version, and profile version.
- A superseded profile/glossary version cannot silently update current approved text.
- Tenant authorization is checked in the application and reinforced in storage/database policy.
- Full subtitle text is excluded from routine logs and traces.

## Translation Job Lifecycle

`queued -> preparing -> translating -> validating -> completed`

Terminal alternatives: `failed`, `cancelled`, `superseded`.

- Retry transient rate-limit, timeout, and provider-availability failures with bounded backoff.
- Do not retry schema, invariant, policy, or content-size failures without a code/config change.
- Route exhausted transient failures and invalid outputs to dead-letter review.
- Allow safe restart from completed blocks without duplicating translations or usage charges.

## Provider Boundary

Each translation/refinement adapter must expose:

- Capability and language declaration.
- Structured request/response schema.
- Timeout, retry, and concurrency policy.
- Usage and cost normalization.
- Data retention/training policy metadata.
- Provider/model/version identifiers.
- Health status and circuit-breaker behavior.

Business workflows must not depend on provider-specific response shapes.

## Deployment Stages

### Prototype

- Local development, synthetic/licensed fixtures, CLI or minimal internal UI.
- One baseline provider and one contextual provider path.
- No customer content and no production identity complexity.

### Pilot MVP

- Managed cloud services, private projects, encrypted storage, queue, backups, deletion workflows, audit events, and environment separation.
- Limited providers, formats, file sizes, concurrency, and invite-only users.

### Later

- Local media playback without media upload.
- Organisation review, API access, private deployment, and vector retrieval only after measured demand.
- Split services only for independently scaling or security-isolated workloads.

## Architecture Review Checklist

- Can a malformed/provider response mutate timing or approved text?
- Can every project read/write path prove organisation membership?
- Can source and derived content be deleted under the stated policy?
- Can a provider be replaced without changing core records or editor behavior?
- Can a failed job resume without duplicate drafts or billing?
- Can an audit explain which source, glossary, prompt, model, and human edit produced an export?
- Can logs and support tooling operate without exposing complete confidential subtitles?

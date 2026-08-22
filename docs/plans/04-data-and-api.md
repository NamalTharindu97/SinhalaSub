# Data And API Plan

## Data Principles

- Use stable opaque IDs; cue indexes are display order, not identity.
- Scope every customer-owned record to an organisation/project and enforce isolation on every query.
- Separate immutable source facts from mutable drafts, approvals, and exports.
- Record provenance for generated text, retrieved knowledge, and user-approved decisions.
- Store timestamps as integer milliseconds in canonical records.
- Store working Sinhala as UTF-8 NFC and measure visual limits by extended grapheme clusters.
- Keep project memory separate from any future consented global-learning dataset.

## Core Records

| Record | Essential fields and rules |
| --- | --- |
| User | Email/identity reference, locale, preferences, consent timestamps |
| Organisation | Name, plan placeholder, provider policy, retention policy |
| Membership | User, organisation, role; unique per pair |
| Project | Organisation, media identity, style profile, rights declaration/version, privacy policy, status |
| Subtitle file | Project, format, detected encoding, source hash, object key, cue count, retention deadline |
| Cue | File, stable ID, display index, start/end milliseconds, source text, format payload; source/timing immutable |
| Character | Project, canonical name, approved Sinhala name, optional metadata, notes |
| Alias/relationship | Character mapping and optional speaker relationship evidence |
| Glossary term | Scope, source term, target term, decision type, approval and version |
| Knowledge source | Project, source type/URL, licence, retrieval date, media/episode scope, confidence |
| Context block | Ordered cue IDs, grouping algorithm/version, profile/glossary versions |
| Translation job | Idempotency key, policy, status, progress, provider usage, failure category |
| Translation version | Cue, source type, text, provider/model/prompt/profile/glossary versions, author, timestamp |
| Alternative | Translation version, text, reason code, score metadata |
| Warning | Cue/project, type, severity, evidence, checker version, resolution status |
| Score | Cue, semantic/entity/terminology/context/readability/formatting components, calibration version |
| Approval/comment | Cue, actor, version, state/body and timestamps |
| Translation memory | Explicit scope, source signature, context, approved target, provenance, deletion link |
| Export | Project, source file/version set, format, validation report, object key, creator, expiry |
| Audit event | Organisation, actor, action, object reference, redacted metadata, timestamp |

## Versioning Rules

- Changing source files creates a new file/cue set; it does not mutate prior cues.
- Changing glossary, profile, or entity decisions creates a version used by later jobs.
- Regeneration creates a candidate translation version and never auto-approves it.
- Approval references the exact translation version accepted.
- An export records the exact approved versions, profile, glossary, and validation result.
- Project deletion must identify and purge all object keys, memories, exports, and queued payloads derived from that project.

## Project State

`draft -> uploaded -> configuring -> ready -> translating -> reviewing -> export_ready -> archived`

- A project cannot become `ready` until rights declaration and source validation pass.
- Translation requires confirmed project settings and at least disposition of ambiguous high-risk entities.
- `export_ready` requires final QA against the current approved versions.
- Deletion is a separate lifecycle operation and must not be represented as ordinary archive.

## API Conventions

- Prefix HTTP APIs with `/v1` and publish an OpenAPI contract from the backend.
- Use organisation/project authorization on every nested and direct-ID endpoint.
- Require idempotency keys for job creation, exports, and retry-sensitive writes.
- Use cursor pagination for cue/warning/audit collections.
- Return stable machine error codes plus actionable human messages.
- Use optimistic concurrency/version fields for cue edits and glossary/profile changes.
- Keep provider names, prompts, and internal chain details out of public responses; expose concise provenance and warning codes.

## Proposed HTTP Surface

### Projects And Files

- `POST /v1/projects`
- `GET /v1/projects/{project_id}`
- `PATCH /v1/projects/{project_id}`
- `DELETE /v1/projects/{project_id}`
- `POST /v1/projects/{project_id}/upload-intents`
- `POST /v1/projects/{project_id}/files/{file_id}:ingest`
- `GET /v1/projects/{project_id}/files/{file_id}/validation`

### Profile, Entities, And Glossary

- `PUT /v1/projects/{project_id}/profile`
- `POST /v1/projects/{project_id}/entities:detect`
- `GET /v1/projects/{project_id}/entities`
- `PATCH /v1/projects/{project_id}/entities/{entity_id}`
- `GET /v1/projects/{project_id}/glossary`
- `POST /v1/projects/{project_id}/glossary`
- `PATCH /v1/projects/{project_id}/glossary/{term_id}`
- `POST /v1/projects/{project_id}/glossary:preview-replacement`

### Translation And Review

- `POST /v1/projects/{project_id}/translation-jobs`
- `GET /v1/jobs/{job_id}`
- `POST /v1/jobs/{job_id}:cancel`
- `GET /v1/projects/{project_id}/cues`
- `GET /v1/cues/{cue_id}`
- `POST /v1/cues/{cue_id}/translation-candidates`
- `PATCH /v1/cues/{cue_id}/translations/{version_id}`
- `POST /v1/cues/{cue_id}/translations/{version_id}:approve`
- `POST /v1/cues/{cue_id}/comments`

### QA, Export, And Audit

- `POST /v1/projects/{project_id}/qa-jobs`
- `GET /v1/projects/{project_id}/warnings`
- `POST /v1/warnings/{warning_id}:resolve`
- `POST /v1/projects/{project_id}/exports`
- `GET /v1/exports/{export_id}`
- `POST /v1/exports/{export_id}/download-intents`
- `GET /v1/projects/{project_id}/audit-events`

## Event And Worker Contracts

All queue messages include schema version, event/job ID, project and organisation IDs, trace correlation, requested policy, and creation/expiry timestamps. Pass object references or record IDs instead of full subtitle content where practical.

Required job categories:

- Ingest and parse subtitle.
- Detect entities.
- Build context blocks.
- Translate/refine a block.
- Run deterministic QA.
- Run selective model-assisted QA.
- Build and validate export.
- Delete project-derived data.

## Contract-First Milestones

1. Define canonical cue and subtitle round-trip schemas.
2. Define provider-neutral translation input/output schemas.
3. Define warnings, severity, scores, and export-blocking rules.
4. Define project/profile/glossary version and job idempotency semantics.
5. Generate OpenAPI and typed client only after these contracts pass fixture tests.

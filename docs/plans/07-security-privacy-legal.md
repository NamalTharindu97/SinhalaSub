# Security, Privacy, And Legal Plan

## Operating Boundary

The service processes private subtitle files for users who own or are authorised to translate the content. It does not discover, host, or distribute a public subtitle catalogue. Translation and training rights are not inferred from public availability.

This plan is engineering guidance, not legal advice. Qualified Sri Lankan and contract counsel must approve the external-pilot model.

## Pre-Pilot Legal Deliverables

- Rights declaration and Terms of Service covering authorised use and prohibited uploads.
- Privacy notice covering purposes, retention, AI providers, cross-border processing, deletion, and contact rights.
- Customer/output ownership and narrow service-processing licence.
- Separate terms for project memory and optional organisation/user reuse.
- Global-learning consent that is separate, explicit, revocable where required, and off by default.
- Takedown, counter-notice/appeal, and repeat-infringer procedures.
- Provider and subprocessor register with contracts/data terms.
- Metadata source licence register with attribution, caching, AI-use, and deletion constraints.

## Data Classification

| Class | Examples | Handling |
| --- | --- | --- |
| Restricted content | Uploaded subtitles, unreleased scripts, translations, comments | Encrypt, tenant-isolate, minimize provider transfer, no routine logs |
| Personal/confidential | Accounts, organisation membership, audit actor, project metadata | Least privilege, purpose limitation, retention schedule |
| Derived sensitive | Embeddings, translation memory, prompt payloads, exports | Same classification and deletion link as source project |
| Operational metadata | Usage counts, latency, redacted errors | No subtitle text; bounded retention |
| Public product data | Published docs and public marketing | Standard integrity controls |

## Minimum Security Controls

### Identity And Authorization

- Managed authentication for MVP; do not build password storage from scratch.
- Organisation roles with deny-by-default object access.
- Application authorization on every operation plus database/storage isolation controls.
- MFA for production administrators and protected support access.
- Time-bound, audited support impersonation only if later required.

### Upload And Storage

- TLS, HSTS, short-lived signed upload/download URLs, strict type/size limits, and malware scanning.
- Reject archives and executable content; enforce parser resource/decompression limits.
- Encrypt database, object storage, queue payloads where supported, and backups.
- Use separate credentials and data stores for development, test, staging, and production.
- Never use customer production content in tests or local development.

### Secrets And Providers

- Store credentials in managed secret/KMS tooling; never browser code, repository, prompt, or logs.
- Use scoped service identities, rotation, egress controls where practical, and provider circuit breakers.
- Document provider data retention/training controls and enforce project policy before dispatch.
- Minimize context sent and redact unrelated identifiers.

### Application And Operations

- Validate all model/provider output as untrusted data before rendering or storage transitions.
- Escape subtitle and metadata content; use a restrictive content security policy.
- Apply rate, quota, concurrency, and object-size controls by tenant.
- Log security/audit actions without full subtitle text.
- Run dependency, secret, static analysis, and production configuration checks in CI once a toolchain exists.
- Complete threat modeling and remediate critical/high findings before external pilot.

## Retention And Deletion

- Define source, export, job payload, logs, backup, and memory retention separately.
- Offer short default source retention and test a zero-retention/export-and-delete mode.
- A deletion request immediately revokes access, cancels pending jobs, and queues primary/derived data purge.
- Show deletion progress and document unavoidable encrypted-backup expiry.
- Ensure project-derived embeddings, caches, exports, and memories share a deletion lineage.
- Test deletion end to end; a successful API response alone is insufficient.

## Audit Events

Capture rights acceptance, uploads, profile/glossary changes, job/provider selection, approvals, warning resolutions, exports/downloads, retention changes, deletion, membership changes, and privileged support/admin access.

Audit metadata should identify actor/action/object/result/version without storing complete subtitle text.

## Metadata And Dataset Rules

- User-approved project data outranks all external sources.
- Use official/licensed sources and Wikidata suggestions only after source-specific terms are recorded.
- Treat Wikipedia reuse/attribution and share-alike obligations explicitly.
- Do not ingest TMDb into AI/RAG by default without an appropriate agreement.
- Avoid IMDb/scraped sources and unlicensed scripts/subtitles.
- Scope facts by title/year/season/episode and prevent future-episode spoiler retrieval by default.
- Quarantine any dataset whose line-level provenance and intended-use rights cannot be established.

## Threat Model Priorities

- Cross-tenant project access through direct IDs, exports, signed URLs, search, or queue payloads.
- Confidential subtitle leakage to providers, logs, support tooling, telemetry, or backups.
- Prompt injection in subtitle/metadata text changing system behavior or exfiltrating context.
- Malformed SRT/WebVTT causing parser exhaustion, stored injection, or export corruption.
- Job replay causing duplicate provider spend or overwriting newer edits.
- Stale signed URLs and incomplete deletion.
- Unauthorised dataset reuse or memory leakage across projects/organisations.
- Compromised provider keys or CI/deployment credentials.

## External Pilot Gate

- Counsel-reviewed terms, privacy, rights, and takedown process are published.
- Provider/subprocessor and metadata licence reviews are recorded.
- Threat model is reviewed and no critical findings remain.
- Tenant isolation, signed URL expiry, backup restore, and deletion are tested.
- Incident contacts, containment steps, evidence preservation, notification assessment, and credential rotation are rehearsed.

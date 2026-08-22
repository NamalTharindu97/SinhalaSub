# Decisions And Open Questions

## Confirmed Product Decisions

| Decision | Reason |
| --- | --- |
| Authorised-use private workspace | Translation is rights-sensitive; initial customers must control the content |
| Human-in-the-loop publication | Sinhala context, tone, idioms, and culture cannot be safely automated end to end |
| SRT and WebVTT only for MVP | Tests the core value without media storage/transcoding risk |
| Preserve source timing by default | Timestamp safety is a key user outcome and deterministic invariant |
| No public subtitle catalogue | Not needed to prove value and creates substantial rights/moderation risk |
| No unlicensed scraping/training | Public availability does not establish training or redistribution rights |
| Project memory by default | Limits leakage and aligns learning with user-approved context |
| Global training off by default | Requires separate consent and rights |
| Validation gate before SaaS build | Paying demand and measurable quality/time improvement remain unproven |

## Proposed Technical Decisions Requiring ADRs

Do not treat these as installed technology until the repository contains an accepted ADR and manifests.

| Candidate | Decision to make | Evidence needed |
| --- | --- | --- |
| Next.js + TypeScript | Browser editor framework and deployment model | Editor prototype, team skill, accessibility, streaming/job needs |
| FastAPI + Python | API/AI modular monolith | NLP libraries, async jobs, schema/client generation, operational comfort |
| PostgreSQL | Transactional store and isolation strategy | Data model, tenant policy, migration/backup tooling |
| Redis-compatible queue | Job semantics/library | Idempotency, cancellation, retries, observability, hosting |
| Object storage | Upload/export lifecycle | Signed URLs, malware flow, deletion, region and cost |
| pgvector | Whether semantic memory needs vectors | Retrieval benchmark against simpler text/signature matching |
| Auth provider | Managed identity and organisation support | Sri Lankan availability, cost, exportability, MFA, privacy |
| AI providers | Baseline/refinement routes | Sinhala benchmark, data terms, cost, latency, availability |
| Cloud/region | Pilot deployment | PDPA/legal review, provider availability, latency, cost |

## Product Questions For Phase 0

- Which initial segment has both authorised content and repeat translation volume?
- Will viable users upload subtitle-only files to cloud processing, and under what retention/provider controls?
- Which Sinhala style profiles and profanity policies match real workflows?
- Which errors cost the most expert time and which warning explanations are trusted?
- Are line-density defaults acceptable across films, education, YouTube, and television?
- What is the actual baseline editing time and correction distribution by genre?
- Does local video playback without upload materially improve review speed?
- Which payment unit best matches value: project, media minute, cue, subscription, or team plan?

## Technical Questions Before Scaffolding

- Is the first experiment best implemented as a reproducible CLI/internal web tool rather than the proposed production stack?
- Which parser/serializer libraries preserve all required SRT/WebVTT details, and what must be custom?
- How are cue tags, style payloads, comments, and non-dialogue metadata represented canonically?
- Which queue supports required cancellation/idempotency semantics with least operational overhead?
- Can provider payload retention/training be disabled contractually for pilot content?
- What source-file and export retention defaults pass legal review and user interviews?
- Is database row-level security required for the pilot or used as defense in depth after application checks?
- What exact content can operational telemetry retain without undermining confidentiality?

## Deferred Questions

- Desktop/local inference and hybrid synchronization.
- Organisation memory and cross-project terminology governance.
- Billing, API quotas, SSO, SLA, private deployment, and data residency.
- Licensed movie/episode metadata retrieval and attribution UX.
- ASR, diarisation, automatic scenes, waveform, and video upload.
- Fine-tuning/distillation and multilingual expansion.

## ADR Process

Create architecture decisions under `docs/decisions/` using `NNNN-short-title.md` when implementation starts. Each ADR records:

- Status and date.
- Decision owner.
- Problem and constraints.
- Options considered with evidence.
- Decision and consequences.
- Security/privacy/legal/cost impact.
- Validation or reversal trigger.

First expected ADRs:

1. Experiment tool shape and reproducibility.
2. Canonical subtitle representation and parser strategy.
3. Production web/API/worker stack after the experiment gate.
4. Authentication and tenant-isolation model.
5. Queue and job-idempotency implementation.
6. Pilot AI providers and data-processing policy.
7. Retention, deletion, and backup behavior.

## Decision Log

| Date | Decision | Evidence/owner |
| --- | --- | --- |
| 2026-08-22 | Adopt the research report's validation-gated, authorised-use, human-in-the-loop direction as the planning baseline | Repository planning pass; confirm with product owner before Phase 0 execution |

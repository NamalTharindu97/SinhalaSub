# SinhalaSub Delivery Plan

## Purpose

This folder turns the product research in `../AI_Powered_English_to_Sinhala_Subtitle_Research_Report.docx` into an executable delivery plan. The report remains the evidence base; these files define the current build sequence, boundaries, and acceptance gates.

## Product Decision

Build a private, authorised-use assistant that translates English SRT/WebVTT subtitles into reviewable Sinhala drafts. Humans remain responsible for publication. The product must prove that context, protected entities, glossary enforcement, and risk-ranked review reduce expert editing time without increasing critical errors.

Do not build the full SaaS before the Phase 0 experiment passes. A technically complete editor is not product validation.

## Plan Index

| File | Owns |
| --- | --- |
| [`01-product-scope.md`](01-product-scope.md) | Users, outcomes, MVP requirements, exclusions, success metrics |
| [`02-validation-plan.md`](02-validation-plan.md) | Discovery, legal checks, benchmark experiment, go/no-go rules |
| [`03-system-architecture.md`](03-system-architecture.md) | Proposed boundaries, data flow, invariants, deployment shape |
| [`04-data-and-api.md`](04-data-and-api.md) | Core records, state transitions, API contracts, job semantics |
| [`05-ai-and-quality.md`](05-ai-and-quality.md) | Translation pipeline, provider abstraction, QA, evaluation data |
| [`06-review-experience.md`](06-review-experience.md) | User journeys, editor behavior, accessibility, trust controls |
| [`07-security-privacy-legal.md`](07-security-privacy-legal.md) | Authorised use, retention, tenant isolation, provider and data controls |
| [`08-testing-and-evaluation.md`](08-testing-and-evaluation.md) | Test layers, fixtures, quality metrics, release gates |
| [`09-delivery-roadmap.md`](09-delivery-roadmap.md) | Work packages, dependencies, milestones, definition of done |
| [`10-operations-and-cost.md`](10-operations-and-cost.md) | Environments, observability, quotas, cost and incident controls |
| [`11-decisions-and-questions.md`](11-decisions-and-questions.md) | Confirmed decisions, assumptions, unresolved decisions, ADR process |

## Delivery Order

1. Complete Phase 0 interviews, legal review, benchmark corpus, and experiment protocol.
2. Build the smallest translation prototype needed to compare baseline and contextual pipelines.
3. Run the blinded experiment and apply the go/no-go thresholds.
4. If the gate passes, build the pilot-ready web MVP in vertical slices.
5. Run authorised pilots before adding collaboration, media processing, billing, or enterprise deployment.

## Current Implementation Status

- Phase 1 Slice 1 is implemented in the local Python harness: SRT/WebVTT integrity, normalized export, tests, and GUI.
- Phase 1 Slice 2 has provider-neutral context blocks, a versioned character/alias/glossary/style profile, deterministic glossary enforcement, and protected-value contracts, but no live baseline or AI adapter.
- Phase 1 Slice 3 has deterministic QA, versioned local review reports, reproducible blinded packaging, controlled critical-error categories, confidential rubric/preference analysis stratified by genre and challenge phenomenon, and paired baseline/contextual editing-time analysis with a deterministic bootstrap interval; real frozen system outputs and human evaluator protocol approval remain outstanding.
- Provider-neutral system-freeze auditing pins the three experiment roles, corpus/instruction hashes, model and adapter versions, policy review, seed, and rubric; only a synthetic not-ready record exists because no live provider or policy has been approved.
- System-run auditing requires every frozen system/corpus pair, verifies output structure and hashes, captures latency/usage/cost, and binds blinded packages to those outputs; current evidence remains synthetic and not ready.
- The Phase 0 decision gate now applies the frozen go/narrow/local-pivot/stop thresholds to hash-bound evidence, but the repository dry run is explicitly `not-authorized`; interviews, legal approval, real corpus/runs, translators, viewers, and independent review remain external blockers.
- The corpus workflow now generates source-bound independent annotation templates and neutral-label, hash-linked adjudication templates, and the readiness gate verifies completed records; the repository still contains only a valid three-cue synthetic dry run, so the rights-clean 1,500-2,000 cue corpus, private holdout, and real expert annotations have not been created.
- Phase 0 discovery, rights-clean corpus creation, legal review, and the controlled experiment remain required before the product gate.

## Non-Negotiable Invariants

- Preserve cue count, cue identity, and timestamps in translation-only mode.
- Never let an AI provider edit timestamps or silently overwrite approved text.
- Require a rights declaration before processing uploaded content.
- Keep projects private; do not provide a public subtitle catalogue.
- Use only commissioned, licensed, public-domain, or explicitly opted-in data for evaluation or learning.
- Keep global model training disabled by default and separate from project memory.
- Treat humour, idioms, tone, profanity, cultural adaptation, and low-confidence meaning as human-review work.

## Plan Maintenance

- Record architecture-changing decisions in `11-decisions-and-questions.md` before implementation diverges from this plan.
- Replace assumptions with measured results after Phase 0 and each pilot.
- Update acceptance criteria before expanding scope; do not mark a gate complete by lowering a metric after results are known.

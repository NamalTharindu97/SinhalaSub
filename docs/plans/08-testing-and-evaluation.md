# Testing And Evaluation Plan

## Verification Strategy

Correctness has four separate dimensions: subtitle structure, application behavior, security/privacy, and Sinhala translation quality. A green unit-test suite cannot substitute for blinded human evaluation.

## Test Data Policy

- Default automated fixtures are synthetic, commissioned, or verified public-domain/licensed.
- Include English, Sinhala, mixed-language, Unicode combining sequences, entities, numbers, dates, currencies, URLs, music cues, dual speakers, tags, and malformed samples.
- Store fixture provenance and licence beside the corpus manifest.
- Never copy customer subtitles into tests, snapshots, issue reports, or developer machines.
- Keep the private quality hold-out corpus separate from prompt development fixtures.

## Test Layers

### Parser And Export

- Valid and malformed SRT/WebVTT, BOM/encoding cases, CRLF/LF, tags, multiline cues, overlaps, gaps, and unusual cue identifiers.
- Property/round-trip tests proving stable cue count, order, text mapping, and exact canonical timestamps.
- Resource-limit tests for large cues/files and adversarial parser input.
- NFC and extended-grapheme handling for Sinhala.
- Export tests in representative browsers, VLC-like players, mobile devices, and target workflows.

### Domain And API

- Project state transitions and rights-declaration gate.
- Organisation/role authorization for every direct and nested resource path.
- Profile, glossary, entity, translation, approval, warning, export, retention, and deletion versioning.
- Optimistic concurrency and stale-edit rejection.
- Idempotency for jobs/exports and pagination/error contracts.
- OpenAPI compatibility between backend and generated frontend client.

### Worker And Provider

- Contract tests shared by every provider adapter.
- Timeout, rate limit, retry, circuit breaker, cancellation, dead-letter, and partial-block recovery.
- Duplicate delivery and restart tests proving no duplicate candidates or charges where controllable.
- Invalid JSON/schema, omitted/extra cue IDs, protected-token loss, and provider-policy rejection.
- Fake providers for deterministic CI; live provider tests run separately with quotas and no secrets in forked/untrusted jobs.

### Quality Engine

- Golden cases for names/common words, numbers, dates, currency, negation, glossary variants, English residue, and grapheme limits.
- Severity and export-blocking behavior for every warning code.
- Regression cases for omissions, additions, reversals, idioms, pronouns, tone, and context.
- Calibration tests comparing review priority against adjudicated human labels.
- Prompt/model regression suite with frozen inputs, versions, budget, and critical-error deltas.

### Web Experience

- Core journey E2E: upload, configure, translate, review, approve, QA, export, delete.
- Keyboard navigation, undo/version recovery, filter state, autosave conflicts, job progress, and failed-job recovery.
- Accessibility automation plus manual keyboard/screen-reader checks.
- Responsive and Sinhala rendering tests at representative widths and zoom levels.
- No silent text loss when regeneration, stale responses, or glossary changes race with edits.

### Security And Privacy

- Cross-tenant access matrix for records, search/filter results, jobs, exports, and signed URLs.
- Upload type/size/malware/parser limit tests.
- XSS/content rendering, CSRF/session, rate/quota, prompt-injection boundary, and secret/log redaction tests.
- Project deletion verification across database, queue, object storage, cache, memory, and later backup expiry.
- Backup restore and incident-response exercise before pilot.

## CI Stages

Exact commands depend on the toolchain selected during scaffolding. Preserve this order when scripts are defined:

1. Format/config validation and generated-contract drift.
2. Lint and static analysis.
3. Frontend/backend type checks.
4. Fast unit and property tests.
5. Integration tests with isolated database/queue/object-store services.
6. Web E2E and accessibility smoke tests.
7. Security/dependency/secret scans.
8. Build deployable artifacts.

Live AI-provider and full human-quality evaluations are scheduled/release workflows, not required for every pull request.

## Quality Evaluation

### Automated Signals

- chrF/BLEU for surface regression only.
- COMET or multilingual quality estimation only after Sinhala/domain calibration.
- Entity accuracy, glossary adherence, critical invariant errors, readability profile, cue/timestamp integrity, latency, and cost.

### Human Signals

- Accuracy, fluency, context, tone/voice, terminology, readability, cultural appropriateness, and formatting on a 1-5 anchored rubric.
- Publish-ready editing time, keystrokes, changed cues, critical errors, and viewer preference/comprehension.
- Multiple raters, blinded system identity, paired scenes, adjudication, confidence intervals, and inter-rater agreement.

## Pull Request Gate

- Relevant unit/integration/E2E tests pass.
- Contract and generated artifacts are current.
- No new critical/high security finding.
- Parser/export changes pass round-trip corpus tests.
- Provider/prompt/QA changes state measured regression impact and do not worsen critical-error gates.
- User-facing workflow changes include keyboard/accessibility verification.

## Release Gate

- Migration, deployment, rollback, backup/restore, and deletion checks pass in staging.
- Smoke test completes the core journey with synthetic/licensed content.
- Cue/timestamp integrity remains 100%.
- Known critical translation failures are documented and guarded by required review/blocking behavior.
- Observability and budget alerts exist for new providers/jobs.
- Pilot release has no unresolved critical security issue and explicit product/legal approval.

# Delivery Roadmap

## Planning Basis

The report estimates 12-16 weeks for a focused MVP with a full-stack engineer, AI/NLP engineer, and part-time Sinhala subtitle expert. Treat dates as capacity-dependent; exit criteria, not calendar time, control progression.

## Phase 0: Validate Before Product Build

Estimated 4-6 weeks.

### Work Packages

- Conduct creator, professional, and organisation interviews and workflow observations.
- Obtain copyright/privacy/provider legal review.
- Commission and annotate the rights-clean benchmark corpus.
- Select and freeze generic MT and isolated-line baselines.
- Prototype project setup and review interactions with no production backend.
- Define critical-error rubric, telemetry protocol, and analysis method.
- Recruit evaluators, viewers, and pilot candidates.

### Exit

- Discovery criteria in `02-validation-plan.md` pass.
- Experiment corpus/protocol and legal rights are auditable.
- At least five translators can use the prototype workflow.
- Pilot interest is documented.
- A written decision authorizes only the prototype scope needed for the experiment.

## Phase 1: Translation Experiment Prototype

Estimated 4-6 weeks.

### Slice 1: Subtitle Integrity

- Canonical SRT/WebVTT parser and serializer.
- UTF-8/NFC and extended-grapheme utility.
- Round-trip fixture suite with 100% cue/timestamp integrity.
- CLI/internal API to inspect validation and canonical JSON.

### Slice 2: Context And Entity Pipeline

- Protected invariant extraction and restoration.
- Character/alias/glossary input fixture format.
- Deterministic context grouping.
- Baseline and context-aware provider adapters with structured output.

### Slice 3: QA And Experiment Capture

- Deterministic warning engine.
- Minimal candidate review/edit/approve interface or experiment tool.
- Version, latency, usage, cost, edit-time, keystroke, and correction capture.
- Frozen experiment runner and blinded output packaging.

### Exit

- Three systems run reproducibly over the evaluation corpus.
- No provider output can change canonical timing.
- Experiment telemetry and blinded evaluation procedure are verified in a dry run.
- Controlled experiment is completed and independently reviewed.

## Decision Gate

Apply the outcomes in `02-validation-plan.md`:

- **Go:** continue to Phase 2.
- **Narrow:** replace Phase 2 scope with entity/glossary/QA or plugin workflow.
- **Local pivot:** design a local/hybrid proof before SaaS work.
- **Stop:** archive results and do not add features to compensate for failed value.

## Phase 2: Pilot-Ready Web MVP

Estimated 8-12 weeks after a Go decision.

### Slice 1: Private Project Foundation

- Select stack through ADR and scaffold web/API/worker boundaries.
- Authentication, organisations, roles, tenant isolation, and environments.
- Project creation, rights declaration, upload, ingest, validation, save/resume, and deletion.
- Encrypted storage, signed URLs, retention policy, audit events, and operational telemetry.

Exit: an invited user can privately upload, inspect, and delete a subtitle; isolation/deletion tests pass.

### Slice 2: Translation Preparation

- Media/style profile.
- Character, alias, optional relationship, glossary, and ambiguous entity workflows.
- Context block preview and versioned readiness state.

Exit: the user can resolve required context and generate an immutable translation-job input.

### Slice 3: Translation And Job Control

- Queue, idempotent jobs, progress, cancellation, bounded retry, provider policy, and usage tracking.
- Baseline/context/refinement paths selected from experiment evidence.
- Candidate storage and stale profile/glossary handling.

Exit: supported files complete reliably under failure/retry tests without duplicate or silent overwrite.

### Slice 4: Risk-Ranked Review

- Side-by-side editor, adjacent context, warnings, scores, alternatives, keyboard workflow, filters, comments, approval, and history.
- Deterministic QA plus only model-assisted checks justified by experiment results.
- Project-scoped approved memory.

Exit: pilot translators complete the usability tasks in `06-review-experience.md` with no data loss.

### Slice 5: Safe Export And Pilot Operations

- Final QA, blocking conditions, exact preview, SRT/WebVTT export, validation report, expiring download.
- Support/admin controls, quotas, alerts, backup/restore, incident and deletion runbooks.
- Legal notices, takedown flow, provider/subprocessor register, and pilot onboarding.

Exit: release criteria in `08-testing-and-evaluation.md` and `07-security-privacy-legal.md` pass.

## Phase 3: Authorised Pilot

Run until repeat behavior and operational evidence are credible; do not time-box success into existence.

- Onboard 10-15 creators and three authorised organisations.
- Require multiple real projects where feasible.
- Measure activation, completion, editing time, corrections, critical errors, second-project use, support, provider cost, and deletion/privacy concerns.
- Review metrics weekly without changing benchmark thresholds after observing results.
- Decide whether the next investment is editor UX, quality, local mode, collaboration, or B2B security.

Exit: paid-pilot gate and 70% repeat/continued-use target pass, with no unresolved critical legal/security issue.

## Later Phases

Only after pilot evidence:

- Licensed metadata and provenance-aware retrieval.
- Series/organisation memory and reviewer collaboration.
- Local media playback, then optional local/hybrid text processing.
- API, billing, SLA, SSO, private deployment, and editor integrations.
- Audio/video intelligence or multilingual expansion only under separate value, rights, privacy, and cost validation.

## Team Responsibilities

| Role | Accountable for |
| --- | --- |
| Product/research lead | Interviews, priorities, experiment integrity, pilots, commercial validation |
| Full-stack engineer | Web, API, data, auth, deployment, product observability |
| AI/NLP engineer | Providers, prompts, entity protection, QA, evaluation tooling |
| Sinhala subtitle expert | Style, corpus, annotations, adjudication, acceptance review |
| UX designer/researcher | Editor prototype, keyboard/accessibility workflow, usability testing |
| Legal/security advisers | Rights/privacy model, threat review, pilot approval |

## Definition Of Done For Any Slice

- User outcome and measurable acceptance criteria are met.
- Automated tests and required human evaluation pass.
- Authorization, retention, deletion, audit, and provider impacts are reviewed.
- Operational metrics, failure behavior, and rollback are defined.
- Documentation and decision records reflect the implemented behavior.
- No excluded MVP feature has been smuggled in as an implementation dependency.

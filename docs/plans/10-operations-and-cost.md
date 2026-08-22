# Operations And Cost Plan

## Environments

- Local: synthetic/licensed fixtures and fake providers by default.
- CI: ephemeral isolated services; no production credentials or customer content.
- Staging: production-like policy and migrations with synthetic/licensed smoke projects.
- Production pilot: invite-only, strict quotas, approved providers, encrypted managed services, separate credentials and data.

Promotion must use immutable artifacts and reviewed migrations. Define rollback before each production change.

## Service Objectives For Pilot

These are starting targets to confirm after workload tests:

- Interactive API p95 below 500 ms excluding upload and queued AI work.
- Job progress visible within 5 seconds of state change.
- No lost acknowledged edits or approvals.
- 100% cue/timestamp integrity for successful exports.
- Recovery point and recovery time objectives documented and tested before external pilot.

Do not promise enterprise SLA until usage and failure data support it.

## Observability

### Metrics

- Requests, latency, errors, saturation, queue depth/age, worker concurrency, retries, dead letters, and job completion time.
- Provider/model latency, error category, input/output usage, normalized cost, and circuit state.
- Files/cues processed, translation completion, warning rates, edit/approval/export funnel, and deletion completion.
- Cue/timestamp integrity failures and protected-invariant failures as high-severity product signals.

### Logs And Traces

- Correlate request, job, project, provider call, and export with opaque IDs.
- Redact subtitle text, prompts, provider keys, signed URLs, emails, and sensitive metadata by default.
- Restrict and audit any exceptional content-level diagnostic access.
- Bound retention and align it with privacy notices.

### Alerts

- Cross-tenant authorization anomaly or suspicious signed-URL use.
- Cue/timestamp integrity failure.
- Queue age/dead-letter spike or sustained job failure.
- Provider spend, token/character use, or latency above budget.
- Backup/restore, deletion backlog, malware scan, or audit pipeline failure.
- Elevated authentication/admin activity or secret-scanner finding.

## Cost Controls

- Batch by context block instead of repeating context per cue.
- Retrieve only relevant glossary/memory and cache stable profile context safely.
- Run deterministic checks before paid model-assisted QA.
- Route low-risk blocks to cheaper paths and premium refinement to measured high-risk cases.
- Apply per-user/organisation file, cue, concurrency, provider, and monthly spend quotas.
- Estimate job cost before dispatch and stop safely at budget limits.
- Track actual cost per completed project and per publish-ready minute, not only per API call.
- Do not process video/audio in MVP.

Research planning ranges, to replace with live benchmark data:

| Workload | Balanced AI planning estimate |
| --- | --- |
| 45-minute episode | Target below US$3 |
| 100-120 minute film | Target below US$8 |

Human review cost and time saved remain the central economic measures; optimizing pennies of inference is secondary if quality or editing time worsens.

## Capacity And Abuse

- Start with invite-only accounts and hard file/cue/job limits.
- Enforce fair queueing and tenant concurrency so one project cannot starve others.
- Bound prompt/context/output size and parser CPU/memory/time.
- Rate-limit upload intents, job creation, regeneration, QA, export, and downloads separately.
- Detect repeated failed uploads, job replay, credential sharing, and provider-cost abuse.

## Backup And Recovery

- Back up transactional records encrypted under managed keys.
- Decide whether short-retention source objects are backed up; disclose and test the chosen behavior.
- Restore into an isolated environment and verify tenant ownership, cue/timestamp integrity, version history, and deletion markers.
- Ensure deletion commitments include documented backup expiry rather than claiming immediate physical erasure where impossible.

## Incident Runbooks

Create and rehearse runbooks for:

- Cross-tenant or signed-URL exposure.
- AI provider data-policy breach or credential compromise.
- Malicious upload/parser exhaustion.
- Job duplication and spend spike.
- Data corruption or cue/timestamp integrity regression.
- Incomplete deletion or backup exposure.
- Provider outage/model regression and emergency routing disablement.

Each runbook covers detection, containment, credential revocation, evidence preservation, customer/legal notification assessment, recovery, and follow-up tests.

## Pilot Operations Review

Review weekly:

- Completion/export and second-project use.
- Editing-time and critical-error outcomes.
- Support issues and warning usefulness.
- Provider reliability, cost, and privacy concerns.
- Security events, access reviews, deletion status, and backup health.
- Scope requests against measured pain; defer features not tied to validated outcomes.

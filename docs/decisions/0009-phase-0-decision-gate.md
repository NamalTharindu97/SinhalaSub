# ADR 0009: Evidence-Bound Phase 0 Decision Gate

- Status: Accepted
- Date: 2026-08-22
- Owner: Project team

## Context

The product plan defines fixed quality, editing-time, preference, integrity, cost, and sample-size gates plus four outcomes. Without a deterministic final audit, a team could selectively interpret results, lower thresholds after observing them, or mistake synthetic protocol data for authorization to build Phase 2.

## Decision

Use a versioned decision manifest that hash-binds one immutable evidence record. The evidence binds the audited system-run capture and records translator/viewer sample sizes, independent reviewers, protocol and analysis approval, cloud-upload acceptance, and the frozen metrics.

The audit applies these unchanged thresholds:

- 100% cue/timestamp integrity.
- At least 95% protected-entity preservation.
- At least 25% median editing-time reduction.
- At least 30% critical-error reduction.
- Critical hallucinations below 0.5% with no systematic failure.
- At least 65% viewer preference.
- At most US$3 per 45-minute episode and US$8 per film.
- At least three experienced translators and 30 Sinhala-speaking viewers.

Real evidence also requires two independent reviewers, approved protocol, reviewed analysis, and a ready run/freeze/corpus chain. Outcomes are deterministic: `go`, `local-pivot`, `narrow`, or `stop`. Missing, invalid, unreviewed, unready, or synthetic evidence always yields `not-authorized`.

## Consequences

- Passing synthetic numbers cannot authorize Phase 2.
- Threshold failures remain visible individually rather than being averaged into one score.
- The evidence record is an auditable assertion signed off operationally; the tool verifies structure, hashes, and rules but cannot prove reviewer identity or measurement authenticity.
- A decision manifest and evidence record must be frozen before communicating the final outcome.

## Security, Privacy, Legal, And Cost

- Decision records contain aggregates, pseudonymous reviewer IDs, and hashes, not participant identity, raw subtitle text, credentials, or legal advice.
- Participant consent, compensation, legal approval, and source measurement records remain separately controlled.
- Cloud acceptance is an explicit input and can force the local-pivot outcome even if quality passes.
- The audit is local and incurs no provider cost.

## Reversal Trigger

Version the schema before the real decision if the approved statistical analysis changes metric definitions or confidence requirements. Do not alter thresholds or outcome rules after unblinding results.

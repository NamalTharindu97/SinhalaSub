# ADR 0011: Paired Editing-Time Analysis

- Status: Accepted
- Date: 2026-08-23
- Owner: Project team

## Context

The Phase 0 gate requires at least 25% lower median publish-ready editing time than the selected baseline. Local experiment reports already capture active and elapsed time, changed cues, keyboard actions, and edit events, but those reports previously had no controlled join between the same reviewer and asset under baseline and contextual conditions.

## Decision

Analyze editing time separately from blinded quality scoring with `sinhalasub.editing-sessions.v1` and `sinhalasub.editing-analysis.v1` records.

The confidential editing-session manifest:

- Assigns each embedded `sinhalasub.experiment-report.v1` to a pseudonymous reviewer, asset, and one of exactly two system conditions.
- Requires exactly one baseline and one contextual report for every reviewer/asset pair.
- Rejects reused reports, duplicate assignments, source substitution, malformed timestamps, and impossible timing or telemetry values.
- Uses active editing time rather than wall-clock elapsed time for the primary metric.
- Pins a bootstrap seed so identical evidence produces identical analysis.

The analysis reports median active time by condition, the median within-pair proportional reduction, and a 95% percentile bootstrap confidence interval for that paired median. The frozen threshold passes when the observed paired median reduction is at least 25%; the interval is reported as uncertainty and is not silently substituted for the frozen decision rule.

Synthetic manifests always remain not ready even if their metric passes. Real readiness requires valid complete pairs from at least three translators, in addition to the other corpus, protocol, legal, evaluation, and decision-review gates.

## Consequences

- Reviewer and asset effects are controlled through within-pair comparisons.
- Raw review telemetry remains auditable inside the manifest instead of being copied into an untraceable aggregate.
- System assignments and the resulting analysis are confidential until collection is locked.
- A small sample can produce a wide or unstable interval; the output is evidence, not automatic product authorization.

## Security, Privacy, Legal, And Cost

- Reviewer IDs are pseudonyms; consent, identity mapping, and compensation records remain outside the analysis artifact.
- Reports include subtitle text in normal operation, so manifests and analyses inherit corpus access and retention controls.
- The analysis is deterministic, local, and has no provider cost.

## Reversal Trigger

Version the schemas if the approved protocol uses cross-over periods, multiple assets per condition with hierarchical weighting, exclusion rules, or an independently specified interval estimator.

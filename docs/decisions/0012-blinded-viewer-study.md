# ADR 0012: Blinded Viewer Preference And Comprehension Study

- Status: Accepted
- Date: 2026-08-23
- Owner: Project team

## Context

The Phase 0 protocol requires blind A/B viewing by at least 30 Sinhala-speaking viewers and at least 65% preference for the contextual system over baseline. The decision gate previously accepted a manually asserted preference rate and viewer count. Viewer comprehension, consent, presentation order, source-system blinding, and package identity were not represented by executable contracts.

## Decision

Use separate versioned viewer-study manifest, evaluator package, confidential key, response, and analysis schemas.

The builder:

- Requires an audited system-run capture and binds the package to its canonical manifest hash.
- Selects exactly the frozen baseline and contextual outputs for each declared asset.
- Includes only subtitle candidates, rights basis, a controlled external clip reference, and comprehension prompts/options. It never uploads or packages video.
- Randomizes neutral candidate labels with a pinned seed.
- Stores source-system mappings and correct comprehension options only in the confidential key.
- Refuses a real study unless its run capture is ready.

Each pseudonymous viewer response binds to the package hash, confirms consent, records a timezone-aware completion, reports cloud-upload acceptance, covers every asset once, records candidate presentation order and preference, and answers every question for both candidates.

Analysis rejects mismatched, duplicate, partial, malformed, or substituted evidence. It reports system preference counts, contextual preference with a 95% Wilson interval, comprehension accuracy by system, per-asset preference, and cloud-upload acceptance. At least 30 unique viewers are required. The frozen preference rule uses the observed rate of at least 65%; the interval communicates uncertainty rather than replacing the rule.

## Consequences

- Viewers cannot infer system identity or correct answers from their package.
- Preference and comprehension derive from hash-bound raw responses instead of copied decision metrics.
- Presentation order is auditable, but controlled-session operators remain responsible for random assignment and correct clip playback.
- Synthetic evidence can exercise all thresholds but remains not ready.

## Security, Privacy, Legal, And Cost

- Viewer IDs are pseudonyms. Identity, recruitment, consent evidence, compensation, and withdrawal records stay in the approved research system.
- Clip references point to access-controlled playback arranged under the asset licence. The harness remains subtitle-only and does not distribute video.
- Packages and responses inherit corpus retention and access rules; the confidential key remains unavailable to viewers until collection is locked.
- Analysis is local and has no provider cost; recruitment and licensed playback are external experiment costs.

## Reversal Trigger

Version the contracts if protocol approval requires per-viewer assignment tokens, comprehension free text, no-repeat between-subject designs, accessibility accommodations, or a different interval/decision rule.

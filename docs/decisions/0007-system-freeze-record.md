# ADR 0007: Provider-Neutral System Freeze Record

- Status: Accepted
- Date: 2026-08-22
- Owner: Project team

## Context

The controlled experiment must freeze its corpus, three system roles, instructions, model versions, adapter versions, data policies, randomisation seed, and rubric before generating results. No live provider is approved yet, and synthetic fixtures must not be mistaken for an authorised real-system freeze.

## Decision

Use a versioned provider-neutral system-freeze manifest and deterministic audit.

The manifest requires exactly one `generic-mt`, one `isolated-llm`, and one `contextual-pipeline` role. Every system pins a unique ID, provider, model and model version, adapter version, versioned instruction artifact and SHA-256, and reviewed data-policy fields for training use, retention, region, and review date. The freeze also pins the corpus-manifest hash, rubric version, and randomisation seed.

A real freeze is ready only when the corpus readiness audit passes and every provider policy has status `approved` with training disabled. Synthetic records use `dry_run: true` and `not-applicable-synthetic`; they may be structurally valid but can never authorize the experiment.

## Consequences

- Provider selection remains replaceable and no live SDK is introduced by this decision.
- Editing the corpus or an instruction artifact invalidates its declared hash and requires an explicit new freeze.
- Output generation is captured under ADR 0008; packaging verifies the source, seed, system IDs, and captured output hashes and carries freeze/run identity in the confidential key.
- Legal approval is recorded as a gate, not inferred by the tool; the underlying review evidence remains separately controlled.

## Security, Privacy, Legal, And Cost

- Provider training must remain disabled for every real system.
- Retention and processing region must be recorded and approved before dispatching non-synthetic text.
- Freeze records contain identifiers and hashes, not credentials, customer text, contracts, or legal advice.
- The audit is offline and incurs no provider cost.

## Reversal Trigger

Version the schema before the real freeze if approved providers require additional routing, regional, prompt, safety, or cost controls. Do not mutate the frozen record after observing system outputs.

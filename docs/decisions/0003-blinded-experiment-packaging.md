# ADR 0003: Blinded Experiment Packaging

- Status: Accepted
- Date: 2026-08-22
- Owner: Project team

## Context

The controlled experiment requires three systems to be evaluated on identical complete context blocks without exposing system identity. Re-running the same frozen inputs must reproduce the same package, and the evaluator artifact must not contain a seed, provider/model metadata, or source file paths that can reveal conditions.

## Decision

Use a local JSON manifest and Python standard-library runner to create two separate artifacts:

- An evaluator ZIP containing only `package.json`, source/context cues, and per-block labels `candidate-1` through `candidate-3`.
- A confidential JSON key containing the seed, system IDs/metadata, input hashes, and each block's label mapping.

The runner:

- Requires exactly three unique system outputs.
- Requires an audited system-freeze record and complete system-run capture, matching randomisation seed, source, system IDs, and captured output hashes.
- Requires explicit source provenance and rights basis.
- Rejects any output that changes format, cue IDs, order, or timestamps.
- Uses a fixed integer seed and block ID to deterministically shuffle labels separately for every context block.
- Keeps corpus genre and challenge tags only in the confidential key; evaluator packages expose the critical-error vocabulary but not strata that could bias scoring.
- Hashes normalized source/system files and the evaluator package, and records system-freeze and system-run identities/hashes in the confidential key.
- Writes ZIP metadata deterministically so identical inputs reproduce identical bytes.

## Consequences

- System outputs are generated before packaging; this runner makes no provider calls.
- A not-ready freeze is rejected by default. The explicit override accepts only a structurally valid `dry_run` freeze for synthetic protocol testing.
- Candidate labels are not stable across blocks, reducing simple position bias and accidental unblinding.
- The confidential key must never be distributed to evaluators or stored inside the ZIP.
- Different seeds may occasionally produce the same permutation for a block; reproducibility, not guaranteed uniqueness between seeds, is the contract.

## Security, Privacy, Legal, And Cost

- Manifests may reference only commissioned, licensed, public-domain, or otherwise authorised files with recorded provenance.
- Evaluator packages contain source and candidate subtitle text and must be handled according to the corpus agreement.
- Provider/model details remain in the confidential key.
- Packaging is offline and incurs no provider cost.

## Reversal Trigger

Revise the format only before freezing a real experiment, or version the schemas if evaluator tooling requires new fields after a freeze.

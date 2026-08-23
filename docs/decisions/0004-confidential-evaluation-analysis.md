# ADR 0004: Confidential Evaluation Analysis

- Status: Accepted
- Date: 2026-08-22
- Owner: Project team

## Context

Blinded evaluators need one fixed scoring contract, while system identities must remain unavailable until responses are complete. Analysis must reject partial/mismatched responses and report quality, preference uncertainty, critical errors, and inter-rater agreement without modifying raw evaluator files.

## Decision

Use versioned evaluator-response and confidential-analysis JSON schemas.

Each evaluator response:

- Identifies the exact package hash and a unique pseudonymous evaluator ID.
- Includes every block and candidate exactly once in package order.
- Scores accuracy, fluency, context, tone/voice, terminology, readability, cultural appropriateness, and formatting as integers from 1 to 5.
- Records a non-negative critical-error count per candidate and may allocate it across the controlled name/entity, context/meaning, omission/addition, tone/register, terminology, formatting/readability, and hallucination categories.
- Selects exactly one preferred candidate per block.

The confidential key binds each block to its corpus genre and challenge phenomena without exposing them to evaluators. The analysis command requires the blinded ZIP, separate key, and all response files. It validates hashes and schemas before unblinding, then reports per-system rubric means, preference counts/rates with 95% Wilson intervals, categorized critical errors, Fleiss' kappa, and genre/challenge-stratified preference/error summaries.

## Consequences

- Evaluators never need the confidential key.
- Response files remain blinded and can be audited independently before unblinding.
- Legacy/synthetic responses with only an aggregate critical count remain valid and are reported as `unclassified`; categories are never inferred after scoring.
- Editing-time effects remain separate from rubric analysis. ADR 0011 defines confidential reviewer/asset pairing over versioned review reports.
- Statistical outputs are descriptive for small dry runs and must not be presented as proof of quality.

## Security, Privacy, Legal, And Cost

- Evaluator IDs should be pseudonyms; identity mapping, consent, and compensation records stay outside response files.
- Confidential analysis contains system identities and must not be sent to evaluators before scoring is locked.
- Source/candidate text remains governed by the corpus agreement.
- Analysis is offline and has no provider cost.

## Reversal Trigger

Version the schemas before the real experiment if adjudication, challenge categories, viewer comprehension, or paired editing-report joins require additional fields.

# AI Translation And Quality Plan

## Goal

Produce a better editable draft than generic line-by-line translation while making deterministic failures visible and preserving human control. Model output is always untrusted input until schema and invariant validation pass.

## Pipeline

1. Parse source cues into canonical records.
2. Normalize text to NFC and extract protected invariants.
3. Detect candidate names, aliases, places, organisations, brands, terms, numbers, dates, currencies, URLs, codes, and negation.
4. Ask the user to resolve ambiguous high-impact entities and Sinhala spellings.
5. Group cues into context blocks using deterministic text/timing signals.
6. Retrieve only relevant approved glossary and project-memory entries.
7. Generate a baseline draft with a provider-neutral adapter.
8. Refine selectively with adjacent cues, style, speaker/relationship evidence, and approved terminology.
9. Validate response schema, cue coverage, and protected tokens before storing candidates.
10. Run deterministic QA, then selective model-assisted semantic/context checks.
11. Compute component scores and review priority; do not present a single opaque probability.
12. Save human-approved corrections to project memory only.

## Context Contract

Each block request may include:

- Project genre, era, style, audience, and profanity/intensity policy.
- Confirmed characters, aliases, relationships, and approved Sinhala names.
- Relevant glossary entries and prior approved translations.
- Current ordered cues with stable IDs and durations.
- Bounded previous/next dialogue and optional speaker labels.
- Protected placeholders and configurable readability targets.

Do not send future-episode plot facts, unrelated project content, full files when a block is enough, or metadata without a permitted source and scope.

## Structured Output Rules

For every requested cue, return:

- Exact stable cue ID.
- Sinhala candidate text only, without timestamps.
- Uncertainty flag.
- Enumerated warning/reason codes.
- Protected-token references used.

Reject the entire block or affected cue when output is missing, duplicated, extra, malformed, or violates protected invariants. Never infer a timestamp from model output.

## Deterministic QA

### Blocking

- Missing, extra, duplicate, or reordered canonical cue identity.
- Timestamp or cue-count mismatch at export.
- Unparseable SRT/WebVTT output.
- Missing required protected names/numbers/dates/currencies/codes/URLs.
- Failed normalization or invalid text encoding.

### Warning

- Glossary mismatch or inconsistent entity transliteration.
- Changed negation signal.
- Unexplained English residue based on style policy.
- More than configured lines or grapheme density/read speed above profile.
- Poor line break, overlap, duration, or gap inherited from source.
- Profanity/intensity mismatch requiring human judgment.

Source timing defects should be reported but not silently repaired in translation-only mode.

## Model-Assisted QA

Use bilingual comparison for likely omission, addition, reversal, wrong word sense, pronoun/reference, tone, idiom, sarcasm, and adjacent-dialogue mismatch. Return structured warning evidence and suggested alternatives; do not modify approved text during QA.

Human review remains mandatory for humour, puns, songs, cultural references, profanity, relationships/hierarchy, historical voice, and unresolved visual/speaker context.

## Review Priority

Initial risk weighting:

```text
risk = 0.30 * (1 - semantic)
     + 0.20 * (1 - entity)
     + 0.15 * (1 - terminology)
     + 0.15 * (1 - context)
     + 0.10 * (1 - readability)
     + 0.10 * (1 - formatting)
```

Hard overrides:

- Changed fact, number, date, currency, negation, or name: high priority.
- Missing/extra cue or timestamp mutation: block export.
- Unapproved English residue: medium/high according to project policy.
- Profanity/intensity change: required human review.

Treat weights and thresholds as versioned calibration data. Validate them against adjudicated human labels before describing them as confidence.

## Provider Strategy

- Benchmark at least one generic cloud Sinhala MT path and one context-capable LLM path.
- Hide providers behind common contracts and capture model/version, latency, usage, and normalized cost.
- Route by project privacy policy, capability, measured quality, availability, and budget.
- Use low-cost translation for straightforward blocks and premium refinement/criticism only when expected value justifies it.
- Do not make DeepL a dependency without verified Sinhala support.
- Keep NLLB-200 as a non-commercial research baseline unless separate commercial rights are obtained; its published model card is not a production authorization.

## Prompt Governance

- Version prompts and schemas in source control.
- Evaluate every prompt/model change on a frozen regression set.
- Require structured output and bounded context/token limits.
- Request concise reason codes, not hidden chain-of-thought.
- Treat subtitle text and retrieved metadata as untrusted prompt input; delimit it and prevent it from changing system policy.
- Keep test references and adjudicated answers out of generation prompts.

## Translation Memory

- Store only human-approved pairs.
- Scope to project by default; series, user, and organisation reuse require explicit settings.
- Link every memory item to source project, approval, rights/consent, and deletion behavior.
- Retrieve by source/context relevance and glossary compatibility, not embedding similarity alone.
- Never convert project memory into global training data without separate explicit opt-in and rights declaration.

## Quality Improvement Loop

1. Aggregate warning outcomes and correction categories without exposing raw content in routine telemetry.
2. Sample consented, rights-clean failures for expert annotation.
3. Update rules/prompts/adapters against training/development data.
4. Run the frozen hold-out suite and compare critical-error regressions.
5. Release behind a versioned rollout and retain rollback capability.
6. Recalibrate scores only from human-labelled results.

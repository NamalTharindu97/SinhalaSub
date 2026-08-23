# ADR 0010: Versioned Project Context Profile

- Status: Accepted
- Date: 2026-08-23
- Owner: Project team

## Context

The experiment needs repeatable character, alias, glossary, and dialogue-style inputs. A flat comma-separated name list cannot represent aliases or prove that an approved Sinhala term survives provider output.

## Decision

Use `sinhalasub.project-context.v1` with a style, globally unique character names/aliases, and unique English-to-Sinhala glossary entries.

- Character names and aliases become exact protected `NAME` placeholders.
- Glossary source phrases become protected `TERM` placeholders whose validated restoration value is the approved Sinhala target.
- Duplicate aliases, duplicate glossary sources, name/glossary collisions, empty values, and unsupported schemas are rejected before preparation.
- The local GUI accepts one character per line as `name | alias, alias`, one glossary entry per line as `source = target`, and a style selection.
- Experiment reports record style and character/glossary term counts without adding persistence or provider calls.

## Consequences

- The echo provider can contract-test deterministic glossary enforcement without pretending to translate other text.
- Matching is case-sensitive and term-boundary based; automated entity detection and inflection-aware terminology remain future experiment work.
- Project context remains caller-supplied and in memory in the local GUI.

## Security, Privacy, Legal, And Cost

- Profiles may reveal character identities or confidential terminology; treat them as project content and do not log or share them globally.
- Only user-approved terms are enforced; repository fixtures remain synthetic.
- No external request or provider cost is introduced.

## Reversal Trigger

Version the schema if the real experiment requires relationship graphs, inflected glossary forms, transliteration policy, per-speaker register, or ambiguous-term disambiguation.

# Product Scope

## Problem

Generic line-by-line translation loses dialogue context and produces unstable Sinhala names, terminology, tone, pronouns, idioms, and line length. Translators then spend time repairing the draft while also protecting subtitle structure and timing.

## Product Outcome

An experienced Sinhala translator can turn an authorised English SRT/WebVTT file into publication-ready Sinhala faster, with fewer critical context and entity errors than a generic machine-translation baseline.

The product is an editing assistant, not an autonomous publisher. Final approval always belongs to a human reviewer.

## Initial Users

| Priority | User | Primary need |
| --- | --- | --- |
| 1 | Freelance translators | Faster drafting with reliable terminology and private projects |
| 1 | YouTubers and educators | Localise owned content with simple export |
| 1 | Localisation teams and independent producers | Review workflow, consistency, and traceability |
| 2 | Experienced hobby subtitle creators | Quality assistance and workflow research |
| 2 | Broadcasters | Privacy and auditability; enterprise controls come later |

General viewers and public subtitle-download users are not MVP customers.

## Core User Journey

1. Create a private project and declare authority to translate the content.
2. Upload an SRT or WebVTT file; receive structural validation results.
3. Confirm title/version, genre, style, characters, aliases, and Sinhala spellings.
4. Add or approve project glossary terms.
5. Start a context-aware translation job and monitor progress.
6. Review high-risk cues first or review chronologically by scene.
7. Edit, compare alternatives, approve, comment, and undo without losing prior versions.
8. Run final QA and export SRT/WebVTT with original timings.
9. Delete the project or retain approved project memory under the selected policy.

## MVP Requirements

### Import And Project Setup

- Accept SRT and WebVTT only.
- Detect encoding, normalize working text to UTF-8 NFC, and preserve source-format information needed for export.
- Reject malformed, unsupported, or oversized files with actionable errors.
- Capture media title, year, optional season/episode, genre, style profile, and rights declaration.
- Retain an immutable original and canonical cue representation.

### Translation Preparation

- Manage characters, aliases, optional relationships, and approved Sinhala transliterations.
- Manage project glossary terms and translation/transliteration/retain-English decisions.
- Detect candidate entities and ambiguous common-word/name collisions for confirmation.
- Group cues into text-derived context blocks using time gaps, punctuation, and dialogue continuity.

### Translation And QA

- Translate blocks using previous/next context, style profile, confirmed entities, and relevant glossary terms.
- Protect cue IDs, names, numbers, dates, currencies, URLs, codes, and negation signals.
- Store provider, model, prompt version, glossary version, usage, and latency for every generated draft.
- Run deterministic structural and invariant checks independently from model-assisted semantic review.
- Assign component scores and warnings rather than presenting model self-confidence as probability.

### Human Review

- Show source and target side by side with adjacent cues and timing.
- Support keyboard navigation, edit, approve, skip, undo, regenerate, shorten, and alternatives.
- Filter by risk, warning type, approval state, speaker, and modified state.
- Show concise warning evidence and glossary/entity provenance; never expose hidden model reasoning.
- Preserve version history and require explicit acceptance before regenerated text replaces work.

### Export And Lifecycle

- Block export for cue loss, timestamp mutation, malformed output, or unresolved blocking warnings.
- Reconstruct valid SRT/WebVTT from canonical timing and approved text.
- Produce an export validation summary.
- Support save/resume, project deletion, and a documented source-file retention policy.
- Keep correction memory project-scoped by default.

## Pilot Defaults To Validate

- Maximum two lines per cue.
- Soft target of 36-40 extended grapheme clusters per line.
- Readability warning above 14-17 grapheme clusters per second.
- Duration warning below 1 second or above 7 seconds.
- UTF-8 and NFC for working/exported text.

These are hypotheses, not universal Sinhala subtitle standards. Store them as configurable profiles rather than hard-coded truths.

## Explicit Exclusions

- Full video/audio upload, transcoding, ASR, diarisation, face recognition, and automatic scene detection.
- Automatic timing repair in translation-only mode.
- Public subtitle discovery, download, or redistribution.
- Scraping subtitle, script, movie, or metadata sites without explicit permission.
- Fine-tuning on user content or public subtitle corpora without proven rights and consent.
- Fully automatic publication or claims of perfect translation.
- Tamil/multilingual expansion, reviewer marketplace, billing, and enterprise private deployment.

## MVP Success Metrics

| Metric | Required result |
| --- | --- |
| Cue-count and timestamp integrity | 100% |
| Protected-entity preservation before correction | At least 95% |
| Median publish-ready editing time | At least 25% below selected generic MT baseline |
| Critical name/context errors | At least 30% below baseline |
| Critical hallucinations | Below 0.5% of cues and no repeated systematic failure |
| Human preference | At least 65% prefer the contextual pipeline over baseline |
| External pilot security | No unresolved critical findings |
| Pilot retention | At least 70% complete a second project or explicitly request continued access |

## Product Gate

Proceed from prototype to web MVP only when the controlled experiment in `02-validation-plan.md` meets the integrity, quality, and editing-time thresholds. If it fails, test a narrower QA-only, glossary/entity, plugin, or B2B workflow before adding features.

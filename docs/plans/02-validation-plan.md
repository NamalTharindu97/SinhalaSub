# Validation Plan

## Objective

Validate the problem, legal operating model, Sinhala quality improvement, editing-time reduction, cloud-upload acceptance, and willingness to pay before committing to the complete SaaS.

## Phase 0 Outputs

- Interview evidence and observed workflow notes.
- Counsel-reviewed authorised-use and data-handling model.
- Rights-clean evaluation corpus and annotation guide.
- Frozen baseline systems, prompts, model versions, and experiment protocol.
- Clickable editor prototype tested with translators.
- Signed or documented pilot interest from target users.
- Written go, narrow/pivot, or stop decision.

## Discovery Research

### Participants

- Interview 15-20 Sinhala subtitle creators across experience levels.
- Interview 5-8 professional translators or localisation staff.
- Interview 3-5 authorised content organisations.
- Observe at least five complete or representative translation sessions.

### Measure

- Time spent on draft translation, names/terms, context lookup, shortening, and final review.
- Current tools, Sinhala input methods, source-file problems, and baseline AI use.
- Error types that cause rework or viewer complaints.
- Acceptable cloud inputs: subtitles, transcript, audio, or video.
- Required retention, deletion, confidentiality, and provider controls.
- Value of glossary, context, QA, editor, offline mode, and collaboration.
- Willingness to pay only after demonstrating measured time saved.

### Discovery Exit Criteria

- At least ten target users confirm context/entity/consistency or review effort as a recurring problem.
- At least five suitable users agree to a timed evaluation or prototype test.
- At least three authorised organisations or ten active creators express concrete pilot interest.
- Cloud subtitle-only processing is acceptable to a viable initial segment, or a local-first pivot is explicitly chosen.

## Legal And Data Validation

Before processing non-fictional customer content, obtain qualified advice on:

- Sri Lankan copyright treatment of subtitle translation and private processing.
- Rights declaration, customer warranties, takedown, repeat-infringer, and appeal procedures.
- Sri Lankan PDPA notices, processor/controller roles, deletion, retention, and cross-border providers.
- Ownership and permitted reuse of output, corrections, glossaries, and project memory.
- AI-provider terms, training controls, data retention, and data-processing agreements.
- Metadata-provider licences, attribution, caching, AI/RAG restrictions, and removal duties.

Legal review is an external-pilot gate, not a post-launch task.

## Evaluation Corpus

### Composition

- Build 1,500-2,000 cues from commissioned fictional dialogue and verified licensed/public-domain samples.
- Cover modern drama, comedy, crime/action, fantasy, documentary/technical, and youth/social dialogue.
- Mark 150-250 challenge cues containing ambiguous names, pronouns, idioms, sarcasm, negation, numbers, terminology, profanity/tone, and line-length pressure.
- Include multiple speaker relationships, registers, cue durations, and dialogue densities.

### Controls

- Store licence or contributor agreement for every source and reference.
- Create independent source, reference, and adjudicated versions.
- Keep references out of prompts and retain a private hold-out set.
- Have at least two Sinhala experts annotate each sample and adjudicate disagreements.
- Define acceptable alternatives; do not force one-reference wording where multiple translations are valid.

## Controlled Experiment

### Systems

- A: selected generic cloud translation baseline.
- B: LLM translating isolated lines with no project context.
- C: proposed context, glossary, entity protection, deterministic QA, and refinement pipeline.
- Human workflow/reference is measured separately, not treated as a model output.

### Procedure

1. Freeze corpus, systems, prompts, model versions, and scoring rubric before the run.
2. Randomise scene blocks and hide system identity.
3. Have three experienced translators edit complete scenes to publication-ready quality under timed conditions.
4. Capture elapsed time, active edit time, keystrokes, changed cues, warning usefulness, and final text.
5. Use a separate adjudicator for critical-error disagreements.
6. Run blind A/B viewing with at least 30 Sinhala-speaking viewers on short licensed clips.
7. Report paired results with confidence intervals and inter-rater agreement.
8. Stratify by genre and challenge type; never average away severe failures.

### Go Thresholds

- 100% cue and timestamp integrity.
- At least 95% protected-entity preservation before correction.
- At least 25% lower median editing time than baseline.
- At least 30% fewer critical name/context errors than baseline.
- Critical hallucinations below 0.5% with no systematic class of failure.
- At least 65% human preference over baseline.
- Target inference cost below US$3 per 45-minute episode and US$8 per film, excluding human review.

### Decision Outcomes

- **Go:** Integrity thresholds and editing-time/critical-error improvements pass. Build the MVP.
- **Narrow:** Entity, glossary, or QA value passes but full translation does not. Build a QA/plugin workflow.
- **Local pivot:** Quality passes but users reject cloud subtitle upload. Prototype local/hybrid processing.
- **Stop:** No material editing-time or quality improvement and no narrower paid need emerges.

## Pilot Validation

After the experiment passes:

- Invite 10-15 creators and three authorised organisations.
- Require at least two real projects per participant where practical.
- Capture opt-in time/correction telemetry and conduct post-project interviews.
- Track activation, completion, export, second-project use, critical incidents, support load, and cost.
- Do not retain samples beyond the selected project policy without explicit permission.

Paid-pilot gate: at least ten active creators or three authorised organisations complete real projects and show repeat use.

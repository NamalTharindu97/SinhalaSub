# Review Experience Plan

## UX Objective

Help translators make safe decisions quickly. The interface should prioritize risky cues while retaining chronological scene review and should explain warnings without pretending AI output is authoritative.

## Primary Screens

### Project Setup

- Rights declaration and selected retention/provider policy.
- SRT/WebVTT upload with validation summary.
- Media identity, genre, style, audience, and optional season/episode.
- Character/alias confirmation and approved Sinhala spellings.
- Glossary review and ambiguous entity queue.
- Translation readiness checklist and estimated cost/range.

### Translation Progress

- Job status by block, completed/failed counts, cancellation, and retry guidance.
- No false precision for remaining time.
- Clear notice when profile/glossary changes supersede an in-flight job.

### Review Editor

- Source, Sinhala candidate, cue time/duration, and previous/next dialogue.
- Chronological and risk-ranked modes.
- Warning panel with severity, concise evidence, provenance, and resolution action.
- Character and glossary cards with approved values and affected-cue preview.
- Alternatives and regenerate/shorten actions that create candidates rather than overwrite edits.
- Inline grapheme count, reading speed, line count, approval, comment, and version history.
- Filters for severity, warning type, unapproved, modified, speaker, and glossary term.

### Export

- Exact output preview.
- Cue/timestamp integrity, encoding, readability, and unresolved-warning summary.
- Blocking issues linked back to affected cues.
- Explicit format choice, generation action, expiring download, and deletion controls.

## Keyboard Workflow

The initial usability prototype must test:

- Move next/previous cue.
- Edit and save without leaving the keyboard.
- Approve and advance.
- Skip, undo, open context, and open warning details.
- Insert a natural line break.
- Filter to next high-risk or unresolved cue.

Finalize key bindings with translator interviews and avoid overriding browser/assistive-technology conventions.

## Trust And Safety Behavior

- Show what changed and why a warning exists using source/target highlights and reason codes.
- Label generated suggestions as drafts until explicitly approved.
- Never replace a human edit after regeneration, glossary updates, or background QA.
- Show source/licence/scope for external knowledge and allow users to remove or disable it.
- Separate project memory consent from global-learning consent; global learning defaults off.
- Make retention, provider routing, and deletion status visible at project level.
- If confidence is uncalibrated, call it review priority or component score rather than probability.

## Sinhala And Subtitle Rendering

- Use fonts with tested Sinhala coverage and provide a fallback stack.
- Normalize to NFC but preserve the immutable original source separately.
- Count extended grapheme clusters rather than bytes or code points.
- Test selection, cursor movement, line wrapping, copy/paste, search, and highlighting with combining sequences.
- Preview two-line rendering at representative mobile, desktop, TV-like, and video-player widths.
- Support local video selection for browser-only playback later without uploading the media file.

## Accessibility And Responsive Behavior

- Make the editor fully operable by keyboard with visible focus and no focus loss after saves.
- Expose warnings, progress, and approval state to assistive technology without relying only on color.
- Ensure touch targets and split-pane behavior remain usable on tablet/mobile; desktop remains the primary editing surface.
- Respect zoom and text enlargement; avoid fixed-height text regions that hide Sinhala glyphs.
- Announce background job and save results without repeatedly interrupting editing.
- Test contrast, reduced motion, error association, and dialog focus before pilot.

## UX Validation Tasks

Observe at least five translators performing:

1. Import and repair a deliberately malformed file.
2. Resolve Will/Rose-style entity ambiguity.
3. Add a glossary decision and preview affected cues.
4. Review high-risk cues and then inspect chronological context.
5. Regenerate without losing a manual edit.
6. Resolve a blocking invariant warning.
7. Export and verify the resulting file in a subtitle player.
8. Delete the project and explain what data remains temporarily.

Record task completion, errors, time, keyboard/mouse switching, misunderstood labels, warning usefulness, and trust concerns.

## UX Acceptance

- A pilot translator can complete the core journey without facilitator intervention.
- No observed action silently loses approved or manually edited text.
- Users can correctly explain rights, retention, AI draft status, blocking warnings, and deletion behavior.
- At least 80% of critical warnings are correctly understood in usability testing.
- Export-blocking errors lead users directly to a resolution path.

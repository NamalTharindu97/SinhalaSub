# Phase 0 Experiment Harness

This package provides the subtitle integrity foundation for the controlled English-to-Sinhala translation experiment. It parses and normalizes SRT/WebVTT files, prepares bounded context blocks, and protects confirmed names and factual values without changing cue timing.

## Requirements

- Python 3.9+
- No third-party dependencies

## Commands

Run all tests:

```sh
python3 -m unittest discover -s experiment/tests -v
```

Run one test module:

```sh
python3 -m unittest experiment.tests.test_subtitles -v
```

Start the local review workspace:

```sh
PYTHONPATH=experiment/src python3 -m sinhalasub.web --open
```

Then open `http://127.0.0.1:8765`. The workspace accepts an SRT/WebVTT file, keeps timing locked, prepares context/protected values, lets you edit target text, and exports a reviewed copy. It runs locally and does not translate text with AI yet.

The preparation panel accepts character aliases (`name | alias, alias`), approved glossary entries (`source = Sinhala target`), and dialogue style. Names/aliases, glossary targets, numbers, dates, currencies, and URLs are protected through provider round trips. The versioned example is `examples/project-context.json`. The repository still includes only an echo provider for contract testing; no live AI provider is configured.

## Local File Handling

- The browser exposes the selected filename, not its full original path; this is a browser security restriction.
- The GUI reads subtitle text into browser/server request memory and does not save an uploaded source file on the server filesystem.
- Closing or reloading the page clears the current workspace.
- Exported files are downloaded through the browser, normally into the browser's configured Downloads folder.

## Deterministic QA

`Run QA` checks the current target text for the pilot defaults: two lines, a soft 40 graphemes per line, 17 graphemes per second, 1-7 second duration, and source cue overlap. These checks create warnings only and never modify source timing.

## Experiment Report

`Experiment report` downloads a versioned JSON file containing:

- Source filename, format, cue count, and SHA-256 hash.
- Harness/system/provider version fields.
- Elapsed and active edit time, keyboard actions, edit events, approval changes, and changed cue count.
- Preparation and QA summaries.
- Source and final cue text, timings, approval state, and warning codes for evaluator scoring.

Reports download locally and are not retained by the server. The current condition is `manual-source-copy`; provider/model/latency remain `null`, and provider usage/cost remain zero until a live adapter is explicitly approved and configured.

## Blinded Three-System Package

The example manifest uses only the synthetic repository fixtures:

```sh
PYTHONPATH=experiment/src python3 -m sinhalasub.experiment_cli \
  experiment/examples/blinded-manifest.json \
  /tmp/sinhalasub-evaluators.zip \
  --key /tmp/sinhalasub-confidential-key.json \
  --allow-not-ready-freeze
```

The manifest requires an experiment ID, integer seed, source file, provenance, rights basis, an audited system-freeze manifest, a complete system-run capture, and exactly three unique system outputs. Packaging rejects a mismatched source, seed, system set, or captured output hash. All paths are resolved relative to the manifest. The override above accepts only the explicitly synthetic dry-run freeze/capture; omit it for a real experiment.

Give evaluators only the ZIP. The separate key contains the system-freeze ID/hash, system identities, metadata, hashes, seed, and per-block candidate mappings; do not distribute it to evaluators. Re-running identical inputs creates identical package bytes.

## Confidential Evaluation Analysis

Evaluator responses use the eight 1-5 rubric dimensions embedded in the package, select exactly one preferred candidate per block, and may allocate critical counts across the controlled error categories. The repository includes three synthetic dry-run responses tied to the example package; their original aggregate errors remain `unclassified` rather than being categorized retrospectively.

After building the package and key above, validate and aggregate the responses:

```sh
PYTHONPATH=experiment/src python3 -m sinhalasub.evaluation_cli \
  /tmp/sinhalasub-evaluators.zip \
  /tmp/sinhalasub-confidential-key.json \
  experiment/examples/responses/evaluator-1.json \
  experiment/examples/responses/evaluator-2.json \
  experiment/examples/responses/evaluator-3.json \
  --output /tmp/sinhalasub-confidential-analysis.json
```

The output contains unblinded system-level rubric means, preference rates with 95% Wilson intervals, categorized critical-error totals, Fleiss' kappa, and confidential genre/challenge strata. Genre and challenge tags exist only in the key, not the evaluator ZIP. Keep both the key and analysis confidential until evaluator scoring is locked.

## Paired Editing-Time Analysis

Join versioned review reports by pseudonymous reviewer and asset under the baseline and contextual conditions:

```sh
PYTHONPATH=experiment/src python3 -m sinhalasub.editing_cli \
  experiment/examples/editing-session-manifest.json \
  --output /tmp/sinhalasub-editing-analysis.json \
  --allow-not-ready
```

The confidential manifest embeds each original `sinhalasub.experiment-report.v1` with its assignment. The audit rejects missing pairs, duplicate assignments or reports, source substitutions, invalid telemetry, and fewer than three reviewers. It reports median active editing time by system, the paired median proportional reduction, and a seeded 95% bootstrap interval. The synthetic example passes the 25% metric but remains not ready; `--allow-not-ready` is only a dry-run control.

## Evaluation Corpus Audit

Audit the small synthetic corpus manifest while explicitly allowing its expected not-ready status:

```sh
PYTHONPATH=experiment/src python3 -m sinhalasub.corpus_cli \
  experiment/examples/corpus-manifest.json \
  --output /tmp/sinhalasub-corpus-audit.json \
  --allow-not-ready
```

Without `--allow-not-ready`, the command exits with status 2 until a valid corpus reaches all frozen composition thresholds. Invalid provenance/rights/annotation/structure data always exits with status 1. The audit records relative paths and normalized hashes; it verifies manifest controls but does not replace legal review of rights evidence.

Every asset must reference at least two `sinhalasub.corpus-annotation.v1` JSON files and one `sinhalasub.corpus-adjudication.v1` JSON file. Annotation records bind the normalized source hash and all challenge cues. The adjudication record must list the canonical SHA-256 of every annotation input, so changing or substituting an annotation invalidates the corpus audit. Checked-in records under `examples/annotations/` are synthetic protocol fixtures only.

Generate a source-bound template separately for each declared annotator:

```sh
PYTHONPATH=experiment/src python3 -m sinhalasub.annotation_cli annotation \
  experiment/examples/corpus-manifest.json synthetic-dialogue-sample \
  synthetic-annotator-1 /tmp/sinhalasub-annotation.json
```

After all independent records are complete, generate a neutral-label adjudication template. The command rejects incomplete, stale, duplicate, or undeclared annotation inputs:

```sh
PYTHONPATH=experiment/src python3 -m sinhalasub.annotation_cli adjudication \
  experiment/examples/corpus-manifest.json synthetic-dialogue-sample \
  experiment/examples/annotations/synthetic-annotator-1.json \
  experiment/examples/annotations/synthetic-annotator-2.json \
  --output /tmp/sinhalasub-adjudication.json
```

## System Freeze Audit

Audit the synthetic three-role system freeze without treating it as experiment-ready:

```sh
PYTHONPATH=experiment/src python3 -m sinhalasub.system_freeze_cli \
  experiment/examples/system-freeze-manifest.json \
  --output /tmp/sinhalasub-system-freeze-audit.json \
  --allow-not-ready
```

The manifest pins the corpus hash, randomisation seed, rubric, three required system roles, provider/model/adapter versions, instruction hashes, and data-policy review fields. A real freeze requires a ready corpus and `approved` provider policies; `dry_run` records always remain not ready.

## System Run Capture

Audit captured outputs and metering for every frozen system/corpus pair:

```sh
PYTHONPATH=experiment/src python3 -m sinhalasub.run_capture_cli \
  experiment/examples/run-capture-manifest.json \
  --output /tmp/sinhalasub-run-audit.json \
  --allow-not-ready
```

Each run records a timezone-aware generation time, latency, provider-specific usage unit, USD cost, and output path. The audit verifies complete asset/system coverage and cue/timestamp integrity. Usage totals remain grouped by unit. The synthetic capture is valid protocol evidence but cannot authorize a real experiment.

## Phase 0 Decision Gate

Apply the frozen product thresholds to the hash-bound synthetic evidence record:

```sh
PYTHONPATH=experiment/src python3 -m sinhalasub.decision_cli \
  experiment/examples/decision-manifest.json \
  --output /tmp/sinhalasub-decision-audit.json \
  --allow-not-authorized
```

The synthetic evidence intentionally places each metric just beyond the go threshold, but the result remains `not-authorized` because the linked run is not ready and the record is marked synthetic. A real outcome additionally requires at least three translators, 30 viewers, two independent reviewers, approved protocol, reviewed analysis, and a ready corpus/freeze/run chain. Never use the override to claim a real decision.

Normalize a subtitle file:

```sh
PYTHONPATH=experiment/src python3 -m sinhalasub.cli input.srt output.srt
```

The output format is selected from the output extension. Input and output formats must match in this first slice.

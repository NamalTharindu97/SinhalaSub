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

The preparation step accepts comma-separated confirmed character names. It also protects detected numbers, dates, currencies, and URLs. The repository currently includes only an echo provider for contract testing; no live AI provider is configured.

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
  --key /tmp/sinhalasub-confidential-key.json
```

The manifest requires an experiment ID, integer seed, source file, provenance, rights basis, and exactly three unique system outputs. All subtitle paths are resolved relative to the manifest.

Give evaluators only the ZIP. The separate key contains system identities, metadata, hashes, seed, and per-block candidate mappings; do not distribute it to evaluators. Re-running identical inputs creates identical package bytes.

## Confidential Evaluation Analysis

Evaluator responses use the eight 1-5 rubric dimensions embedded in the package and select exactly one preferred candidate per block. The repository includes three synthetic dry-run responses tied to the example package.

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

The output contains unblinded system-level rubric means, preference rates with 95% Wilson intervals, critical-error totals, and Fleiss' kappa for preference agreement. Keep both the key and analysis confidential until evaluator scoring is locked.

Normalize a subtitle file:

```sh
PYTHONPATH=experiment/src python3 -m sinhalasub.cli input.srt output.srt
```

The output format is selected from the output extension. Input and output formats must match in this first slice.

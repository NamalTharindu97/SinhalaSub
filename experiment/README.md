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

Normalize a subtitle file:

```sh
PYTHONPATH=experiment/src python3 -m sinhalasub.cli input.srt output.srt
```

The output format is selected from the output extension. Input and output formats must match in this first slice.

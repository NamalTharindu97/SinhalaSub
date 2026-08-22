# Phase 0 Experiment Harness

This package provides the subtitle integrity foundation for the controlled English-to-Sinhala translation experiment. It currently parses and normalizes SRT/WebVTT files without changing cue timing.

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

Then open `http://127.0.0.1:8765`. The workspace accepts an SRT/WebVTT file, keeps timing locked, lets you edit target text, and exports a reviewed copy. It runs locally and does not translate text with AI yet.

Normalize a subtitle file:

```sh
PYTHONPATH=experiment/src python3 -m sinhalasub.cli input.srt output.srt
```

The output format is selected from the output extension. Input and output formats must match in this first slice.

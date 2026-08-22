# Repository Status

- Product research is in `docs/AI_Powered_English_to_Sinhala_Subtitle_Research_Report.docx`; the delivery plan starts at `docs/plans/README.md`.
- The only implementation is the Python 3.9+ standard-library Phase 0 harness under `experiment/`; its decision and limits are in `docs/decisions/0001-experiment-tool-shape.md`. Next.js/FastAPI/PostgreSQL/Redis remain unapproved production candidates.
- Translation preparation is provider-neutral and has no live AI integration; `EchoProvider` only verifies cue/placeholder contracts. See `docs/decisions/0002-translation-provider-contract.md` before adding an adapter.
- Execute Phase 0 validation and the controlled translation experiment before building the full SaaS; the go/no-go thresholds and pivot outcomes are in `docs/plans/02-validation-plan.md`.
- The MVP is private, authorised-use, subtitle-only, and human-in-the-loop. Preserve cue IDs/count/timestamps, keep global training off by default, and do not add video upload, public subtitle distribution, unlicensed scraping, or unlicensed training data.

# Experiment Commands

- Run all tests: `python3 -m unittest discover -s experiment/tests -v`.
- Run one module: `python3 -m unittest experiment.tests.test_subtitles -v`.
- Start the local GUI: `PYTHONPATH=experiment/src python3 -m sinhalasub.web --open` (defaults to `http://127.0.0.1:8765`).
- Normalize a file: `PYTHONPATH=experiment/src python3 -m sinhalasub.cli input.srt output.srt` (use matching SRT or WebVTT extensions).
- Test fixtures must be synthetic, commissioned, licensed, or public-domain; record their provenance beside the fixtures.

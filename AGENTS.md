# Scope And Boundaries

- The only implementation is the Python 3.9+ standard-library Phase 0 harness in `experiment/`; there is no dependency manifest, install step, CI workflow, or approved production stack. Start with `experiment/README.md` and `docs/plans/README.md`.
- Do not build the proposed Next.js/FastAPI/PostgreSQL/Redis SaaS until the real Phase 0 decision gate passes. Current corpus, providers, runs, evaluator records, and decision evidence are synthetic protocol fixtures and remain `not-authorized`.
- There is no live AI adapter. `EchoProvider` only contract-tests cue IDs and protected placeholders; read `docs/decisions/0002-translation-provider-contract.md` before connecting a provider.
- Preserve subtitle cue IDs, count, order, and timestamps. The product remains private, authorised-use, subtitle-only, human-reviewed, and training-off by default; do not add video upload, public distribution, unlicensed scraping, or unlicensed training data.
- Fixtures must be synthetic, commissioned, licensed, or public-domain, with provenance recorded beside them. Repository visibility being public does not relax product/data privacy constraints.

# Verification

- Run from the repository root. Full gate: `python3 -m unittest discover -s experiment/tests -v`, then `python3 -m compileall -q experiment/src experiment/tests`, then `git diff --check`.
- Focus a module: `python3 -m unittest experiment.tests.test_subtitles -v`; focus a method: `python3 -m unittest experiment.tests.test_subtitles.SrtTests.test_parses_canonical_cues -v`.
- Start the non-persistent local GUI with `PYTHONPATH=experiment/src python3 -m sinhalasub.web --open` (`http://127.0.0.1:8765`). Uploads stay in memory, reload clears state, and exports are browser downloads.
- Normalize matching SRT/WebVTT formats with `PYTHONPATH=experiment/src python3 -m sinhalasub.cli input.srt output.srt`.

# Experiment Chain

- Evidence is hash-linked in this order: corpus/annotations -> system freeze -> run capture -> blinded package/key -> evaluator analysis and paired editing analysis -> decision evidence. Editing an upstream fixture invalidates hashes in downstream manifests or responses; regenerate/update the chain rather than bypassing checks.
- Corpus audit: `PYTHONPATH=experiment/src python3 -m sinhalasub.corpus_cli experiment/examples/corpus-manifest.json --output /tmp/sinhalasub-corpus-audit.json --allow-not-ready`.
- Annotation templates: `PYTHONPATH=experiment/src python3 -m sinhalasub.annotation_cli annotation ...`; adjudication accepts only completed independent records via `PYTHONPATH=experiment/src python3 -m sinhalasub.annotation_cli adjudication ...`.
- Freeze audit: `PYTHONPATH=experiment/src python3 -m sinhalasub.system_freeze_cli experiment/examples/system-freeze-manifest.json --output /tmp/sinhalasub-system-freeze-audit.json --allow-not-ready`.
- Run audit: `PYTHONPATH=experiment/src python3 -m sinhalasub.run_capture_cli experiment/examples/run-capture-manifest.json --output /tmp/sinhalasub-run-audit.json --allow-not-ready`.
- Build the synthetic evaluator package/key: `PYTHONPATH=experiment/src python3 -m sinhalasub.experiment_cli experiment/examples/blinded-manifest.json /tmp/sinhalasub-evaluators.zip --key /tmp/sinhalasub-confidential-key.json --allow-not-ready-freeze`. Never distribute the key to evaluators.
- Analyze responses only after rebuilding that exact package/key: `PYTHONPATH=experiment/src python3 -m sinhalasub.evaluation_cli /tmp/sinhalasub-evaluators.zip /tmp/sinhalasub-confidential-key.json experiment/examples/responses/evaluator-1.json experiment/examples/responses/evaluator-2.json experiment/examples/responses/evaluator-3.json --output /tmp/sinhalasub-confidential-analysis.json`.
- Analyze paired review reports with `PYTHONPATH=experiment/src python3 -m sinhalasub.editing_cli experiment/examples/editing-session-manifest.json --output /tmp/sinhalasub-editing-analysis.json --allow-not-ready`.
- Decision audit: `PYTHONPATH=experiment/src python3 -m sinhalasub.decision_cli experiment/examples/decision-manifest.json --output /tmp/sinhalasub-decision-audit.json --allow-not-authorized`; the synthetic outcome must remain `not-authorized`.
- `--allow-not-ready`, `--allow-not-ready-freeze`, and `--allow-not-authorized` are synthetic dry-run controls only. Never use them to approve a real corpus, provider freeze, run, or product decision.

# Git Workflow

- Develop completed slices on named feature branches, push the feature branch, merge the verified branch into `main` with a normal merge commit, and push `main`.
- Keep feature branches locally and remotely after merging; do not delete them.

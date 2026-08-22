# Repository Status

- The repository contains planning only: product research is in `docs/AI_Powered_English_to_Sinhala_Subtitle_Research_Report.docx`, and the executable delivery plan starts at `docs/plans/README.md`.
- No application entrypoint, manifest, lockfile, developer commands, CI, or toolchain exists yet. Next.js/FastAPI/PostgreSQL/Redis in the plan are candidates requiring ADRs, not installed choices.
- Execute Phase 0 validation and the controlled translation experiment before building the full SaaS; the go/no-go thresholds and pivot outcomes are in `docs/plans/02-validation-plan.md`.
- The MVP is private, authorised-use, subtitle-only, and human-in-the-loop. Preserve cue IDs/count/timestamps, keep global training off by default, and do not add video upload, public subtitle distribution, unlicensed scraping, or unlicensed training data.

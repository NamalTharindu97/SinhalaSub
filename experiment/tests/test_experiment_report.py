from dataclasses import replace
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sinhalasub import REPORT_SCHEMA, SubtitleFormat, build_experiment_report, parse_subtitle  # noqa: E402


SOURCE = (
    "1\n00:00:01,000 --> 00:00:03,000\nHello.\n\n"
    "2\n00:00:04,000 --> 00:00:06,000\nStay here.\n"
)


class ExperimentReportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = parse_subtitle(SOURCE, SubtitleFormat.SRT)
        changed_cue = replace(self.source.cues[0], text="ආයුබෝවන්.")
        self.target = replace(self.source, cues=(changed_cue, self.source.cues[1]))
        self.session = {
            "started_at": "2026-08-22T10:00:00Z",
            "ended_at": "2026-08-22T10:01:00Z",
            "elapsed_ms": 60_000,
            "active_edit_ms": 45_000,
            "keyboard_actions": 12,
            "edit_events": 3,
            "approval_changes": 1,
            "approved_cue_ids": ["1"],
        }

    def test_builds_versioned_report_from_computed_document_changes(self) -> None:
        report = build_experiment_report(
            self.source,
            self.target,
            "/hidden/path/sample.srt",
            self.session,
            preparation={
                "blocks": [{"id": "block-1"}],
                "protected_count": 2,
                "profile": {"style": "formal", "character_term_count": 2, "glossary_term_count": 1},
            },
            quality={
                "counts": {"high": 1, "medium": 0, "low": 0},
                "warnings_by_cue": {"1": [{"code": "READING_SPEED"}]},
            },
        )

        self.assertEqual(REPORT_SCHEMA, report["schema_version"])
        self.assertEqual("sample.srt", report["source"]["filename"])
        self.assertEqual(64, len(report["source"]["sha256"]))
        self.assertEqual(1, report["review"]["changed_cue_count"])
        self.assertEqual(1, report["review"]["approved_cue_count"])
        self.assertEqual("manual-source-copy", report["system"]["condition"])
        self.assertIsNone(report["system"]["provider"])
        self.assertEqual("formal", report["system"]["style"])
        self.assertEqual(1, report["system"]["glossary_terms"])
        self.assertEqual("ආයුබෝවන්.", report["cues"][0]["final_text"])
        self.assertEqual(["READING_SPEED"], report["cues"][0]["warning_codes"])

    def test_rejects_timing_changes(self) -> None:
        changed_timing = replace(
            self.target,
            cues=(replace(self.target.cues[0], start_ms=1100), self.target.cues[1]),
        )

        with self.assertRaisesRegex(ValueError, "structures must match"):
            build_experiment_report(self.source, changed_timing, "sample.srt", self.session)

    def test_rejects_impossible_active_time(self) -> None:
        self.session["active_edit_ms"] = 60_001

        with self.assertRaisesRegex(ValueError, "cannot exceed"):
            build_experiment_report(self.source, self.target, "sample.srt", self.session)


if __name__ == "__main__":
    unittest.main()

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sinhalasub import SubtitleFormat, check_document, grapheme_count, parse_subtitle  # noqa: E402


class GraphemeTests(unittest.TestCase):
    def test_keeps_sinhala_marks_with_their_base_character(self) -> None:
        self.assertEqual(3, grapheme_count("සිංහල"))


class QualityTests(unittest.TestCase):
    def test_reports_readability_and_source_timing_without_mutation(self) -> None:
        source = (
            "1\n00:00:01,000 --> 00:00:02,000\n"
            "This line is deliberately much longer than the configured subtitle limit.\n"
            "Second line.\nThird line.\n\n"
            "2\n00:00:01,900 --> 00:00:10,000\nOverlap\n"
        )
        document = parse_subtitle(source, SubtitleFormat.SRT)

        warnings = check_document(document)
        codes = {warning.code for warning in warnings}

        self.assertTrue({"TOO_MANY_LINES", "LONG_LINE", "READING_SPEED", "LONG_DURATION", "SOURCE_OVERLAP"} <= codes)
        self.assertEqual(1000, document.cues[0].start_ms)
        self.assertEqual(1900, document.cues[1].start_ms)

    def test_clean_short_cue_has_no_warnings(self) -> None:
        document = parse_subtitle(
            "1\n00:00:01,000 --> 00:00:04,000\nShort line.\n",
            SubtitleFormat.SRT,
        )

        self.assertEqual((), check_document(document))


if __name__ == "__main__":
    unittest.main()

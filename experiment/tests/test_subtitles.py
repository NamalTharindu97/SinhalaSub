from pathlib import Path
import sys
import unicodedata
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sinhalasub import (  # noqa: E402
    SubtitleError,
    SubtitleFormat,
    parse_subtitle,
    serialize_subtitle,
)


FIXTURES = Path(__file__).parent / "fixtures"


class SrtTests(unittest.TestCase):
    def test_parses_canonical_cues(self) -> None:
        document = parse_subtitle(
            (FIXTURES / "sample.srt").read_text(encoding="utf-8"),
            SubtitleFormat.SRT,
        )

        self.assertEqual(3, len(document.cues))
        self.assertEqual(("1", "2", "3"), tuple(cue.id for cue in document.cues))
        self.assertEqual(1250, document.cues[0].start_ms)
        self.assertEqual(3500, document.cues[0].end_ms)
        self.assertEqual("I will not.\nThis is important.", document.cues[1].text)
        self.assertEqual(3_723_004, document.cues[2].start_ms)

    def test_normalized_round_trip_preserves_structure(self) -> None:
        source = (FIXTURES / "sample.srt").read_text(encoding="utf-8")
        first = parse_subtitle(source, SubtitleFormat.SRT)
        second = parse_subtitle(serialize_subtitle(first), SubtitleFormat.SRT)

        self.assertEqual(first, second)

    def test_preserves_non_contiguous_numeric_ids(self) -> None:
        source = "2\n00:00:01,000 --> 00:00:02,000\nHello\n"

        document = parse_subtitle(source, SubtitleFormat.SRT)

        self.assertEqual("2", document.cues[0].id)
        self.assertEqual(document, parse_subtitle(serialize_subtitle(document), SubtitleFormat.SRT))


class WebVttTests(unittest.TestCase):
    def test_preserves_header_ids_and_settings(self) -> None:
        document = parse_subtitle(
            (FIXTURES / "sample.vtt").read_text(encoding="utf-8"),
            SubtitleFormat.WEBVTT,
        )

        self.assertEqual(("Kind: captions", "Language: en"), document.header)
        self.assertEqual("- SinhalaSub synthetic fixture", document.webvtt_description)
        self.assertEqual(("intro-1", "intro-2"), tuple(cue.id for cue in document.cues))
        self.assertEqual("align:start position:10%", document.cues[0].settings)
        self.assertEqual(1250, document.cues[0].start_ms)

    def test_normalized_round_trip_preserves_structure(self) -> None:
        source = (FIXTURES / "sample.vtt").read_text(encoding="utf-8")
        first = parse_subtitle(source, SubtitleFormat.WEBVTT)
        second = parse_subtitle(serialize_subtitle(first), SubtitleFormat.WEBVTT)

        self.assertEqual(first, second)

    def test_rejects_unsupported_style_blocks(self) -> None:
        source = "WEBVTT\n\nSTYLE\n::cue { color: lime; }\n"

        with self.assertRaisesRegex(SubtitleError, "UNSUPPORTED_BLOCK"):
            parse_subtitle(source, SubtitleFormat.WEBVTT)


class ValidationTests(unittest.TestCase):
    def test_normalizes_working_text_to_nfc(self) -> None:
        decomposed = unicodedata.normalize("NFD", "සිංහල")
        source = f"1\n00:00:01,000 --> 00:00:02,000\n{decomposed}\n"

        document = parse_subtitle(source, SubtitleFormat.SRT)

        self.assertTrue(unicodedata.is_normalized("NFC", document.cues[0].text))

    def test_rejects_end_before_start(self) -> None:
        source = "1\n00:00:02,000 --> 00:00:01,000\nHello\n"

        with self.assertRaisesRegex(SubtitleError, "INVALID_TIMING"):
            parse_subtitle(source, SubtitleFormat.SRT)

    def test_rejects_nul_content(self) -> None:
        with self.assertRaisesRegex(SubtitleError, "INVALID_TEXT"):
            parse_subtitle("WEBVTT\n\n\x00", SubtitleFormat.WEBVTT)


if __name__ == "__main__":
    unittest.main()

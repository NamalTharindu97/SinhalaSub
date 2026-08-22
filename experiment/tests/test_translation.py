from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sinhalasub import (  # noqa: E402
    EchoProvider,
    SubtitleError,
    SubtitleFormat,
    TranslationCandidate,
    parse_subtitle,
    prepare_document,
    protect_text,
    restore_text,
    run_translation,
)


class ProtectionTests(unittest.TestCase):
    def test_protects_confirmed_names_and_factual_values(self) -> None:
        source = "Will paid USD 1,250.50 on 2026-08-22. See https://example.test/case"

        protected, values = protect_text(source, confirmed_names=["Will"])

        self.assertNotIn("Will", protected)
        self.assertNotIn("USD 1,250.50", protected)
        self.assertNotIn("2026-08-22", protected)
        self.assertEqual(("NAME", "CURRENCY", "DATE", "URL"), tuple(item.kind for item in values))
        self.assertEqual(source, restore_text(protected, values))

    def test_restore_rejects_missing_or_duplicate_placeholders(self) -> None:
        protected, values = protect_text("Rose has 2 keys.", confirmed_names=["Rose"])

        with self.assertRaisesRegex(SubtitleError, "PROTECTED_VALUE_MISMATCH"):
            restore_text(protected.replace(values[0].placeholder, ""), values)

        with self.assertRaisesRegex(SubtitleError, "PROTECTED_VALUE_MISMATCH"):
            restore_text(f"{protected} {values[0].placeholder}", values)

    def test_does_not_treat_lowercase_common_word_as_confirmed_name(self) -> None:
        protected, values = protect_text("Will said I will stay.", confirmed_names=["Will"])

        self.assertEqual(1, len(values))
        self.assertEqual("NAME", values[0].kind)
        self.assertIn("I will stay", protected)


class ContextTests(unittest.TestCase):
    def test_groups_by_gap_and_cue_limit_with_bounded_context(self) -> None:
        source = (
            "1\n00:00:01,000 --> 00:00:02,000\nOne\n\n"
            "2\n00:00:03,000 --> 00:00:04,000\nTwo\n\n"
            "3\n00:00:20,000 --> 00:00:21,000\nThree\n"
        )
        document = parse_subtitle(source, SubtitleFormat.SRT)

        cues, blocks = prepare_document(document, max_cues_per_block=2, max_gap_ms=6000)

        self.assertEqual(3, len(cues))
        self.assertEqual(("1", "2"), blocks[0].cue_ids)
        self.assertEqual(("3",), blocks[0].context_after)
        self.assertEqual(("1", "2"), blocks[1].context_before)
        self.assertEqual(("3",), blocks[1].cue_ids)


class ProviderContractTests(unittest.TestCase):
    def setUp(self) -> None:
        source = "1\n00:00:01,000 --> 00:00:02,000\nWill has 2 keys.\n"
        document = parse_subtitle(source, SubtitleFormat.SRT)
        self.cues, self.blocks = prepare_document(document, confirmed_names=["Will"])

    def test_echo_provider_proves_protected_round_trip(self) -> None:
        candidates = run_translation(self.cues, self.blocks, EchoProvider())

        self.assertEqual("Will has 2 keys.", candidates[0].text)

    def test_rejects_provider_cue_id_changes(self) -> None:
        class WrongIdProvider:
            name = "wrong-id"

            def translate(self, request):
                return (TranslationCandidate(cue_id="changed", text=request.cues[0].protected_text),)

        with self.assertRaisesRegex(SubtitleError, "INVALID_PROVIDER_RESPONSE"):
            run_translation(self.cues, self.blocks, WrongIdProvider())

    def test_rejects_provider_that_drops_protected_value(self) -> None:
        class MissingValueProvider:
            name = "missing-value"

            def translate(self, request):
                return (TranslationCandidate(cue_id="1", text="No placeholders"),)

        with self.assertRaisesRegex(SubtitleError, "PROTECTED_VALUE_MISMATCH"):
            run_translation(self.cues, self.blocks, MissingValueProvider())


if __name__ == "__main__":
    unittest.main()

import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sinhalasub import (  # noqa: E402
    CORPUS_SCHEMA,
    REQUIRED_CHALLENGES,
    REQUIRED_GENRES,
    audit_corpus_manifest,
)


class CorpusAuditTests(unittest.TestCase):
    def test_synthetic_example_is_valid_but_cannot_pass_readiness_gate(self) -> None:
        audit = audit_corpus_manifest(ROOT / "examples" / "corpus-manifest.json")

        self.assertTrue(audit["valid"])
        self.assertFalse(audit["ready"])
        self.assertEqual(3, audit["counts"]["cues"])
        self.assertTrue(any("1,500-2,000" in failure for failure in audit["readiness_failures"]))
        self.assertNotIn(str(ROOT.resolve()), json.dumps(audit))

    def test_reports_missing_rights_and_annotation_controls_as_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subtitle = root / "sample.srt"
            subtitle.write_text("1\n00:00:01,000 --> 00:00:02,000\nHello.\n", encoding="utf-8")
            manifest = {
                "schema_version": CORPUS_SCHEMA,
                "corpus_id": "invalid",
                "assets": [
                    {
                        "id": "sample",
                        "genre": "modern-drama",
                        "split": "development",
                        "source": "sample.srt",
                        "reference": "sample.srt",
                        "adjudicated_reference": "sample.srt",
                        "provenance": "Synthetic",
                        "rights": {},
                        "annotators": ["one"],
                        "adjudicator": "",
                        "acceptable_alternatives_documented": False,
                        "challenges": [],
                    }
                ],
            }
            path = root / "manifest.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")

            audit = audit_corpus_manifest(path)

            self.assertFalse(audit["valid"])
            self.assertTrue(any("rights basis" in error for error in audit["errors"]))
            self.assertTrue(any("two unique annotator" in error for error in audit["errors"]))
            self.assertTrue(any("acceptable alternatives" in error for error in audit["errors"]))

    def test_full_synthetic_manifest_meets_frozen_readiness_thresholds(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "RIGHTS.md").write_text("Synthetic test rights evidence.", encoding="utf-8")
            assets = []
            for asset_number, genre in enumerate(REQUIRED_GENRES, start=1):
                source_name = f"source-{asset_number}.srt"
                reference_name = f"reference-{asset_number}.srt"
                adjudicated_name = f"adjudicated-{asset_number}.srt"
                source = self._subtitle(250, f"Source {asset_number}")
                reference = self._subtitle(250, f"Reference {asset_number}")
                adjudicated = self._subtitle(250, f"Adjudicated {asset_number}")
                (root / source_name).write_text(source, encoding="utf-8")
                (root / reference_name).write_text(reference, encoding="utf-8")
                (root / adjudicated_name).write_text(adjudicated, encoding="utf-8")
                challenges = [
                    {
                        "cue_id": str(index),
                        "tags": [REQUIRED_CHALLENGES[(index - 1) % len(REQUIRED_CHALLENGES)]],
                    }
                    for index in range(1, 26)
                ]
                assets.append(
                    {
                        "id": f"asset-{asset_number}",
                        "genre": genre,
                        "split": "holdout" if asset_number == 6 else "development",
                        "source": source_name,
                        "reference": reference_name,
                        "adjudicated_reference": adjudicated_name,
                        "provenance": "Commissioned synthetic test fixture.",
                        "rights": {"basis": "Commissioned for evaluation.", "evidence": "RIGHTS.md"},
                        "annotators": ["annotator-a", "annotator-b"],
                        "adjudicator": "adjudicator-c",
                        "acceptable_alternatives_documented": True,
                        "reference_independently_authored": True,
                        "private_holdout": asset_number == 6,
                        "challenges": challenges,
                    }
                )
            manifest_path = root / "manifest.json"
            manifest_path.write_text(
                json.dumps({"schema_version": CORPUS_SCHEMA, "corpus_id": "ready", "assets": assets}),
                encoding="utf-8",
            )

            audit = audit_corpus_manifest(manifest_path)

            self.assertTrue(audit["valid"], audit["errors"])
            self.assertTrue(audit["ready"], audit["readiness_failures"])
            self.assertEqual(1500, audit["counts"]["cues"])
            self.assertEqual(150, audit["counts"]["challenge_cues"])
            self.assertEqual(6, audit["counts"]["genres"])
            self.assertEqual(2, audit["counts"]["splits"])

    @staticmethod
    def _subtitle(cue_count: int, prefix: str) -> str:
        blocks = []
        for index in range(1, cue_count + 1):
            start_ms = index * 2000
            end_ms = start_ms + 1000
            blocks.append(
                f"{index}\n{CorpusAuditTests._timestamp(start_ms)} --> "
                f"{CorpusAuditTests._timestamp(end_ms)}\n{prefix} cue {index}."
            )
        return "\n\n".join(blocks) + "\n"

    @staticmethod
    def _timestamp(milliseconds: int) -> str:
        seconds_total, millis = divmod(milliseconds, 1000)
        minutes_total, seconds = divmod(seconds_total, 60)
        hours, minutes = divmod(minutes_total, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


if __name__ == "__main__":
    unittest.main()

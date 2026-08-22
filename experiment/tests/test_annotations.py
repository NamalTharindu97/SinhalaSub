import copy
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sinhalasub import (  # noqa: E402
    ADJUDICATION_SCHEMA,
    ANNOTATION_SCHEMA,
    annotation_digest,
    validate_adjudication_record,
    validate_annotation_record,
)


class AnnotationContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.challenge = {"cue_id": "1", "tags": ["negation"]}
        self.annotation = {
            "schema_version": ANNOTATION_SCHEMA,
            "corpus_id": "corpus",
            "asset_id": "asset",
            "source_sha256": "source-hash",
            "annotator_id": "annotator-a",
            "cues": [
                {
                    "cue_id": "1",
                    "translation": "Translation",
                    "acceptable_alternatives": [],
                    "tags": ["negation"],
                    "notes": "",
                }
            ],
        }

    def test_valid_annotation_is_accepted(self) -> None:
        errors = validate_annotation_record(
            self.annotation, "corpus", "asset", "source-hash", [self.challenge], {"annotator-a"}
        )

        self.assertEqual([], errors)

    def test_annotation_rejects_stale_source_and_incomplete_cues(self) -> None:
        record = copy.deepcopy(self.annotation)
        record["source_sha256"] = "stale"
        record["cues"] = []

        errors = validate_annotation_record(
            record, "corpus", "asset", "source-hash", [self.challenge], {"annotator-a"}
        )

        self.assertTrue(any("source hash" in error for error in errors))
        self.assertTrue(any("every challenge cue" in error for error in errors))

    def test_adjudication_rejects_substituted_annotation_inputs(self) -> None:
        annotation_hash = annotation_digest(self.annotation)
        adjudication = {
            "schema_version": ADJUDICATION_SCHEMA,
            "corpus_id": "corpus",
            "asset_id": "asset",
            "source_sha256": "source-hash",
            "adjudicator_id": "adjudicator",
            "input_annotation_sha256": ["substituted"],
            "cues": self.annotation["cues"],
        }

        errors = validate_adjudication_record(
            adjudication,
            "corpus",
            "asset",
            "source-hash",
            [self.challenge],
            "adjudicator",
            {annotation_hash},
        )

        self.assertTrue(any("hash-link" in error for error in errors))

    def test_adjudication_rejects_non_string_hashes_without_crashing(self) -> None:
        adjudication = {
            "schema_version": ADJUDICATION_SCHEMA,
            "corpus_id": "corpus",
            "asset_id": "asset",
            "source_sha256": "source-hash",
            "adjudicator_id": "adjudicator",
            "input_annotation_sha256": [{"not": "a hash"}],
            "cues": self.annotation["cues"],
        }

        errors = validate_adjudication_record(
            adjudication, "corpus", "asset", "source-hash", [self.challenge], "adjudicator", {"expected"}
        )

        self.assertTrue(any("hash-link" in error for error in errors))


if __name__ == "__main__":
    unittest.main()

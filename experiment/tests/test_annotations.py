import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sinhalasub import (  # noqa: E402
    ADJUDICATION_SCHEMA,
    ANNOTATION_SCHEMA,
    annotation_digest,
    build_adjudication_template,
    build_annotation_template,
    validate_adjudication_record,
    validate_annotation_record,
)
from sinhalasub.annotation_cli import main as annotation_cli_main  # noqa: E402


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


class AnnotationWorkflowTests(unittest.TestCase):
    manifest_path = ROOT / "examples" / "corpus-manifest.json"

    def test_builds_source_bound_annotation_template(self) -> None:
        record = build_annotation_template(
            self.manifest_path, "synthetic-dialogue-sample", "synthetic-annotator-1"
        )

        self.assertEqual(ANNOTATION_SCHEMA, record["schema_version"])
        self.assertEqual("d21518baea97af5d9f343d5982a37110e53c01f2b1757d247ecaab7e28962766", record["source_sha256"])
        self.assertEqual("Will, leave the case here.", record["cues"][0]["source_text"])
        self.assertEqual("", record["cues"][0]["translation"])

    def test_builds_hash_linked_adjudication_template_without_annotator_ids(self) -> None:
        paths = [
            ROOT / "examples" / "annotations" / "synthetic-annotator-1.json",
            ROOT / "examples" / "annotations" / "synthetic-annotator-2.json",
        ]

        record = build_adjudication_template(self.manifest_path, "synthetic-dialogue-sample", paths)
        reversed_record = build_adjudication_template(
            self.manifest_path, "synthetic-dialogue-sample", list(reversed(paths))
        )

        self.assertEqual(ADJUDICATION_SCHEMA, record["schema_version"])
        self.assertEqual(record, reversed_record)
        self.assertEqual(2, len(record["input_annotation_sha256"]))
        self.assertEqual(["candidate-1", "candidate-2"], [item["label"] for item in record["cues"][0]["independent_candidates"]])
        self.assertNotIn("synthetic-annotator", json.dumps(record))

    def test_cli_writes_annotation_template(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "annotation.json"
            with patch.object(
                sys,
                "argv",
                [
                    "annotation_cli",
                    "annotation",
                    str(self.manifest_path),
                    "synthetic-dialogue-sample",
                    "synthetic-annotator-1",
                    str(output),
                ],
            ):
                status = annotation_cli_main()

            self.assertEqual(0, status)
            self.assertEqual(ANNOTATION_SCHEMA, json.loads(output.read_text(encoding="utf-8"))["schema_version"])

if __name__ == "__main__":
    unittest.main()

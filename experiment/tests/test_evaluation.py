from dataclasses import replace
import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sinhalasub import (  # noqa: E402
    RESPONSE_SCHEMA,
    RUBRIC_DIMENSIONS,
    SubtitleFormat,
    SystemOutput,
    aggregate_evaluator_responses,
    build_blinded_package,
    package_digest,
    parse_subtitle,
    write_blinded_package,
)
from sinhalasub.evaluation_cli import analyze_files  # noqa: E402
from sinhalasub.experiment_cli import build_from_manifest  # noqa: E402


SOURCE = (
    "1\n00:00:01,000 --> 00:00:02,000\nOne.\n\n"
    "2\n00:00:20,000 --> 00:00:21,000\nTwo.\n"
)


class EvaluationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = parse_subtitle(SOURCE, SubtitleFormat.SRT)
        systems = tuple(
            SystemOutput(
                id=f"system-{letter}",
                document=replace(
                    self.source,
                    cues=tuple(replace(cue, text=f"{letter}:{cue.text}") for cue in self.source.cues),
                ),
                metadata={},
            )
            for letter in ("a", "b", "c")
        )
        self.package, self.key = build_blinded_package(
            "evaluation-test",
            42,
            self.source,
            systems,
            "Synthetic",
            "Repository-authored",
            evaluation_metadata={
                "genre": "modern-drama",
                "challenge_tags_by_cue": {"1": ["idiom"], "2": ["negation"]},
            },
        )

    def response(self, evaluator_id: str, preferred_system: str = "system-c"):
        key_blocks = {block["block_id"]: block["labels"] for block in self.key["blocks"]}
        blocks = []
        for block in self.package["blocks"]:
            candidates = []
            for candidate in block["candidates"]:
                preferred = key_blocks[block["id"]][candidate["label"]] == preferred_system
                candidates.append(
                    {
                        "label": candidate["label"],
                        "scores": {dimension: 5 if preferred else 3 for dimension in RUBRIC_DIMENSIONS},
                        "critical_errors": 0 if preferred else 1,
                        "critical_error_categories": {} if preferred else {"context_meaning": 1},
                        "preferred": preferred,
                    }
                )
            blocks.append({"block_id": block["id"], "candidates": candidates})
        return {
            "schema_version": RESPONSE_SCHEMA,
            "experiment_id": self.package["experiment_id"],
            "package_sha256": package_digest(self.package),
            "evaluator_id": evaluator_id,
            "blocks": blocks,
        }

    def test_unblinds_and_aggregates_rubric_preference_and_agreement(self) -> None:
        responses = [self.response(f"evaluator-{number}") for number in range(1, 4)]

        analysis = aggregate_evaluator_responses(self.package, self.key, responses)

        by_system = {system["system_id"]: system for system in analysis["systems"]}
        self.assertEqual(3, analysis["evaluator_count"])
        self.assertEqual(2, analysis["block_count"])
        self.assertEqual(1.0, analysis["preference_fleiss_kappa"])
        self.assertEqual(1.0, by_system["system-c"]["preference_rate"])
        self.assertEqual(5.0, by_system["system-c"]["overall_rubric_mean"])
        self.assertEqual(0, by_system["system-c"]["critical_error_total"])
        self.assertEqual(0.0, by_system["system-a"]["preference_rate"])
        self.assertEqual(6, by_system["system-a"]["critical_error_categories"]["context_meaning"])
        strata = {(item["kind"], item["value"]): item for item in analysis["strata"]}
        self.assertIn(("genre", "modern-drama"), strata)
        self.assertIn(("challenge", "idiom"), strata)
        idiom_by_system = {
            system["system_id"]: system
            for system in strata[("challenge", "idiom")]["systems"]
        }
        self.assertEqual(3, idiom_by_system["system-a"]["critical_error_total"])

    def test_rejects_incomplete_candidate_scores(self) -> None:
        response = self.response("evaluator-1")
        del response["blocks"][0]["candidates"][0]["scores"]["accuracy"]

        with self.assertRaisesRegex(ValueError, "all rubric dimensions"):
            aggregate_evaluator_responses(self.package, self.key, [response])

    def test_rejects_multiple_preferences_in_one_block(self) -> None:
        response = self.response("evaluator-1")
        response["blocks"][0]["candidates"][0]["preferred"] = True
        response["blocks"][0]["candidates"][1]["preferred"] = True
        response["blocks"][0]["candidates"][2]["preferred"] = False

        with self.assertRaisesRegex(ValueError, "exactly one preferred"):
            aggregate_evaluator_responses(self.package, self.key, [response])

    def test_rejects_response_for_different_package(self) -> None:
        response = self.response("evaluator-1")
        response["package_sha256"] = "0" * 64

        with self.assertRaisesRegex(ValueError, "hash does not match"):
            aggregate_evaluator_responses(self.package, self.key, [response])

    def test_rejects_critical_error_category_total_mismatch(self) -> None:
        response = self.response("evaluator-1")
        response["blocks"][0]["candidates"][0]["critical_error_categories"] = {"terminology": 2}

        with self.assertRaisesRegex(ValueError, "must equal"):
            aggregate_evaluator_responses(self.package, self.key, [response])

    def test_cli_writes_confidential_analysis(self) -> None:
        responses = [self.response(f"evaluator-{number}") for number in range(1, 4)]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package_path = root / "package.zip"
            key_path = root / "key.json"
            output_path = root / "analysis.json"
            write_blinded_package(self.package, self.key, package_path, key_path)
            response_paths = []
            for number, response in enumerate(responses, start=1):
                path = root / f"response-{number}.json"
                path.write_text(json.dumps(response), encoding="utf-8")
                response_paths.append(path)

            analyze_files(package_path, key_path, response_paths, output_path)

            analysis = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(3, analysis["evaluator_count"])


class ExampleEvaluationTests(unittest.TestCase):
    def test_repository_dry_run_responses_match_example_package(self) -> None:
        manifest = ROOT / "examples" / "blinded-manifest.json"
        responses = sorted((ROOT / "examples" / "responses").glob("*.json"))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package_path = root / "evaluators.zip"
            key_path = root / "key.json"
            analysis_path = root / "analysis.json"
            build_from_manifest(manifest, package_path, key_path, allow_not_ready_freeze=True)

            analyze_files(package_path, key_path, responses, analysis_path)

            analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
            self.assertEqual(3, analysis["evaluator_count"])
            self.assertEqual(2, analysis["block_count"])


if __name__ == "__main__":
    unittest.main()

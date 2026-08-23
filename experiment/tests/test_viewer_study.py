import copy
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sinhalasub.viewer_study import analyze_viewer_responses, build_viewer_study  # noqa: E402


MANIFEST = ROOT / "examples" / "viewer-study-manifest.json"
RESPONSES = ROOT / "examples" / "viewer-responses.json"


class ViewerStudyTests(unittest.TestCase):
    def setUp(self):
        self.package, self.key = build_viewer_study(MANIFEST)
        self.responses = json.loads(RESPONSES.read_text(encoding="utf-8"))

    def test_build_keeps_systems_and_answers_out_of_package(self):
        serialized = json.dumps(self.package)

        self.assertNotIn("synthetic-baseline", serialized)
        self.assertNotIn("synthetic-contextual", serialized)
        self.assertNotIn("correct_option", serialized)
        self.assertEqual(self.key["assets"][0]["correct_options"], {"intent": 1, "location": 0})
        self.assertEqual({item["candidate_id"] for item in self.package["assets"][0]["candidates"]}, {"A", "B"})

    def test_analyzes_preference_comprehension_and_cloud_acceptance(self):
        analysis = analyze_viewer_responses(self.package, self.key, self.responses)

        self.assertTrue(analysis["valid"])
        self.assertFalse(analysis["evidence_ready"])
        self.assertEqual(analysis["viewer_count"], 30)
        self.assertEqual(analysis["contextual_preference_rate"], 0.6667)
        self.assertEqual(analysis["contextual_preference_ci_95"], [0.4878, 0.8077])
        self.assertTrue(analysis["threshold_passed"])
        self.assertEqual(analysis["comprehension"]["synthetic-baseline"]["rate"], 0.75)
        self.assertEqual(analysis["comprehension"]["synthetic-contextual"]["rate"], 0.9)
        self.assertEqual(analysis["cloud_upload_acceptance_rate"], 0.8)

    def test_rejects_duplicate_viewer_and_incomplete_answers(self):
        responses = copy.deepcopy(self.responses)
        responses["responses"][1]["viewer_id"] = "viewer-001"
        del responses["responses"][0]["assignments"][0]["answers"]["A"]["intent"]

        analysis = analyze_viewer_responses(self.package, self.key, responses)

        self.assertFalse(analysis["valid"])
        self.assertTrue(any("unique pseudonymous ID" in error for error in analysis["errors"]))
        self.assertTrue(any("incomplete answers" in error for error in analysis["errors"]))

    def test_rejects_substituted_package_and_invalid_order(self):
        package = copy.deepcopy(self.package)
        package["assets"][0]["candidates"][0]["subtitle"] += "changed"
        responses = copy.deepcopy(self.responses)
        responses["responses"][0]["assignments"][0]["presentation_order"] = ["A", "A"]

        analysis = analyze_viewer_responses(package, self.key, responses)

        self.assertFalse(analysis["valid"])
        self.assertTrue(any("key does not match" in error for error in analysis["errors"]))
        self.assertTrue(any("responses do not match" in error for error in analysis["errors"]))
        self.assertTrue(any("presentation order" in error for error in analysis["errors"]))

    def test_fewer_than_thirty_real_viewers_is_not_ready(self):
        key = copy.deepcopy(self.key)
        key["dry_run"] = False
        key["run_capture_ready"] = True
        responses = copy.deepcopy(self.responses)
        responses["responses"] = responses["responses"][:29]

        analysis = analyze_viewer_responses(self.package, key, responses)

        self.assertTrue(analysis["valid"])
        self.assertFalse(analysis["evidence_ready"])
        self.assertTrue(any("At least 30" in blocker for blocker in analysis["blockers"]))

    def test_complete_real_viewer_evidence_is_ready(self):
        key = copy.deepcopy(self.key)
        key["dry_run"] = False
        key["run_capture_ready"] = True

        analysis = analyze_viewer_responses(self.package, key, self.responses)

        self.assertTrue(analysis["evidence_ready"])

    def test_invalid_confidential_mapping_is_reported_without_crashing(self):
        key = copy.deepcopy(self.key)
        key["assets"][0]["candidate_systems"]["A"] = "unknown-system"

        analysis = analyze_viewer_responses(self.package, key, self.responses)

        self.assertFalse(analysis["valid"])
        self.assertTrue(any("invalid confidential mapping" in error for error in analysis["errors"]))


if __name__ == "__main__":
    unittest.main()

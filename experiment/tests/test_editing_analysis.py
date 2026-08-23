import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sinhalasub.editing_analysis import analyze_editing_sessions  # noqa: E402


EXAMPLE = ROOT / "examples" / "editing-session-manifest.json"


class EditingAnalysisTests(unittest.TestCase):
    def test_synthetic_pairs_pass_metric_but_not_readiness(self):
        analysis = analyze_editing_sessions(EXAMPLE)

        self.assertTrue(analysis["valid"])
        self.assertFalse(analysis["evidence_ready"])
        self.assertEqual(analysis["reviewer_count"], 3)
        self.assertEqual(analysis["pair_count"], 3)
        self.assertEqual(analysis["paired_median_reduction"], 0.3)
        self.assertEqual(analysis["paired_reduction_ci_95"], [0.25, 0.4])
        self.assertTrue(analysis["threshold_passed"])
        self.assertIn("Synthetic editing sessions", analysis["blockers"][0])

    def test_rejects_incomplete_pair(self):
        manifest = self._manifest()
        manifest["sessions"].pop()

        analysis = self._analyze(manifest)

        self.assertFalse(analysis["valid"])
        self.assertTrue(any("Incomplete" in error for error in analysis["errors"]))

    def test_rejects_duplicate_assignment_and_session_id(self):
        manifest = self._manifest()
        manifest["sessions"].append(copy.deepcopy(manifest["sessions"][0]))

        analysis = self._analyze(manifest)

        self.assertFalse(analysis["valid"])
        self.assertTrue(any("unique session ID" in error for error in analysis["errors"]))
        self.assertTrue(any("duplicates a reviewer/asset/system" in error for error in analysis["errors"]))

    def test_rejects_source_substitution_and_impossible_time(self):
        manifest = self._manifest()
        manifest["sessions"][1]["report"]["source"]["sha256"] = "2" * 64
        manifest["sessions"][1]["report"]["review"]["active_edit_ms"] = 96000

        analysis = self._analyze(manifest)

        self.assertFalse(analysis["valid"])
        self.assertTrue(any("same source" in error for error in analysis["errors"]))
        self.assertTrue(any("not exceed elapsed" in error for error in analysis["errors"]))

    def test_real_complete_pairs_are_evidence_ready(self):
        manifest = self._manifest()
        manifest["dry_run"] = False

        analysis = self._analyze(manifest)

        self.assertTrue(analysis["evidence_ready"])

    def _manifest(self):
        return json.loads(EXAMPLE.read_text(encoding="utf-8"))

    def _analyze(self, manifest):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            return analyze_editing_sessions(path)


if __name__ == "__main__":
    unittest.main()

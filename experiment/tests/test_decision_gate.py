import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sinhalasub import audit_decision  # noqa: E402


class DecisionGateTests(unittest.TestCase):
    example = ROOT / "examples" / "decision-manifest.json"

    def test_passing_synthetic_metrics_cannot_authorize_go(self) -> None:
        audit = audit_decision(self.example)

        self.assertTrue(audit["valid"], audit["errors"])
        self.assertFalse(audit["evidence_ready"])
        self.assertEqual("not-authorized", audit["outcome"])
        self.assertTrue(all(result["passed"] for result in audit["thresholds"].values()))
        self.assertTrue(any("Synthetic" in blocker for blocker in audit["blockers"]))
        self.assertNotIn(str(ROOT.resolve()), json.dumps(audit))

    def test_rejects_changed_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = json.loads(self.example.read_text(encoding="utf-8"))
            manifest["evidence"] = str((ROOT / "examples" / "decision-evidence.json").resolve())
            manifest["evidence_sha256"] = "stale"
            path = root / "decision.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")

            audit = audit_decision(path)

            self.assertFalse(audit["valid"])
            self.assertTrue(any("evidence hash" in error for error in audit["errors"]))

    def test_real_evidence_maps_to_each_decision_outcome(self) -> None:
        cases = (
            ({}, "go"),
            ({"cloud_upload_acceptable": False}, "local-pivot"),
            ({"editing_time_reduction": 0.1, "viewer_preference_rate": 0.4}, "narrow"),
            ({"protected_entity_rate": 0.1, "critical_error_reduction": 0.1, "editing_time_reduction": 0.1}, "stop"),
        )
        for changes, expected in cases:
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as directory:
                path = self._real_manifest(Path(directory), changes)
                run_audit = {"valid": True, "ready": True, "manifest_sha256": "ready-run"}
                with patch("sinhalasub.decision_gate.audit_run_capture", return_value=run_audit):
                    audit = audit_decision(path)

                self.assertTrue(audit["evidence_ready"], audit["blockers"])
                self.assertEqual(expected, audit["outcome"])

    def test_rejects_rate_above_one(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self._real_manifest(Path(directory), {"viewer_preference_rate": 1.1})
            run_audit = {"valid": True, "ready": True, "manifest_sha256": "ready-run"}
            with patch("sinhalasub.decision_gate.audit_run_capture", return_value=run_audit):
                audit = audit_decision(path)

            self.assertFalse(audit["valid"])
            self.assertTrue(any("cannot exceed" in error for error in audit["errors"]))

    @staticmethod
    def _real_manifest(root: Path, changes):
        evidence = json.loads((ROOT / "examples" / "decision-evidence.json").read_text(encoding="utf-8"))
        evidence["synthetic"] = False
        evidence["run_capture"] = str((ROOT / "examples" / "run-capture-manifest.json").resolve())
        evidence["run_capture_sha256"] = "ready-run"
        evidence["metrics"].update(changes)
        evidence_path = root / "evidence.json"
        evidence_bytes = (json.dumps(evidence, sort_keys=True) + "\n").encode("utf-8")
        evidence_path.write_bytes(evidence_bytes)
        manifest = {
            "schema_version": "sinhalasub.decision-manifest.v1",
            "decision_id": "real-decision",
            "dry_run": False,
            "evidence": "evidence.json",
            "evidence_sha256": hashlib.sha256(evidence_bytes).hexdigest(),
        }
        path = root / "decision.json"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        return path


if __name__ == "__main__":
    unittest.main()

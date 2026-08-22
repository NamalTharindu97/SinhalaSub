import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sinhalasub import audit_run_capture  # noqa: E402


class RunCaptureTests(unittest.TestCase):
    example = ROOT / "examples" / "run-capture-manifest.json"

    def test_synthetic_run_is_complete_but_not_ready(self) -> None:
        audit = audit_run_capture(self.example)

        self.assertTrue(audit["valid"], audit["errors"])
        self.assertFalse(audit["ready"])
        self.assertEqual({"assets": 1, "systems": 3, "runs": 3}, audit["counts"])
        self.assertEqual(540, audit["totals"]["duration_ms"])
        self.assertEqual(75, audit["totals"]["usage_by_unit"]["synthetic-characters"]["input_units"])
        self.assertEqual(88, audit["totals"]["usage_by_unit"]["synthetic-tokens"]["input_units"])
        self.assertTrue(all(run["output_sha256"] for run in audit["runs"]))
        self.assertNotIn(str(ROOT.resolve()), json.dumps(audit))

    def test_rejects_missing_system_run(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self._portable_manifest()
            manifest["runs"].pop()
            path = root / "runs.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")

            audit = audit_run_capture(path)

            self.assertFalse(audit["valid"])
            self.assertTrue(any("Missing asset/system" in error for error in audit["errors"]))

    def test_rejects_output_with_changed_timing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self._portable_manifest()
            changed = root / "changed.srt"
            changed.write_text(
                "1\n00:00:01,100 --> 00:00:02,000\nChanged.\n\n"
                "2\n00:00:03,000 --> 00:00:04,000\nChanged.\n\n"
                "3\n00:00:20,000 --> 00:00:21,000\nChanged.\n",
                encoding="utf-8",
            )
            manifest["runs"][0]["output"] = str(changed)
            path = root / "runs.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")

            audit = audit_run_capture(path)

            self.assertFalse(audit["valid"])
            self.assertTrue(any("does not preserve" in error for error in audit["errors"]))

    def test_rejects_negative_metering(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self._portable_manifest()
            manifest["runs"][0]["duration_ms"] = -1
            manifest["runs"][0]["usage"]["input_units"] = -1
            manifest["runs"][0]["cost_usd"] = -0.1
            path = root / "runs.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")

            audit = audit_run_capture(path)

            self.assertFalse(audit["valid"])
            self.assertTrue(any("duration_ms" in error for error in audit["errors"]))
            self.assertTrue(any("input units" in error for error in audit["errors"]))
            self.assertTrue(any("cost_usd" in error for error in audit["errors"]))

    def test_rejects_timestamp_without_timezone(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self._portable_manifest()
            manifest["runs"][0]["generated_at"] = "2026-08-22T10:00:00"
            path = root / "runs.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")

            audit = audit_run_capture(path)

            self.assertFalse(audit["valid"])
            self.assertTrue(any("with timezone" in error for error in audit["errors"]))

    def _portable_manifest(self):
        manifest = json.loads(self.example.read_text(encoding="utf-8"))
        manifest["system_freeze"] = str((ROOT / "examples" / "system-freeze-manifest.json").resolve())
        for run in manifest["runs"]:
            run["output"] = str((ROOT / "examples" / run["output"]).resolve())
        return manifest


if __name__ == "__main__":
    unittest.main()

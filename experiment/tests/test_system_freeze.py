import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sinhalasub.system_freeze import audit_system_freeze  # noqa: E402


class SystemFreezeTests(unittest.TestCase):
    example = ROOT / "examples" / "system-freeze-manifest.json"

    def test_synthetic_freeze_is_valid_but_not_ready(self) -> None:
        audit = audit_system_freeze(self.example)

        self.assertTrue(audit["valid"], audit["errors"])
        self.assertFalse(audit["ready"])
        self.assertEqual(3, len(audit["systems"]))
        self.assertTrue(all(system["instruction_sha256"] for system in audit["systems"]))
        self.assertTrue(any("dry-run" in failure for failure in audit["readiness_failures"]))
        self.assertNotIn(str(ROOT.resolve()), json.dumps(audit))

    def test_rejects_missing_role_and_enabled_training(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = json.loads(self.example.read_text(encoding="utf-8"))
            manifest["corpus_manifest"] = str((ROOT / "examples" / "corpus-manifest.json").resolve())
            for system in manifest["systems"]:
                source = ROOT / "examples" / system["instruction"]["path"]
                target = root / source.name
                target.write_bytes(source.read_bytes())
                system["instruction"]["path"] = target.name
            manifest["systems"][2]["role"] = "isolated-llm"
            manifest["systems"][0]["data_policy"]["training_disabled"] = False
            path = root / "freeze.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")

            audit = audit_system_freeze(path)

            self.assertFalse(audit["valid"])
            self.assertTrue(any("roles" in error for error in audit["errors"]))
            self.assertTrue(any("training disabled" in error for error in audit["errors"]))

    def test_instruction_change_changes_audited_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = copy.deepcopy(json.loads(self.example.read_text(encoding="utf-8")))
            manifest["corpus_manifest"] = str((ROOT / "examples" / "corpus-manifest.json").resolve())
            for system in manifest["systems"]:
                source = ROOT / "examples" / system["instruction"]["path"]
                target = root / source.name
                target.write_bytes(source.read_bytes())
                system["instruction"]["path"] = target.name
            path = root / "freeze.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            before = audit_system_freeze(path)["systems"][0]["instruction_sha256"]
            (root / "generic-mt.txt").write_text("changed\n", encoding="utf-8")

            after = audit_system_freeze(path)["systems"][0]["instruction_sha256"]
            audit = audit_system_freeze(path)

            self.assertNotEqual(before, after)
            self.assertFalse(audit["valid"])
            self.assertTrue(any("instruction hash" in error for error in audit["errors"]))

    def test_real_freeze_is_ready_only_with_ready_corpus_and_approved_policies(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = json.loads(self.example.read_text(encoding="utf-8"))
            manifest["dry_run"] = False
            manifest["corpus_manifest"] = str((ROOT / "examples" / "corpus-manifest.json").resolve())
            manifest["corpus_manifest_sha256"] = "ready-corpus-hash"
            for system in manifest["systems"]:
                instruction = ROOT / "examples" / system["instruction"]["path"]
                system["instruction"]["path"] = str(instruction.resolve())
                system["data_policy"]["status"] = "approved"
            path = root / "freeze.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            corpus_audit = {"valid": True, "ready": True, "manifest_sha256": "ready-corpus-hash"}

            with patch("sinhalasub.system_freeze.audit_corpus_manifest", return_value=corpus_audit):
                audit = audit_system_freeze(path)

            self.assertTrue(audit["valid"], audit["errors"])
            self.assertTrue(audit["ready"], audit["readiness_failures"])


if __name__ == "__main__":
    unittest.main()

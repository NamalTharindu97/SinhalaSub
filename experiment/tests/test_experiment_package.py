from dataclasses import replace
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sinhalasub import (  # noqa: E402
    PACKAGE_SCHEMA,
    SubtitleFormat,
    SystemOutput,
    build_blinded_package,
    parse_subtitle,
    write_blinded_package,
)
from sinhalasub.experiment_cli import build_from_manifest  # noqa: E402


SOURCE = (
    "1\n00:00:01,000 --> 00:00:02,000\nOne.\n\n"
    "2\n00:00:03,000 --> 00:00:04,000\nTwo.\n\n"
    "3\n00:00:20,000 --> 00:00:21,000\nThree.\n"
)


class ExperimentPackageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = parse_subtitle(SOURCE, SubtitleFormat.SRT)
        self.systems = tuple(
            SystemOutput(
                id=f"system-{letter}",
                document=replace(
                    self.source,
                    cues=tuple(replace(cue, text=f"{letter}:{cue.text}") for cue in self.source.cues),
                ),
                metadata={"model": f"secret-{letter}"},
            )
            for letter in ("a", "b", "c")
        )

    def build(self, seed: int = 42):
        return build_blinded_package(
            experiment_id="dry-run",
            seed=seed,
            source=self.source,
            systems=self.systems,
            provenance="Synthetic test dialogue.",
            rights_basis="Repository-authored fixture.",
        )

    def test_package_is_deterministic_and_system_details_remain_in_key(self) -> None:
        first_package, first_key = self.build()
        second_package, second_key = self.build()

        self.assertEqual(first_package, second_package)
        self.assertEqual(first_key, second_key)
        serialized_package = json.dumps(first_package)
        self.assertEqual(PACKAGE_SCHEMA, first_package["schema_version"])
        self.assertNotIn("system-a", serialized_package)
        self.assertNotIn("secret-a", serialized_package)
        self.assertNotIn('"seed"', serialized_package)
        self.assertEqual({"system-a", "system-b", "system-c"}, {item["id"] for item in first_key["systems"]})
        for block in first_package["blocks"]:
            self.assertEqual(["candidate-1", "candidate-2", "candidate-3"], [item["label"] for item in block["candidates"]])

    def test_package_hash_and_zip_bytes_are_reproducible(self) -> None:
        package, key = self.build()
        package_bytes = (json.dumps(package, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")

        self.assertEqual(hashlib.sha256(package_bytes).hexdigest(), key["package_sha256"])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first_zip = root / "first.zip"
            second_zip = root / "second.zip"
            write_blinded_package(package, key, first_zip, root / "first-key.json")
            write_blinded_package(package, key, second_zip, root / "second-key.json")

            self.assertEqual(first_zip.read_bytes(), second_zip.read_bytes())
            with zipfile.ZipFile(first_zip) as archive:
                self.assertEqual(["package.json"], archive.namelist())
                self.assertEqual(package, json.loads(archive.read("package.json")))

    def test_blinding_key_records_the_selected_seed(self) -> None:
        _, first_key = self.build(seed=1)
        _, second_key = self.build(seed=2)

        self.assertEqual(1, first_key["seed"])
        self.assertEqual(2, second_key["seed"])
        self.assertNotEqual(first_key, second_key)

    def test_rejects_output_with_changed_timing(self) -> None:
        invalid_document = replace(
            self.systems[0].document,
            cues=(replace(self.systems[0].document.cues[0], start_ms=1100),) + self.systems[0].document.cues[1:],
        )
        invalid_systems = (replace(self.systems[0], document=invalid_document),) + self.systems[1:]

        with self.assertRaisesRegex(ValueError, "does not preserve"):
            build_blinded_package("dry-run", 1, self.source, invalid_systems, "Synthetic", "Permitted")

    def test_requires_exactly_three_systems(self) -> None:
        with self.assertRaisesRegex(ValueError, "exactly three"):
            build_blinded_package("dry-run", 1, self.source, self.systems[:2], "Synthetic", "Permitted")


class ExperimentCliTests(unittest.TestCase):
    def test_example_manifest_builds_separate_package_and_key(self) -> None:
        manifest = ROOT / "examples" / "blinded-manifest.json"
        with tempfile.TemporaryDirectory() as directory:
            package_path = Path(directory) / "evaluators.zip"
            key_path = Path(directory) / "confidential-key.json"

            build_from_manifest(manifest, package_path, key_path, allow_not_ready_freeze=True)

            self.assertTrue(package_path.is_file())
            self.assertTrue(key_path.is_file())
            with zipfile.ZipFile(package_path) as archive:
                package = json.loads(archive.read("package.json"))
            key = json.loads(key_path.read_text(encoding="utf-8"))
            self.assertEqual(package["experiment_id"], key["experiment_id"])
            self.assertNotIn("systems", package)
            self.assertEqual("synthetic-system-freeze-001", key["system_freeze"]["id"])
            self.assertTrue(key["system_freeze"]["dry_run"])

    def test_rejects_synthetic_freeze_without_explicit_override(self) -> None:
        manifest = ROOT / "examples" / "blinded-manifest.json"
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "not ready"):
                build_from_manifest(
                    manifest,
                    Path(directory) / "evaluators.zip",
                    Path(directory) / "key.json",
                )

    def test_rejects_seed_that_differs_from_freeze(self) -> None:
        source_manifest = ROOT / "examples" / "blinded-manifest.json"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = json.loads(source_manifest.read_text(encoding="utf-8"))
            manifest["seed"] += 1
            manifest["system_freeze"] = str((ROOT / "examples" / manifest["system_freeze"]).resolve())
            manifest["source"] = str((ROOT / "examples" / manifest["source"]).resolve())
            path = root / "manifest.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "seed"):
                build_from_manifest(
                    path,
                    root / "evaluators.zip",
                    root / "key.json",
                    allow_not_ready_freeze=True,
                )


if __name__ == "__main__":
    unittest.main()

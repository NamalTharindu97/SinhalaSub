"""Build a deterministic blinded experiment package from a JSON manifest."""

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Dict

from .experiment_package import SystemOutput, build_blinded_package, write_blinded_package
from .subtitles import SubtitleError, SubtitleFormat, parse_subtitle


def _format_for_path(path: Path) -> SubtitleFormat:
    suffix = path.suffix.lower()
    if suffix == ".srt":
        return SubtitleFormat.SRT
    if suffix in {".vtt", ".webvtt"}:
        return SubtitleFormat.WEBVTT
    raise ValueError(f"Unsupported subtitle extension: {suffix or '(none)'}")


def _load_document(path: Path):
    return parse_subtitle(path.read_text(encoding="utf-8-sig"), _format_for_path(path))


def build_from_manifest(manifest_path: Path, package_path: Path, key_path: Path) -> None:
    manifest: Dict[str, Any] = json.loads(manifest_path.read_text(encoding="utf-8"))
    root = manifest_path.parent
    source_path = (root / manifest["source"]).resolve()
    systems = tuple(
        SystemOutput(
            id=str(item["id"]),
            document=_load_document((root / item["output"]).resolve()),
            metadata=dict(item.get("metadata", {})),
        )
        for item in manifest["systems"]
    )
    package, key = build_blinded_package(
        experiment_id=str(manifest["experiment_id"]),
        seed=int(manifest["seed"]),
        source=_load_document(source_path),
        systems=systems,
        provenance=str(manifest["provenance"]),
        rights_basis=str(manifest["rights_basis"]),
    )
    write_blinded_package(package, key, package_path, key_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a blinded three-system evaluation package.")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("package", type=Path, help="Output .zip path for evaluators")
    parser.add_argument("--key", required=True, type=Path, help="Separate confidential JSON key path")
    args = parser.parse_args()
    try:
        build_from_manifest(args.manifest, args.package, args.key)
    except (OSError, KeyError, TypeError, ValueError, UnicodeError, json.JSONDecodeError, SubtitleError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"Wrote blinded package to {args.package}")
    print(f"Wrote confidential key to {args.key}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

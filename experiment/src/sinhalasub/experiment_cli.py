"""Build a deterministic blinded experiment package from a JSON manifest."""

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Dict

from .experiment_package import SystemOutput, build_blinded_package, write_blinded_package
from .corpus import audit_corpus_manifest
from .run_capture import audit_run_capture
from .subtitles import SubtitleError, SubtitleFormat, parse_subtitle, serialize_subtitle
from .system_freeze import audit_system_freeze


def _format_for_path(path: Path) -> SubtitleFormat:
    suffix = path.suffix.lower()
    if suffix == ".srt":
        return SubtitleFormat.SRT
    if suffix in {".vtt", ".webvtt"}:
        return SubtitleFormat.WEBVTT
    raise ValueError(f"Unsupported subtitle extension: {suffix or '(none)'}")


def _load_document(path: Path):
    return parse_subtitle(path.read_text(encoding="utf-8-sig"), _format_for_path(path))


def build_from_manifest(
    manifest_path: Path,
    package_path: Path,
    key_path: Path,
    allow_not_ready_freeze: bool = False,
) -> None:
    manifest: Dict[str, Any] = json.loads(manifest_path.read_text(encoding="utf-8"))
    root = manifest_path.parent
    source_path = (root / manifest["source"]).resolve()
    freeze_path = (root / manifest["system_freeze"]).resolve()
    freeze_audit = audit_system_freeze(freeze_path)
    if not freeze_audit["valid"]:
        raise ValueError("System freeze is invalid: " + " ".join(freeze_audit["errors"]))
    if not freeze_audit["ready"] and (not allow_not_ready_freeze or not freeze_audit["dry_run"]):
        raise ValueError("System freeze is not ready for a real experiment.")
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    if int(manifest["seed"]) != freeze["seed"]:
        raise ValueError("Package seed does not match the frozen randomisation seed.")
    frozen_by_id = {system["id"]: system for system in freeze["systems"]}
    manifest_ids = {str(item["id"]) for item in manifest["systems"]}
    if manifest_ids != set(frozen_by_id):
        raise ValueError("Package systems do not match the frozen system IDs.")

    corpus_path = (freeze_path.parent / freeze["corpus_manifest"]).resolve()
    corpus_audit = audit_corpus_manifest(corpus_path)
    source_document = _load_document(source_path)
    source_hash = hashlib.sha256(serialize_subtitle(source_document).encode("utf-8")).hexdigest()
    if source_hash not in {asset["source_sha256"] for asset in corpus_audit["assets"]}:
        raise ValueError("Package source does not belong to the frozen corpus.")

    run_path = (root / manifest["run_capture"]).resolve()
    run_audit = audit_run_capture(run_path)
    if not run_audit["valid"]:
        raise ValueError("System-run capture is invalid: " + " ".join(run_audit["errors"]))
    if not run_audit["ready"] and (not allow_not_ready_freeze or not freeze_audit["dry_run"]):
        raise ValueError("System-run capture is not ready for a real experiment.")
    if run_audit["system_freeze"]["sha256"] != freeze_audit["manifest_sha256"]:
        raise ValueError("System-run capture does not match the package system freeze.")
    captured_by_system = {
        run["system_id"]: run for run in run_audit["runs"] if run["source_sha256"] == source_hash
    }
    if set(captured_by_system) != manifest_ids:
        raise ValueError("System-run capture does not contain every package system for this source.")

    system_outputs = []
    for item in manifest["systems"]:
        system_id = str(item["id"])
        document = _load_document((root / item["output"]).resolve())
        output_hash = hashlib.sha256(serialize_subtitle(document).encode("utf-8")).hexdigest()
        if output_hash != captured_by_system[system_id]["output_sha256"]:
            raise ValueError(f"System {system_id!r} output does not match the captured run output.")
        system_outputs.append(
            SystemOutput(
                id=system_id,
                document=document,
                metadata={
                    **dict(item.get("metadata", {})),
                    "role": frozen_by_id[system_id]["role"],
                    "provider": frozen_by_id[system_id]["provider"],
                    "model": frozen_by_id[system_id]["model"],
                    "model_version": frozen_by_id[system_id]["model_version"],
                    "adapter_version": frozen_by_id[system_id]["adapter_version"],
                    "instruction_sha256": frozen_by_id[system_id]["instruction"]["sha256"],
                    "duration_ms": captured_by_system[system_id]["duration_ms"],
                    "input_units": captured_by_system[system_id]["input_units"],
                    "output_units": captured_by_system[system_id]["output_units"],
                    "usage_unit": captured_by_system[system_id]["usage_unit"],
                    "cost_usd": captured_by_system[system_id]["cost_usd"],
                },
            )
        )
    systems = tuple(system_outputs)
    package, key = build_blinded_package(
        experiment_id=str(manifest["experiment_id"]),
        seed=int(manifest["seed"]),
        source=source_document,
        systems=systems,
        provenance=str(manifest["provenance"]),
        rights_basis=str(manifest["rights_basis"]),
        system_freeze={
            "id": freeze_audit["freeze_id"],
            "manifest_sha256": freeze_audit["manifest_sha256"],
            "dry_run": freeze_audit["dry_run"],
        },
        system_run={
            "id": run_audit["run_id"],
            "manifest_sha256": run_audit["manifest_sha256"],
            "ready": run_audit["ready"],
        },
    )
    write_blinded_package(package, key, package_path, key_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a blinded three-system evaluation package.")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("package", type=Path, help="Output .zip path for evaluators")
    parser.add_argument("--key", required=True, type=Path, help="Separate confidential JSON key path")
    parser.add_argument(
        "--allow-not-ready-freeze",
        action="store_true",
        help="Permit only an explicitly marked synthetic dry-run freeze for protocol testing.",
    )
    args = parser.parse_args()
    try:
        build_from_manifest(args.manifest, args.package, args.key, args.allow_not_ready_freeze)
    except (OSError, KeyError, TypeError, ValueError, UnicodeError, json.JSONDecodeError, SubtitleError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"Wrote blinded package to {args.package}")
    print(f"Wrote confidential key to {args.key}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

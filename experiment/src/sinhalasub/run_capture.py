"""Audit complete output and metering capture for frozen experiment systems."""

import hashlib
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Mapping, Set, Tuple

from .subtitles import SubtitleDocument, SubtitleFormat, parse_subtitle, serialize_subtitle
from .system_freeze import audit_system_freeze


RUN_SCHEMA = "sinhalasub.system-run-capture.v1"
RUN_AUDIT_SCHEMA = "sinhalasub.system-run-audit.v1"


def audit_run_capture(manifest_path: Path) -> Dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    root = manifest_path.parent
    errors: List[str] = []
    readiness_failures: List[str] = []
    if manifest.get("schema_version") != RUN_SCHEMA:
        errors.append("Unsupported or missing system-run capture schema.")
    run_id = str(manifest.get("run_id", "")).strip()
    if not run_id:
        errors.append("Run ID is required.")

    freeze_value = manifest.get("system_freeze")
    freeze_path = _resolve_path(root, freeze_value)
    freeze = None
    freeze_audit = None
    if freeze_path is None or not freeze_path.is_file():
        errors.append("System-freeze manifest does not exist.")
    else:
        freeze_audit = audit_system_freeze(freeze_path)
        freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
        if not freeze_audit["valid"]:
            errors.append("System-freeze manifest is invalid.")
        if manifest.get("system_freeze_sha256") != freeze_audit["manifest_sha256"]:
            errors.append("System-freeze hash does not match the captured freeze.")
        if not freeze_audit["ready"]:
            readiness_failures.append("System freeze is not ready for a real experiment run.")

    assets: Dict[str, Tuple[SubtitleDocument, str]] = {}
    system_ids: Set[str] = set()
    if freeze is not None and freeze_path is not None:
        system_ids = {str(system.get("id", "")) for system in freeze.get("systems", [])}
        corpus_path = _resolve_path(freeze_path.parent, freeze.get("corpus_manifest"))
        if corpus_path is not None and corpus_path.is_file():
            corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
            for asset in corpus.get("assets", []):
                asset_id = str(asset.get("id", ""))
                source_path = _resolve_path(corpus_path.parent, asset.get("source"))
                if source_path is not None and source_path.is_file():
                    source = _load_document(source_path)
                    assets[asset_id] = (source, _document_hash(source))

    runs = manifest.get("runs")
    if not isinstance(runs, list):
        errors.append("Runs must be a list.")
        runs = []
    reports = []
    seen: Set[Tuple[str, str]] = set()
    total_duration = 0
    usage_by_unit: Dict[str, Dict[str, int]] = {}
    total_cost = 0.0
    for position, run in enumerate(runs, start=1):
        report = _audit_run(root, run, position, assets, system_ids, errors)
        reports.append(report)
        key = (report["asset_id"], report["system_id"])
        if key in seen:
            errors.append(f"Duplicate run for asset/system pair {key!r}.")
        seen.add(key)
        total_duration += report["duration_ms"]
        unit_totals = usage_by_unit.setdefault(report["usage_unit"], {"input_units": 0, "output_units": 0})
        unit_totals["input_units"] += report["input_units"]
        unit_totals["output_units"] += report["output_units"]
        total_cost += report["cost_usd"]

    expected = {(asset_id, system_id) for asset_id in assets for system_id in system_ids}
    if seen != expected:
        missing = sorted(expected - seen)
        unexpected = sorted(seen - expected)
        if missing:
            errors.append(f"Missing asset/system runs: {missing}.")
        if unexpected:
            errors.append(f"Unexpected asset/system runs: {unexpected}.")

    return {
        "schema_version": RUN_AUDIT_SCHEMA,
        "run_id": run_id,
        "manifest_sha256": hashlib.sha256(_canonical_json(manifest)).hexdigest(),
        "system_freeze": {
            "path": str(freeze_value or ""),
            "sha256": freeze_audit.get("manifest_sha256") if freeze_audit else None,
            "ready": freeze_audit.get("ready", False) if freeze_audit else False,
        },
        "valid": not errors,
        "ready": not errors and not readiness_failures,
        "counts": {"assets": len(assets), "systems": len(system_ids), "runs": len(runs)},
        "totals": {
            "duration_ms": total_duration,
            "cost_usd": round(total_cost, 8),
            "usage_by_unit": usage_by_unit,
        },
        "runs": reports,
        "errors": errors,
        "readiness_failures": readiness_failures,
    }


def _audit_run(
    root: Path,
    run: Mapping[str, Any],
    position: int,
    assets: Mapping[str, Tuple[SubtitleDocument, str]],
    system_ids: Set[str],
    errors: List[str],
) -> Dict[str, Any]:
    asset_id = str(run.get("asset_id", "")).strip()
    system_id = str(run.get("system_id", "")).strip()
    prefix = f"Run {position} ({asset_id!r}, {system_id!r})"
    if asset_id not in assets:
        errors.append(f"{prefix} references an unknown corpus asset.")
    if system_id not in system_ids:
        errors.append(f"{prefix} references an unknown frozen system.")
    generated_at = str(run.get("generated_at", "")).strip()
    try:
        parsed_generated_at = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
        if parsed_generated_at.tzinfo is None:
            raise ValueError
    except ValueError:
        errors.append(f"{prefix} requires an ISO 8601 generation timestamp with timezone.")
    duration_ms = _nonnegative_integer(run.get("duration_ms"), prefix, "duration_ms", errors)
    usage = run.get("usage", {})
    input_units = _nonnegative_integer(usage.get("input_units") if isinstance(usage, Mapping) else None, prefix, "input units", errors)
    output_units = _nonnegative_integer(usage.get("output_units") if isinstance(usage, Mapping) else None, prefix, "output units", errors)
    unit = str(usage.get("unit", "")).strip() if isinstance(usage, Mapping) else ""
    if not unit:
        errors.append(f"{prefix} requires a usage unit.")
    cost_value = run.get("cost_usd")
    cost_usd = float(cost_value) if isinstance(cost_value, (int, float)) and not isinstance(cost_value, bool) else 0.0
    if not isinstance(cost_value, (int, float)) or isinstance(cost_value, bool) or not math.isfinite(cost_usd) or cost_usd < 0:
        errors.append(f"{prefix} cost_usd must be a non-negative number.")
        cost_usd = 0.0

    output_value = run.get("output")
    output_path = _resolve_path(root, output_value)
    output_hash = None
    if output_path is None or not output_path.is_file():
        errors.append(f"{prefix} output file does not exist.")
    else:
        try:
            output = _load_document(output_path)
            output_hash = _document_hash(output)
            if asset_id in assets and _structure(output) != _structure(assets[asset_id][0]):
                errors.append(f"{prefix} output does not preserve source cue IDs and timestamps.")
        except (OSError, UnicodeError, ValueError) as error:
            errors.append(f"{prefix} output is invalid: {error}")
    return {
        "asset_id": asset_id,
        "system_id": system_id,
        "source_sha256": assets[asset_id][1] if asset_id in assets else None,
        "output": str(output_value or ""),
        "output_sha256": output_hash,
        "generated_at": generated_at,
        "duration_ms": duration_ms,
        "input_units": input_units,
        "output_units": output_units,
        "usage_unit": unit,
        "cost_usd": cost_usd,
    }


def _nonnegative_integer(value: Any, prefix: str, field: str, errors: List[str]) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        errors.append(f"{prefix} {field} must be a non-negative integer.")
        return 0
    return value


def _load_document(path: Path) -> SubtitleDocument:
    suffix = path.suffix.lower()
    if suffix == ".srt":
        subtitle_format = SubtitleFormat.SRT
    elif suffix in {".vtt", ".webvtt"}:
        subtitle_format = SubtitleFormat.WEBVTT
    else:
        raise ValueError(f"Unsupported subtitle extension: {suffix or '(none)'}")
    return parse_subtitle(path.read_text(encoding="utf-8-sig"), subtitle_format)


def _structure(document: SubtitleDocument) -> Any:
    return tuple((cue.id, cue.index, cue.start_ms, cue.end_ms) for cue in document.cues)


def _document_hash(document: SubtitleDocument) -> str:
    return hashlib.sha256(serialize_subtitle(document).encode("utf-8")).hexdigest()


def _resolve_path(root: Path, value: Any) -> Any:
    if not isinstance(value, str) or not value.strip():
        return None
    return (root / value).resolve()


def _canonical_json(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")

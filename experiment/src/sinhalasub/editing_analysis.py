"""Paired analysis of baseline and contextual subtitle editing sessions."""

import hashlib
import json
import random
from datetime import datetime
from pathlib import Path
from statistics import median
from typing import Any, Dict, List, Mapping, Sequence, Tuple

from .experiment_report import REPORT_SCHEMA


EDITING_MANIFEST_SCHEMA = "sinhalasub.editing-sessions.v1"
EDITING_ANALYSIS_SCHEMA = "sinhalasub.editing-analysis.v1"
EDITING_TIME_THRESHOLD = 0.25


def analyze_editing_sessions(manifest_path: Path) -> Dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors: List[str] = []
    blockers: List[str] = []
    if manifest.get("schema_version") != EDITING_MANIFEST_SCHEMA:
        errors.append("Unsupported or missing editing-session schema.")
    analysis_id = str(manifest.get("analysis_id", "")).strip()
    if not analysis_id:
        errors.append("Analysis ID is required.")
    if not isinstance(manifest.get("dry_run"), bool):
        errors.append("Dry-run state must be a boolean.")
    dry_run = manifest.get("dry_run") is True
    baseline_id = str(manifest.get("baseline_system_id", "")).strip()
    contextual_id = str(manifest.get("contextual_system_id", "")).strip()
    if not baseline_id or not contextual_id or baseline_id == contextual_id:
        errors.append("Distinct baseline and contextual system IDs are required.")
    seed = manifest.get("seed")
    if not isinstance(seed, int) or isinstance(seed, bool):
        errors.append("A fixed integer bootstrap seed is required.")
        seed = 0

    sessions = manifest.get("sessions")
    if not isinstance(sessions, list):
        errors.append("Sessions must be a list.")
        sessions = []
    seen_ids = set()
    seen_reports = set()
    paired: Dict[Tuple[str, str], Dict[str, Mapping[str, Any]]] = {}
    reviewers = set()
    for position, session in enumerate(sessions, start=1):
        if not isinstance(session, Mapping):
            errors.append(f"Session {position} must be an object.")
            continue
        session_id = str(session.get("session_id", "")).strip()
        reviewer_id = str(session.get("reviewer_id", "")).strip()
        asset_id = str(session.get("asset_id", "")).strip()
        system_id = str(session.get("system_id", "")).strip()
        prefix = f"Session {session_id or position!r}"
        if not session_id or session_id in seen_ids:
            errors.append(f"{prefix} requires a unique session ID.")
        seen_ids.add(session_id)
        if not reviewer_id or not asset_id:
            errors.append(f"{prefix} requires reviewer and asset IDs.")
        if system_id not in {baseline_id, contextual_id}:
            errors.append(f"{prefix} references an unknown comparison system.")
        report = session.get("report")
        if not isinstance(report, Mapping) or report.get("schema_version") != REPORT_SCHEMA:
            errors.append(f"{prefix} requires an embedded {REPORT_SCHEMA} report.")
            report = {}
        report_hash = hashlib.sha256(_canonical_json(report)).hexdigest()
        if report_hash in seen_reports:
            errors.append(f"{prefix} reuses an experiment report.")
        seen_reports.add(report_hash)
        source = report.get("source", {}) if isinstance(report.get("source"), Mapping) else {}
        source_hash = str(source.get("sha256", ""))
        if len(source_hash) != 64 or any(character not in "0123456789abcdef" for character in source_hash):
            errors.append(f"{prefix} requires a lowercase SHA-256 source hash.")
        _timestamp(report.get("generated_at"), prefix, errors)
        review = report.get("review", {}) if isinstance(report.get("review"), Mapping) else {}
        active = _nonnegative_int(review.get("active_edit_ms"), prefix, "active_edit_ms", errors)
        elapsed = _nonnegative_int(review.get("elapsed_ms"), prefix, "elapsed_ms", errors)
        if active <= 0 or active > elapsed:
            errors.append(f"{prefix} active edit time must be positive and not exceed elapsed time.")
        for field in ("changed_cue_count", "keyboard_actions", "edit_events"):
            _nonnegative_int(review.get(field), prefix, field, errors)
        record = {"active_edit_ms": active, "source_sha256": source_hash}
        pair = paired.setdefault((reviewer_id, asset_id), {})
        if system_id in pair:
            errors.append(f"{prefix} duplicates a reviewer/asset/system assignment.")
        pair[system_id] = record
        if reviewer_id:
            reviewers.add(reviewer_id)

    expected_systems = {baseline_id, contextual_id}
    incomplete = sorted(key for key, values in paired.items() if set(values) != expected_systems)
    if incomplete:
        errors.append(f"Incomplete baseline/contextual pairs: {incomplete}.")
    for key, values in paired.items():
        if set(values) == expected_systems and len({values[system]["source_sha256"] for system in expected_systems}) != 1:
            errors.append(f"Pair {key!r} does not use the same source under both systems.")
    if len(reviewers) < 3:
        blockers.append("At least three experienced translators are required.")
    if dry_run:
        blockers.append("Synthetic editing sessions cannot authorize the experiment.")

    complete_pairs = [values for values in paired.values() if set(values) == expected_systems]
    baseline_times = [int(values[baseline_id]["active_edit_ms"]) for values in complete_pairs]
    contextual_times = [int(values[contextual_id]["active_edit_ms"]) for values in complete_pairs]
    reductions = [
        (baseline - contextual) / baseline
        for baseline, contextual in zip(baseline_times, contextual_times)
        if baseline > 0
    ]
    reduction_median = median(reductions) if reductions else 0.0
    confidence = _bootstrap_median_ci(reductions, seed) if reductions else (0.0, 0.0)
    return {
        "schema_version": EDITING_ANALYSIS_SCHEMA,
        "analysis_id": analysis_id,
        "manifest_sha256": hashlib.sha256(_canonical_json(manifest)).hexdigest(),
        "dry_run": dry_run,
        "valid": not errors,
        "evidence_ready": not errors and not blockers,
        "reviewer_count": len(reviewers),
        "pair_count": len(complete_pairs),
        "baseline_system_id": baseline_id,
        "contextual_system_id": contextual_id,
        "baseline_median_active_edit_ms": median(baseline_times) if baseline_times else 0,
        "contextual_median_active_edit_ms": median(contextual_times) if contextual_times else 0,
        "paired_median_reduction": round(reduction_median, 4),
        "paired_reduction_ci_95": [round(value, 4) for value in confidence],
        "threshold": EDITING_TIME_THRESHOLD,
        "threshold_passed": reduction_median >= EDITING_TIME_THRESHOLD,
        "errors": errors,
        "blockers": blockers,
    }


def _bootstrap_median_ci(values: Sequence[float], seed: int, samples: int = 10000) -> Tuple[float, float]:
    generator = random.Random(seed)
    medians = sorted(
        median([values[generator.randrange(len(values))] for _ in values])
        for _ in range(samples)
    )
    return _percentile(medians, 0.025), _percentile(medians, 0.975)


def _percentile(values: Sequence[float], probability: float) -> float:
    position = (len(values) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(values) - 1)
    fraction = position - lower
    return values[lower] * (1 - fraction) + values[upper] * fraction


def _timestamp(value: Any, prefix: str, errors: List[str]) -> None:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError
    except ValueError:
        errors.append(f"{prefix} requires an ISO 8601 generation timestamp with timezone.")


def _nonnegative_int(value: Any, prefix: str, field: str, errors: List[str]) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        errors.append(f"{prefix} {field} must be a non-negative integer.")
        return 0
    return value


def _canonical_json(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")

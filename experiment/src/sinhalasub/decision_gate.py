"""Apply frozen Phase 0 product thresholds to a versioned evidence record."""

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Mapping

from .run_capture import audit_run_capture


DECISION_MANIFEST_SCHEMA = "sinhalasub.decision-manifest.v1"
DECISION_EVIDENCE_SCHEMA = "sinhalasub.decision-evidence.v1"
DECISION_AUDIT_SCHEMA = "sinhalasub.decision-audit.v1"


def audit_decision(manifest_path: Path) -> Dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    root = manifest_path.parent
    errors: List[str] = []
    blockers: List[str] = []
    if manifest.get("schema_version") != DECISION_MANIFEST_SCHEMA:
        errors.append("Unsupported or missing decision-manifest schema.")
    decision_id = str(manifest.get("decision_id", "")).strip()
    if not decision_id:
        errors.append("Decision ID is required.")
    dry_run = manifest.get("dry_run") is True

    evidence_value = manifest.get("evidence")
    evidence_path = _resolve_path(root, evidence_value)
    evidence: Mapping[str, Any] = {}
    evidence_hash = None
    if evidence_path is None or not evidence_path.is_file():
        errors.append("Decision evidence file does not exist.")
    else:
        evidence_bytes = evidence_path.read_bytes()
        evidence_hash = hashlib.sha256(evidence_bytes).hexdigest()
        if manifest.get("evidence_sha256") != evidence_hash:
            errors.append("Decision evidence hash does not match the frozen hash.")
        evidence = json.loads(evidence_bytes.decode("utf-8"))
        if evidence.get("schema_version") != DECISION_EVIDENCE_SCHEMA:
            errors.append("Unsupported or missing decision-evidence schema.")
        if (evidence.get("synthetic") is True) != dry_run:
            errors.append("Manifest dry-run state does not match the evidence.")

    run_audit = None
    run_value = evidence.get("run_capture")
    run_path = _resolve_path(evidence_path.parent if evidence_path else root, run_value)
    if run_path is None or not run_path.is_file():
        errors.append("Evidence system-run capture does not exist.")
    else:
        run_audit = audit_run_capture(run_path)
        if not run_audit["valid"]:
            errors.append("Evidence system-run capture is invalid.")
        if evidence.get("run_capture_sha256") != run_audit["manifest_sha256"]:
            errors.append("Evidence system-run hash does not match the captured run.")
        if not run_audit["ready"]:
            blockers.append("System run is not ready.")

    translator_count = _nonnegative_int(evidence.get("translator_count"), "translator_count", errors)
    viewer_count = _nonnegative_int(evidence.get("viewer_count"), "viewer_count", errors)
    if translator_count < 3:
        blockers.append("At least three experienced translators are required.")
    if viewer_count < 30:
        blockers.append("At least 30 Sinhala-speaking viewers are required.")
    reviewers = evidence.get("independent_reviewers", [])
    if not isinstance(reviewers, list) or len({str(value).strip() for value in reviewers if str(value).strip()}) < 2:
        blockers.append("At least two independent protocol/result reviewers are required.")
    if evidence.get("protocol_approved") is not True or evidence.get("analysis_reviewed") is not True:
        blockers.append("Protocol approval and independent analysis review are required.")
    if dry_run:
        blockers.append("Synthetic dry-run evidence cannot authorize a product decision.")

    metrics = evidence.get("metrics", {})
    thresholds = _threshold_results(metrics, errors)
    all_go = all(item["passed"] for item in thresholds.values())
    quality_keys = ("cue_integrity", "protected_entities", "editing_time", "critical_errors", "hallucinations", "viewer_preference")
    quality_pass = all(thresholds[key]["passed"] for key in quality_keys)
    narrow_value = thresholds["protected_entities"]["passed"] or thresholds["critical_errors"]["passed"]
    evidence_ready = not errors and not blockers
    if not evidence_ready:
        outcome = "not-authorized"
    elif all_go and bool(metrics.get("cloud_upload_acceptable")):
        outcome = "go"
    elif quality_pass and not bool(metrics.get("cloud_upload_acceptable")):
        outcome = "local-pivot"
    elif narrow_value:
        outcome = "narrow"
    else:
        outcome = "stop"

    return {
        "schema_version": DECISION_AUDIT_SCHEMA,
        "decision_id": decision_id,
        "manifest_sha256": hashlib.sha256(_canonical_json(manifest)).hexdigest(),
        "evidence": {"path": str(evidence_value or ""), "sha256": evidence_hash},
        "dry_run": dry_run,
        "valid": not errors,
        "evidence_ready": evidence_ready,
        "outcome": outcome,
        "thresholds": thresholds,
        "errors": errors,
        "blockers": blockers,
    }


def _threshold_results(metrics: Any, errors: List[str]) -> Dict[str, Dict[str, Any]]:
    if not isinstance(metrics, Mapping):
        errors.append("Metrics must be an object.")
        metrics = {}
    integrity = _rate(metrics.get("cue_integrity_rate"), "cue_integrity_rate", errors)
    protected = _rate(metrics.get("protected_entity_rate"), "protected_entity_rate", errors)
    edit_reduction = _rate(metrics.get("editing_time_reduction"), "editing_time_reduction", errors)
    critical_reduction = _rate(metrics.get("critical_error_reduction"), "critical_error_reduction", errors)
    hallucination = _rate(metrics.get("critical_hallucination_rate"), "critical_hallucination_rate", errors)
    preference = _rate(metrics.get("viewer_preference_rate"), "viewer_preference_rate", errors)
    episode_cost = _number(metrics.get("episode_cost_usd"), "episode_cost_usd", errors)
    film_cost = _number(metrics.get("film_cost_usd"), "film_cost_usd", errors)
    if not isinstance(metrics.get("systematic_failure"), bool):
        errors.append("systematic_failure must be a boolean.")
    if not isinstance(metrics.get("cloud_upload_acceptable"), bool):
        errors.append("cloud_upload_acceptable must be a boolean.")
    systematic = metrics.get("systematic_failure") is True
    return {
        "cue_integrity": _result(integrity, 1.0, integrity == 1.0),
        "protected_entities": _result(protected, 0.95, protected >= 0.95),
        "editing_time": _result(edit_reduction, 0.25, edit_reduction >= 0.25),
        "critical_errors": _result(critical_reduction, 0.30, critical_reduction >= 0.30),
        "hallucinations": {"value": hallucination, "threshold": "<0.005 and no systematic failure", "passed": hallucination < 0.005 and not systematic},
        "viewer_preference": _result(preference, 0.65, preference >= 0.65),
        "episode_cost": {"value": episode_cost, "threshold": "<=3.0", "passed": episode_cost <= 3.0},
        "film_cost": {"value": film_cost, "threshold": "<=8.0", "passed": film_cost <= 8.0},
    }


def _result(value: float, threshold: float, passed: bool) -> Dict[str, Any]:
    return {"value": value, "threshold": threshold, "passed": passed}


def _number(value: Any, field: str, errors: List[str]) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)) or float(value) < 0:
        errors.append(f"{field} must be a finite non-negative number.")
        return 0.0
    return float(value)


def _rate(value: Any, field: str, errors: List[str]) -> float:
    number = _number(value, field, errors)
    if number > 1:
        errors.append(f"{field} cannot exceed 1.")
        return 0.0
    return number


def _nonnegative_int(value: Any, field: str, errors: List[str]) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        errors.append(f"{field} must be a non-negative integer.")
        return 0
    return value


def _resolve_path(root: Path, value: Any) -> Any:
    if not isinstance(value, str) or not value.strip():
        return None
    return (root / value).resolve()


def _canonical_json(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")

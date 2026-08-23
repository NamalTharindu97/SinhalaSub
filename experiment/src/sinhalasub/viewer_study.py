"""Build and analyze blinded subtitle-only viewer A/B studies."""

import hashlib
import json
import math
import random
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence, Tuple

from .run_capture import audit_run_capture
from .subtitles import SubtitleFormat, parse_subtitle, serialize_subtitle


VIEWER_MANIFEST_SCHEMA = "sinhalasub.viewer-study-manifest.v1"
VIEWER_PACKAGE_SCHEMA = "sinhalasub.viewer-study-package.v1"
VIEWER_KEY_SCHEMA = "sinhalasub.viewer-study-key.v1"
VIEWER_RESPONSES_SCHEMA = "sinhalasub.viewer-study-responses.v1"
VIEWER_ANALYSIS_SCHEMA = "sinhalasub.viewer-study-analysis.v1"
VIEWER_PREFERENCE_THRESHOLD = 0.65


def build_viewer_study(manifest_path: Path) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    root = manifest_path.parent
    if manifest.get("schema_version") != VIEWER_MANIFEST_SCHEMA:
        raise ValueError("Unsupported or missing viewer-study manifest schema.")
    study_id = _required_text(manifest, "study_id")
    if not isinstance(manifest.get("dry_run"), bool):
        raise ValueError("dry_run must be a boolean.")
    dry_run = manifest["dry_run"]
    seed = manifest.get("seed")
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ValueError("seed must be an integer.")
    baseline_id = _required_text(manifest, "baseline_system_id")
    contextual_id = _required_text(manifest, "contextual_system_id")
    if baseline_id == contextual_id:
        raise ValueError("Baseline and contextual system IDs must differ.")

    run_path = _resolve(root, manifest.get("run_capture"))
    if run_path is None or not run_path.is_file():
        raise ValueError("Run-capture manifest does not exist.")
    run_audit = audit_run_capture(run_path)
    if not run_audit["valid"]:
        raise ValueError("Run-capture manifest is invalid.")
    if manifest.get("run_capture_sha256") != run_audit["manifest_sha256"]:
        raise ValueError("Run-capture hash does not match the viewer study.")
    if not dry_run and not run_audit["ready"]:
        raise ValueError("A real viewer study requires a ready run capture.")
    run_manifest = json.loads(run_path.read_text(encoding="utf-8"))
    outputs = _load_outputs(run_path.parent, run_manifest, {baseline_id, contextual_id})

    assets = manifest.get("assets")
    if not isinstance(assets, list) or not assets:
        raise ValueError("At least one viewer-study asset is required.")
    generator = random.Random(seed)
    package_assets = []
    key_assets = []
    seen_assets = set()
    for asset in assets:
        if not isinstance(asset, Mapping):
            raise ValueError("Viewer-study assets must be objects.")
        asset_id = _required_text(asset, "asset_id")
        if asset_id in seen_assets:
            raise ValueError(f"Duplicate viewer-study asset {asset_id!r}.")
        seen_assets.add(asset_id)
        clip_reference = _required_text(asset, "clip_reference")
        rights_basis = _required_text(asset, "rights_basis")
        questions, answers = _questions(asset.get("questions"))
        systems = [baseline_id, contextual_id]
        generator.shuffle(systems)
        labels = ("A", "B")
        candidates = []
        mapping = {}
        for label, system_id in zip(labels, systems):
            output = outputs.get((asset_id, system_id))
            if output is None:
                raise ValueError(f"Missing captured output for {(asset_id, system_id)!r}.")
            candidates.append({"candidate_id": label, "subtitle_sha256": _sha(output), "subtitle": output})
            mapping[label] = system_id
        package_assets.append({
            "asset_id": asset_id,
            "clip_reference": clip_reference,
            "rights_basis": rights_basis,
            "candidates": candidates,
            "questions": questions,
        })
        key_assets.append({"asset_id": asset_id, "candidate_systems": mapping, "correct_options": answers})

    package = {
        "schema_version": VIEWER_PACKAGE_SCHEMA,
        "study_id": study_id,
        "run_capture_sha256": run_audit["manifest_sha256"],
        "instructions": "View each controlled clip with both subtitle candidates. Keep system identity hidden.",
        "assets": package_assets,
    }
    key = {
        "schema_version": VIEWER_KEY_SCHEMA,
        "study_id": study_id,
        "dry_run": dry_run,
        "package_sha256": viewer_package_digest(package),
        "run_capture_ready": run_audit["ready"],
        "baseline_system_id": baseline_id,
        "contextual_system_id": contextual_id,
        "assets": key_assets,
    }
    return package, key


def analyze_viewer_responses(
    package: Mapping[str, Any], key: Mapping[str, Any], responses: Mapping[str, Any]
) -> Dict[str, Any]:
    errors: List[str] = []
    blockers: List[str] = []
    package_hash = viewer_package_digest(package)
    if package.get("schema_version") != VIEWER_PACKAGE_SCHEMA:
        errors.append("Unsupported viewer package schema.")
    if key.get("schema_version") != VIEWER_KEY_SCHEMA or key.get("package_sha256") != package_hash:
        errors.append("Confidential key does not match the viewer package.")
    if responses.get("schema_version") != VIEWER_RESPONSES_SCHEMA or responses.get("package_sha256") != package_hash:
        errors.append("Viewer responses do not match the viewer package.")
    if package.get("study_id") != key.get("study_id") or package.get("study_id") != responses.get("study_id"):
        errors.append("Viewer study IDs do not match.")

    package_rows = package.get("assets")
    key_rows = key.get("assets")
    if not isinstance(package_rows, list) or not isinstance(key_rows, list):
        errors.append("Package and key assets must be lists.")
        package_rows = []
        key_rows = []
    package_assets = {str(item.get("asset_id")): item for item in package_rows if isinstance(item, Mapping)}
    key_assets = {str(item.get("asset_id")): item for item in key_rows if isinstance(item, Mapping)}
    if set(package_assets) != set(key_assets):
        errors.append("Confidential key asset set does not match the package.")
    systems = [str(key.get("baseline_system_id", "")), str(key.get("contextual_system_id", ""))]
    if not all(systems) or len(set(systems)) != 2:
        errors.append("Confidential key requires distinct baseline and contextual systems.")
    preference = {system: 0 for system in systems}
    comprehension = {system: {"correct": 0, "total": 0} for system in systems}
    asset_preferences = {asset_id: {system: 0 for system in systems} for asset_id in package_assets}
    cloud_acceptances = set()
    viewer_ids = set()
    rows = responses.get("responses")
    if not isinstance(rows, list):
        errors.append("Viewer responses must be a list.")
        rows = []
    for position, row in enumerate(rows, start=1):
        if not isinstance(row, Mapping):
            errors.append(f"Viewer response {position} must be an object.")
            continue
        viewer_id = str(row.get("viewer_id", "")).strip()
        prefix = f"Viewer {viewer_id or position!r}"
        if not viewer_id or viewer_id in viewer_ids:
            errors.append(f"{prefix} requires a unique pseudonymous ID.")
        viewer_ids.add(viewer_id)
        _timestamp(row.get("completed_at"), prefix, errors)
        if row.get("consent_confirmed") is not True:
            errors.append(f"{prefix} must confirm consent.")
        if not isinstance(row.get("cloud_upload_acceptable"), bool):
            errors.append(f"{prefix} cloud-upload acceptance must be boolean.")
        elif row["cloud_upload_acceptable"]:
            cloud_acceptances.add(viewer_id)
        assignments = row.get("assignments")
        if not isinstance(assignments, list):
            errors.append(f"{prefix} assignments must be a list.")
            assignments = []
        seen = set()
        for assignment in assignments:
            if not isinstance(assignment, Mapping):
                errors.append(f"{prefix} assignment must be an object.")
                continue
            asset_id = str(assignment.get("asset_id", ""))
            if asset_id in seen or asset_id not in package_assets:
                errors.append(f"{prefix} has a duplicate or unknown asset {asset_id!r}.")
                continue
            seen.add(asset_id)
            candidate_ids = {str(item.get("candidate_id")) for item in package_assets[asset_id].get("candidates", [])}
            order = assignment.get("presentation_order")
            if not isinstance(order, list) or len(order) != 2 or set(map(str, order)) != candidate_ids:
                errors.append(f"{prefix} asset {asset_id!r} has invalid presentation order.")
            preferred = str(assignment.get("preferred_candidate", ""))
            if preferred not in candidate_ids:
                errors.append(f"{prefix} asset {asset_id!r} has invalid preference.")
                continue
            mapping = key_assets[asset_id].get("candidate_systems", {})
            preferred_system = str(mapping.get(preferred, ""))
            if preferred_system not in preference:
                errors.append(f"{prefix} asset {asset_id!r} has invalid confidential mapping.")
                continue
            preference[preferred_system] += 1
            asset_preferences[asset_id][preferred_system] += 1
            _score_answers(prefix, asset_id, assignment.get("answers"), package_assets[asset_id], key_assets[asset_id], mapping, comprehension, errors)
        if seen != set(package_assets):
            errors.append(f"{prefix} does not cover every study asset exactly once.")

    viewer_count = len(viewer_ids)
    if viewer_count < 30:
        blockers.append("At least 30 Sinhala-speaking viewers are required.")
    if key.get("run_capture_ready") is not True:
        blockers.append("Viewer evidence is not bound to a ready system run.")
    if key.get("dry_run") is True:
        blockers.append("Synthetic viewer responses cannot authorize the experiment.")
    contextual_id = str(key.get("contextual_system_id", ""))
    comparisons = sum(preference.values())
    contextual_wins = preference.get(contextual_id, 0)
    rate = contextual_wins / comparisons if comparisons else 0.0
    interval = _wilson_interval(contextual_wins, comparisons)
    comprehension_summary = {
        system: {
            **counts,
            "rate": round(counts["correct"] / counts["total"], 4) if counts["total"] else 0.0,
        }
        for system, counts in comprehension.items()
    }
    return {
        "schema_version": VIEWER_ANALYSIS_SCHEMA,
        "study_id": str(package.get("study_id", "")),
        "package_sha256": package_hash,
        "dry_run": key.get("dry_run") is True,
        "valid": not errors,
        "evidence_ready": not errors and not blockers,
        "viewer_count": viewer_count,
        "comparison_count": comparisons,
        "preference_counts": preference,
        "contextual_preference_rate": round(rate, 4),
        "contextual_preference_ci_95": [round(value, 4) for value in interval],
        "threshold": VIEWER_PREFERENCE_THRESHOLD,
        "threshold_passed": rate >= VIEWER_PREFERENCE_THRESHOLD,
        "comprehension": comprehension_summary,
        "asset_preference_counts": asset_preferences,
        "cloud_upload_acceptance_rate": round(len(cloud_acceptances) / viewer_count, 4) if viewer_count else 0.0,
        "errors": errors,
        "blockers": blockers,
    }


def viewer_package_digest(package: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(package)).hexdigest()


def _load_outputs(root: Path, manifest: Mapping[str, Any], systems: set) -> Dict[Tuple[str, str], str]:
    outputs = {}
    for run in manifest.get("runs", []):
        asset_id = str(run.get("asset_id", ""))
        system_id = str(run.get("system_id", ""))
        if system_id not in systems:
            continue
        path = _resolve(root, run.get("output"))
        if path is None or not path.is_file():
            raise ValueError(f"Captured output does not exist for {(asset_id, system_id)!r}.")
        suffix = path.suffix.lower()
        if suffix == ".srt":
            subtitle_format = SubtitleFormat.SRT
        elif suffix in {".vtt", ".webvtt"}:
            subtitle_format = SubtitleFormat.WEBVTT
        else:
            raise ValueError(f"Unsupported captured subtitle extension: {suffix or '(none)'}.")
        document = parse_subtitle(path.read_text(encoding="utf-8-sig"), subtitle_format)
        outputs[(asset_id, system_id)] = serialize_subtitle(document)
    return outputs


def _questions(value: Any) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    if not isinstance(value, list) or not value:
        raise ValueError("Each viewer-study asset requires comprehension questions.")
    public = []
    answers = {}
    for question in value:
        if not isinstance(question, Mapping):
            raise ValueError("Comprehension questions must be objects.")
        question_id = _required_text(question, "question_id")
        prompt = _required_text(question, "prompt")
        options = question.get("options")
        correct = question.get("correct_option")
        if question_id in answers or not isinstance(options, list) or len(options) < 2 or not all(isinstance(item, str) and item.strip() for item in options):
            raise ValueError("Questions require unique IDs and at least two non-empty options.")
        if not isinstance(correct, int) or isinstance(correct, bool) or not 0 <= correct < len(options):
            raise ValueError(f"Question {question_id!r} has an invalid correct option.")
        public.append({"question_id": question_id, "prompt": prompt, "options": options})
        answers[question_id] = correct
    return public, answers


def _score_answers(prefix: str, asset_id: str, value: Any, package_asset: Mapping[str, Any], key_asset: Mapping[str, Any], mapping: Mapping[str, Any], totals: Dict[str, Dict[str, int]], errors: List[str]) -> None:
    if not isinstance(value, Mapping):
        errors.append(f"{prefix} asset {asset_id!r} answers must be an object.")
        return
    question_ids = {str(item.get("question_id")) for item in package_asset.get("questions", [])}
    candidate_ids = {str(item.get("candidate_id")) for item in package_asset.get("candidates", [])}
    if set(map(str, value)) != candidate_ids:
        errors.append(f"{prefix} asset {asset_id!r} must answer for both candidates.")
        return
    correct = key_asset.get("correct_options", {})
    for candidate_id in candidate_ids:
        candidate_answers = value.get(candidate_id)
        if not isinstance(candidate_answers, Mapping) or set(map(str, candidate_answers)) != question_ids:
            errors.append(f"{prefix} asset {asset_id!r} candidate {candidate_id!r} has incomplete answers.")
            continue
        system_id = str(mapping.get(candidate_id, ""))
        if system_id not in totals:
            errors.append(f"{prefix} asset {asset_id!r} candidate {candidate_id!r} has an invalid confidential mapping.")
            continue
        for question in package_asset.get("questions", []):
            question_id = str(question.get("question_id"))
            answer = candidate_answers.get(question_id)
            options = question.get("options", [])
            if not isinstance(answer, int) or isinstance(answer, bool) or not 0 <= answer < len(options):
                errors.append(f"{prefix} asset {asset_id!r} question {question_id!r} has an invalid answer.")
                continue
            totals[system_id]["total"] += 1
            totals[system_id]["correct"] += int(answer == correct.get(question_id))


def _wilson_interval(successes: int, observations: int, z: float = 1.96) -> Tuple[float, float]:
    if observations == 0:
        return 0.0, 0.0
    rate = successes / observations
    denominator = 1 + z * z / observations
    centre = (rate + z * z / (2 * observations)) / denominator
    margin = z * math.sqrt((rate * (1 - rate) + z * z / (4 * observations)) / observations) / denominator
    return max(0.0, centre - margin), min(1.0, centre + margin)


def _timestamp(value: Any, prefix: str, errors: List[str]) -> None:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError
    except ValueError:
        errors.append(f"{prefix} requires a completion timestamp with timezone.")


def _required_text(value: Mapping[str, Any], field: str) -> str:
    result = value.get(field)
    if not isinstance(result, str) or not result.strip():
        raise ValueError(f"{field} must be a non-empty string.")
    return result.strip()


def _resolve(root: Path, value: Any) -> Any:
    if not isinstance(value, str) or not value.strip():
        return None
    return (root / value).resolve()


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical_json(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")

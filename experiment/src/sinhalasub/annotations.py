"""Validation contracts for independent corpus annotations and adjudication."""

import hashlib
import json
from typing import Any, List, Mapping, Sequence, Set


ANNOTATION_SCHEMA = "sinhalasub.corpus-annotation.v1"
ADJUDICATION_SCHEMA = "sinhalasub.corpus-adjudication.v1"


def annotation_digest(record: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(record)).hexdigest()


def validate_annotation_record(
    record: Mapping[str, Any],
    corpus_id: str,
    asset_id: str,
    source_sha256: str,
    expected_challenges: Sequence[Mapping[str, Any]],
    allowed_annotators: Set[str],
) -> List[str]:
    errors: List[str] = []
    prefix = f"Asset {asset_id!r} annotation"
    if record.get("schema_version") != ANNOTATION_SCHEMA:
        errors.append(f"{prefix} has an unsupported schema.")
    if record.get("corpus_id") != corpus_id or record.get("asset_id") != asset_id:
        errors.append(f"{prefix} corpus/asset identity does not match the manifest.")
    if record.get("source_sha256") != source_sha256:
        errors.append(f"{prefix} source hash does not match the audited source.")
    annotator_id = str(record.get("annotator_id", "")).strip()
    if annotator_id not in allowed_annotators:
        errors.append(f"{prefix} annotator ID is not declared by the manifest.")
    _validate_cues(record.get("cues"), expected_challenges, prefix, errors)
    return errors


def validate_adjudication_record(
    record: Mapping[str, Any],
    corpus_id: str,
    asset_id: str,
    source_sha256: str,
    expected_challenges: Sequence[Mapping[str, Any]],
    adjudicator_id: str,
    annotation_hashes: Set[str],
) -> List[str]:
    errors: List[str] = []
    prefix = f"Asset {asset_id!r} adjudication"
    if record.get("schema_version") != ADJUDICATION_SCHEMA:
        errors.append(f"{prefix} has an unsupported schema.")
    if record.get("corpus_id") != corpus_id or record.get("asset_id") != asset_id:
        errors.append(f"{prefix} corpus/asset identity does not match the manifest.")
    if record.get("source_sha256") != source_sha256:
        errors.append(f"{prefix} source hash does not match the audited source.")
    if str(record.get("adjudicator_id", "")).strip() != adjudicator_id:
        errors.append(f"{prefix} adjudicator ID does not match the manifest.")
    input_hashes = record.get("input_annotation_sha256", [])
    valid_hashes = isinstance(input_hashes, list) and all(isinstance(value, str) for value in input_hashes)
    if not valid_hashes or set(input_hashes) != annotation_hashes or len(input_hashes) != len(annotation_hashes):
        errors.append(f"{prefix} must hash-link every independent annotation exactly once.")
    _validate_cues(record.get("cues"), expected_challenges, prefix, errors)
    return errors


def _validate_cues(
    cues: Any,
    expected_challenges: Sequence[Mapping[str, Any]],
    prefix: str,
    errors: List[str],
) -> None:
    if not isinstance(cues, list):
        errors.append(f"{prefix} cues must be a list.")
        return
    expected_ids = [str(challenge.get("cue_id", "")) for challenge in expected_challenges]
    if [str(cue.get("cue_id", "")) for cue in cues if isinstance(cue, Mapping)] != expected_ids or len(cues) != len(expected_ids):
        errors.append(f"{prefix} must cover every challenge cue exactly once in manifest order.")
        return
    for cue, challenge in zip(cues, expected_challenges):
        cue_id = str(challenge.get("cue_id", ""))
        if not str(cue.get("translation", "")).strip():
            errors.append(f"{prefix} cue {cue_id!r} requires a translation.")
        alternatives = cue.get("acceptable_alternatives")
        if not isinstance(alternatives, list) or any(not isinstance(value, str) or not value.strip() for value in alternatives):
            errors.append(f"{prefix} cue {cue_id!r} acceptable alternatives must be a list of non-empty strings.")
        if cue.get("tags") != challenge.get("tags"):
            errors.append(f"{prefix} cue {cue_id!r} tags do not match the manifest challenge tags.")
        if not isinstance(cue.get("notes", ""), str):
            errors.append(f"{prefix} cue {cue_id!r} notes must be text.")


def _canonical_json(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")

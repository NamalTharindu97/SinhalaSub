"""Validation contracts for independent corpus annotations and adjudication."""

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence, Set, Tuple

from .subtitles import SubtitleDocument, SubtitleFormat, parse_subtitle, serialize_subtitle


ANNOTATION_SCHEMA = "sinhalasub.corpus-annotation.v1"
ADJUDICATION_SCHEMA = "sinhalasub.corpus-adjudication.v1"


def annotation_digest(record: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(record)).hexdigest()


def build_annotation_template(manifest_path: Path, asset_id: str, annotator_id: str) -> Dict[str, Any]:
    corpus_id, asset, document, source_hash = _load_asset(manifest_path, asset_id)
    annotators = {str(value).strip() for value in asset.get("annotators", [])}
    if annotator_id not in annotators:
        raise ValueError(f"Annotator {annotator_id!r} is not declared for asset {asset_id!r}.")
    return {
        "schema_version": ANNOTATION_SCHEMA,
        "corpus_id": corpus_id,
        "asset_id": asset_id,
        "source_sha256": source_hash,
        "annotator_id": annotator_id,
        "cues": _template_cues(document, asset.get("challenges", [])),
    }


def build_adjudication_template(
    manifest_path: Path,
    asset_id: str,
    annotation_paths: Sequence[Path],
) -> Dict[str, Any]:
    corpus_id, asset, document, source_hash = _load_asset(manifest_path, asset_id)
    challenges = asset.get("challenges", [])
    annotators = {str(value).strip() for value in asset.get("annotators", [])}
    if len(annotation_paths) < 2:
        raise ValueError("At least two independent annotation files are required.")
    records = [json.loads(path.read_text(encoding="utf-8")) for path in annotation_paths]
    errors: List[str] = []
    for record in records:
        errors.extend(validate_annotation_record(record, corpus_id, asset_id, source_hash, challenges, annotators))
    record_ids = [str(record.get("annotator_id", "")).strip() for record in records]
    records.sort(key=annotation_digest)
    hashes = [annotation_digest(record) for record in records]
    if set(record_ids) != annotators or len(set(hashes)) != len(records):
        errors.append("Annotation inputs must uniquely cover every declared annotator.")
    if errors:
        raise ValueError(" ".join(errors))
    cues = _template_cues(document, challenges)
    for cue_index, cue in enumerate(cues):
        cue["independent_candidates"] = [
            {
                "label": f"candidate-{index}",
                "translation": record["cues"][cue_index]["translation"],
                "acceptable_alternatives": record["cues"][cue_index]["acceptable_alternatives"],
                "notes": record["cues"][cue_index].get("notes", ""),
            }
            for index, record in enumerate(records, start=1)
        ]
    return {
        "schema_version": ADJUDICATION_SCHEMA,
        "corpus_id": corpus_id,
        "asset_id": asset_id,
        "source_sha256": source_hash,
        "adjudicator_id": str(asset.get("adjudicator", "")).strip(),
        "input_annotation_sha256": hashes,
        "cues": cues,
    }


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


def _load_asset(manifest_path: Path, asset_id: str) -> Tuple[str, Mapping[str, Any], SubtitleDocument, str]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    corpus_id = str(manifest.get("corpus_id", "")).strip()
    if not corpus_id:
        raise ValueError("Corpus ID is required.")
    matches = [asset for asset in manifest.get("assets", []) if asset.get("id") == asset_id]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one asset with ID {asset_id!r}.")
    asset = matches[0]
    source_path = (manifest_path.parent / str(asset.get("source", ""))).resolve()
    suffix = source_path.suffix.lower()
    if suffix not in {".srt", ".vtt", ".webvtt"}:
        raise ValueError(f"Unsupported subtitle extension: {suffix or '(none)'}")
    subtitle_format = SubtitleFormat.WEBVTT if suffix in {".vtt", ".webvtt"} else SubtitleFormat.SRT
    document = parse_subtitle(source_path.read_text(encoding="utf-8-sig"), subtitle_format)
    source_hash = hashlib.sha256(serialize_subtitle(document).encode("utf-8")).hexdigest()
    return corpus_id, asset, document, source_hash


def _template_cues(document: SubtitleDocument, challenges: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    source_by_id = {cue.id: cue.text for cue in document.cues}
    if any(str(challenge.get("cue_id", "")) not in source_by_id for challenge in challenges):
        raise ValueError("Every challenge cue must exist in the source document.")
    return [
        {
            "cue_id": str(challenge.get("cue_id", "")),
            "source_text": source_by_id[str(challenge.get("cue_id", ""))],
            "translation": "",
            "acceptable_alternatives": [],
            "tags": challenge.get("tags", []),
            "notes": "",
        }
        for challenge in challenges
    ]

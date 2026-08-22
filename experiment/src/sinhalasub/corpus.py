"""Rights and readiness audit for the controlled evaluation corpus."""

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Set, Tuple

from .annotations import annotation_digest, validate_adjudication_record, validate_annotation_record
from .subtitles import SubtitleDocument, SubtitleFormat, parse_subtitle, serialize_subtitle


CORPUS_SCHEMA = "sinhalasub.corpus-manifest.v1"
AUDIT_SCHEMA = "sinhalasub.corpus-audit.v1"
REQUIRED_GENRES = (
    "modern-drama",
    "comedy",
    "crime-action",
    "fantasy",
    "documentary-technical",
    "youth-social",
)
REQUIRED_CHALLENGES = (
    "ambiguous-name",
    "pronoun",
    "idiom",
    "sarcasm",
    "negation",
    "number",
    "terminology",
    "profanity-tone",
    "line-length",
)


def audit_corpus_manifest(manifest_path: Path) -> Dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    root = manifest_path.parent
    errors: List[str] = []
    readiness_failures: List[str] = []
    asset_reports = []
    seen_ids: Set[str] = set()
    seen_source_hashes: Dict[str, str] = {}
    total_cues = 0
    challenge_keys: Set[Tuple[str, str]] = set()
    covered_genres: Set[str] = set()
    covered_challenges: Set[str] = set()
    covered_splits: Set[str] = set()

    if manifest.get("schema_version") != CORPUS_SCHEMA:
        errors.append("Unsupported or missing corpus manifest schema.")
    corpus_id = str(manifest.get("corpus_id", "")).strip()
    if not corpus_id:
        errors.append("Corpus ID is required.")

    assets = manifest.get("assets")
    if not isinstance(assets, list) or not assets:
        errors.append("At least one corpus asset is required.")
        assets = []

    for position, asset in enumerate(assets, start=1):
        report, documents = _audit_asset(root, corpus_id, asset, position, errors)
        asset_reports.append(report)
        asset_id = report["id"]
        if asset_id in seen_ids:
            errors.append(f"Duplicate asset ID: {asset_id!r}.")
        seen_ids.add(asset_id)
        covered_genres.add(report["genre"])
        covered_splits.add(report["split"])
        total_cues += report["cue_count"]

        source_hash = report.get("source_sha256")
        if source_hash:
            previous_asset = seen_source_hashes.get(source_hash)
            if previous_asset:
                errors.append(f"Assets {previous_asset!r} and {asset_id!r} reuse the same source content.")
            seen_source_hashes[source_hash] = asset_id

        source_ids = {cue.id for cue in documents[0].cues} if documents else set()
        for challenge in asset.get("challenges", []):
            cue_id = str(challenge.get("cue_id", ""))
            key = (asset_id, cue_id)
            if key in challenge_keys:
                errors.append(f"Asset {asset_id!r} repeats challenge cue {cue_id!r}.")
            challenge_keys.add(key)
            if cue_id not in source_ids:
                errors.append(f"Asset {asset_id!r} challenge cue {cue_id!r} does not exist.")
            tags = challenge.get("tags", [])
            if not isinstance(tags, list) or not tags:
                errors.append(f"Asset {asset_id!r} challenge cue {cue_id!r} requires at least one tag.")
                continue
            unknown = set(tags) - set(REQUIRED_CHALLENGES)
            if unknown:
                errors.append(f"Asset {asset_id!r} challenge cue {cue_id!r} has unknown tags: {sorted(unknown)}.")
            covered_challenges.update(tags)

    if not 1500 <= total_cues <= 2000:
        readiness_failures.append(f"Corpus has {total_cues} cues; readiness requires 1,500-2,000.")
    if not 150 <= len(challenge_keys) <= 250:
        readiness_failures.append(
            f"Corpus has {len(challenge_keys)} challenge cues; readiness requires 150-250."
        )
    missing_genres = sorted(set(REQUIRED_GENRES) - covered_genres)
    if missing_genres:
        readiness_failures.append(f"Missing required genres: {missing_genres}.")
    missing_challenges = sorted(set(REQUIRED_CHALLENGES) - covered_challenges)
    if missing_challenges:
        readiness_failures.append(f"Missing required challenge phenomena: {missing_challenges}.")
    if not {"development", "holdout"} <= covered_splits:
        readiness_failures.append("Corpus requires separate development and private holdout assets.")

    manifest_hash = hashlib.sha256(_canonical_json(manifest)).hexdigest()
    return {
        "schema_version": AUDIT_SCHEMA,
        "corpus_id": corpus_id,
        "manifest_sha256": manifest_hash,
        "valid": not errors,
        "ready": not errors and not readiness_failures,
        "counts": {
            "assets": len(assets),
            "cues": total_cues,
            "challenge_cues": len(challenge_keys),
            "genres": len(covered_genres & set(REQUIRED_GENRES)),
            "splits": len(covered_splits & {"development", "holdout"}),
        },
        "coverage": {
            "genres": sorted(covered_genres),
            "challenge_phenomena": sorted(covered_challenges),
            "splits": sorted(covered_splits),
        },
        "errors": errors,
        "readiness_failures": readiness_failures,
        "assets": asset_reports,
    }


def _audit_asset(
    root: Path,
    corpus_id: str,
    asset: Mapping[str, Any],
    position: int,
    errors: List[str],
) -> Tuple[Dict[str, Any], Tuple[SubtitleDocument, ...]]:
    asset_id = str(asset.get("id", f"asset-{position}")).strip()
    genre = str(asset.get("genre", "")).strip()
    split = str(asset.get("split", "")).strip()
    if genre not in REQUIRED_GENRES:
        errors.append(f"Asset {asset_id!r} has unsupported genre {genre!r}.")
    if split not in {"development", "holdout"}:
        errors.append(f"Asset {asset_id!r} has unsupported split {split!r}.")
    if not str(asset.get("provenance", "")).strip():
        errors.append(f"Asset {asset_id!r} requires provenance.")

    rights = asset.get("rights", {})
    if not str(rights.get("basis", "")).strip():
        errors.append(f"Asset {asset_id!r} requires a rights basis.")
    evidence_path = _resolve_path(root, rights.get("evidence"))
    if evidence_path is None or not evidence_path.is_file():
        errors.append(f"Asset {asset_id!r} rights evidence file does not exist.")

    annotators = asset.get("annotators", [])
    if not isinstance(annotators, list) or len({str(value).strip() for value in annotators if str(value).strip()}) < 2:
        errors.append(f"Asset {asset_id!r} requires at least two unique annotator IDs.")
    if not str(asset.get("adjudicator", "")).strip():
        errors.append(f"Asset {asset_id!r} requires an adjudicator ID.")
    if asset.get("acceptable_alternatives_documented") is not True:
        errors.append(f"Asset {asset_id!r} must document acceptable alternatives.")
    if asset.get("reference_independently_authored") is not True:
        errors.append(f"Asset {asset_id!r} must confirm independent reference authorship.")
    if split == "holdout" and asset.get("private_holdout") is not True:
        errors.append(f"Holdout asset {asset_id!r} must be marked private.")

    documents_by_role: Dict[str, SubtitleDocument] = {}
    paths = {}
    for role in ("source", "reference", "adjudicated_reference"):
        path = _resolve_path(root, asset.get(role))
        paths[role] = str(asset.get(role, ""))
        if path is None or not path.is_file():
            errors.append(f"Asset {asset_id!r} {role} file does not exist.")
            continue
        try:
            documents_by_role[role] = _load_document(path)
        except (OSError, UnicodeError, ValueError) as error:
            errors.append(f"Asset {asset_id!r} {role} is invalid: {error}")

    source_document = documents_by_role.get("source")
    cue_count = len(source_document.cues) if source_document else 0
    source_hash = _document_hash(source_document) if source_document else None
    document_hashes = {role: _document_hash(document) for role, document in documents_by_role.items()}
    if len(documents_by_role) == 3 and source_document:
        structure = _structure(source_document)
        if any(
            document.format is not source_document.format or _structure(document) != structure
            for role, document in documents_by_role.items()
            if role != "source"
        ):
            errors.append(f"Asset {asset_id!r} source/reference structures do not match.")

    annotation_hashes: Set[str] = set()
    annotation_paths = asset.get("annotation_files", [])
    annotation_ids: Set[str] = set()
    declared_annotators = {str(value).strip() for value in annotators if str(value).strip()} if isinstance(annotators, list) else set()
    if not isinstance(annotation_paths, list) or len(annotation_paths) < 2:
        errors.append(f"Asset {asset_id!r} requires at least two independent annotation files.")
        annotation_paths = []
    if source_hash:
        for value in annotation_paths:
            path = _resolve_path(root, value)
            record = _load_json_record(path, asset_id, "annotation", errors)
            if record is None:
                continue
            errors.extend(
                validate_annotation_record(
                    record,
                    corpus_id,
                    asset_id,
                    source_hash,
                    asset.get("challenges", []),
                    declared_annotators,
                )
            )
            annotation_ids.add(str(record.get("annotator_id", "")).strip())
            annotation_hashes.add(annotation_digest(record))
        if annotation_ids != declared_annotators or len(annotation_hashes) != len(annotation_paths):
            errors.append(f"Asset {asset_id!r} annotation files must uniquely cover every declared annotator.")

    adjudication_path_value = asset.get("adjudication_file")
    adjudication_path = _resolve_path(root, adjudication_path_value)
    adjudication_record = _load_json_record(adjudication_path, asset_id, "adjudication", errors)
    adjudication_hash = None
    if adjudication_record is not None and source_hash:
        errors.extend(
            validate_adjudication_record(
                adjudication_record,
                corpus_id,
                asset_id,
                source_hash,
                asset.get("challenges", []),
                str(asset.get("adjudicator", "")).strip(),
                annotation_hashes,
            )
        )
        adjudication_hash = annotation_digest(adjudication_record)

    return (
        {
            "id": asset_id,
            "genre": genre,
            "split": split,
            "cue_count": cue_count,
            "challenge_cues": len(asset.get("challenges", [])),
            "source_sha256": source_hash,
            "document_hashes": document_hashes,
            "annotation_sha256": sorted(annotation_hashes),
            "adjudication_sha256": adjudication_hash,
            "rights_evidence": str(rights.get("evidence", "")),
            "paths": paths,
            "annotation_files": [str(value) for value in annotation_paths],
            "adjudication_file": str(adjudication_path_value or ""),
        },
        (source_document,) if source_document else (),
    )


def _resolve_path(root: Path, value: Any) -> Any:
    if not isinstance(value, str) or not value.strip():
        return None
    return (root / value).resolve()


def _load_json_record(path: Any, asset_id: str, role: str, errors: List[str]) -> Any:
    if path is None or not path.is_file():
        errors.append(f"Asset {asset_id!r} {role} file does not exist.")
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        errors.append(f"Asset {asset_id!r} {role} file is invalid: {error}")
        return None
    if not isinstance(value, dict):
        errors.append(f"Asset {asset_id!r} {role} file must contain a JSON object.")
        return None
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


def _structure(document: SubtitleDocument) -> Tuple[Tuple[str, int, int, int], ...]:
    return tuple((cue.id, cue.index, cue.start_ms, cue.end_ms) for cue in document.cues)


def _document_hash(document: SubtitleDocument) -> str:
    return hashlib.sha256(serialize_subtitle(document).encode("utf-8")).hexdigest()


def _canonical_json(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")

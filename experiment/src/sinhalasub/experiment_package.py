"""Deterministic blinded packaging for the three-system experiment."""

from dataclasses import dataclass
import hashlib
import json
import random
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple
import zipfile

from .subtitles import SubtitleDocument, serialize_subtitle
from .translation import prepare_document


PACKAGE_SCHEMA = "sinhalasub.blinded-package.v1"
KEY_SCHEMA = "sinhalasub.blinding-key.v1"
RUBRIC_DIMENSIONS = (
    "accuracy",
    "fluency",
    "context",
    "tone_voice",
    "terminology",
    "readability",
    "cultural_appropriateness",
    "formatting",
)
CRITICAL_ERROR_CATEGORIES = (
    "name_entity",
    "context_meaning",
    "omission_addition",
    "tone_register",
    "terminology",
    "formatting_readability",
    "hallucination",
    "unclassified",
)


@dataclass(frozen=True)
class SystemOutput:
    id: str
    document: SubtitleDocument
    metadata: Mapping[str, Any]


def build_blinded_package(
    experiment_id: str,
    seed: int,
    source: SubtitleDocument,
    systems: Sequence[SystemOutput],
    provenance: str,
    rights_basis: str,
    system_freeze: Optional[Mapping[str, Any]] = None,
    system_run: Optional[Mapping[str, Any]] = None,
    evaluation_metadata: Optional[Mapping[str, Any]] = None,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    if not experiment_id.strip() or not provenance.strip() or not rights_basis.strip():
        raise ValueError("Experiment ID, provenance, and rights basis are required.")
    if len(systems) != 3 or len({system.id for system in systems}) != 3:
        raise ValueError("The controlled experiment requires exactly three unique systems.")

    source_structure = _structure(source)
    for system in systems:
        if system.document.format is not source.format or _structure(system.document) != source_structure:
            raise ValueError(f"System {system.id!r} does not preserve source cue IDs and timestamps.")

    _, context_blocks = prepare_document(source)
    source_by_id = {cue.id: cue for cue in source.cues}
    outputs_by_system = {
        system.id: {cue.id: cue for cue in system.document.cues}
        for system in systems
    }
    package_blocks = []
    key_blocks = []
    for block in context_blocks:
        ordered_systems = list(systems)
        block_seed = int.from_bytes(
            hashlib.sha256(f"{seed}:{block.id}".encode("utf-8")).digest(),
            "big",
        )
        random.Random(block_seed).shuffle(ordered_systems)

        candidates = []
        label_map = {}
        for position, system in enumerate(ordered_systems, start=1):
            label = f"candidate-{position}"
            label_map[label] = system.id
            candidates.append(
                {
                    "label": label,
                    "cues": [
                        {"id": cue_id, "text": outputs_by_system[system.id][cue_id].text}
                        for cue_id in block.cue_ids
                    ],
                }
            )

        package_blocks.append(
            {
                "id": block.id,
                "context_before": [_source_cue(source_by_id[cue_id]) for cue_id in block.context_before],
                "source_cues": [_source_cue(source_by_id[cue_id]) for cue_id in block.cue_ids],
                "context_after": [_source_cue(source_by_id[cue_id]) for cue_id in block.context_after],
                "candidates": candidates,
            }
        )
        challenge_tags_by_cue = (evaluation_metadata or {}).get("challenge_tags_by_cue", {})
        key_blocks.append(
            {
                "block_id": block.id,
                "labels": label_map,
                "genre": str((evaluation_metadata or {}).get("genre", "unspecified")),
                "challenge_tags": sorted(
                    {
                        tag
                        for cue_id in block.cue_ids
                        for tag in challenge_tags_by_cue.get(cue_id, [])
                    }
                ),
            }
        )

    source_hash = _document_hash(source)
    package = {
        "schema_version": PACKAGE_SCHEMA,
        "experiment_id": experiment_id,
        "source": {
            "format": source.format.value,
            "cue_count": len(source.cues),
            "sha256": source_hash,
            "provenance": provenance,
            "rights_basis": rights_basis,
        },
        "instructions": {
            "blinded": True,
            "review_complete_blocks": True,
            "candidate_labels_change_by_block": True,
            "response_schema": "sinhalasub.evaluator-response.v1",
            "rubric_dimensions": list(RUBRIC_DIMENSIONS),
            "critical_error_categories": list(CRITICAL_ERROR_CATEGORIES[:-1]),
            "rubric_score_range": [1, 5],
            "preference_rule": "Select exactly one preferred candidate per block.",
        },
        "blocks": package_blocks,
    }
    package_hash = package_digest(package)
    key = {
        "schema_version": KEY_SCHEMA,
        "experiment_id": experiment_id,
        "seed": int(seed),
        "package_sha256": package_hash,
        "source_sha256": source_hash,
        "systems": [
            {
                "id": system.id,
                "output_sha256": _document_hash(system.document),
                "metadata": dict(system.metadata),
            }
            for system in systems
        ],
        "blocks": key_blocks,
    }
    if system_freeze is not None:
        key["system_freeze"] = dict(system_freeze)
    if system_run is not None:
        key["system_run"] = dict(system_run)
    return package, key


def write_blinded_package(
    package: Mapping[str, Any],
    key: Mapping[str, Any],
    package_path: Path,
    key_path: Path,
) -> None:
    package_path.parent.mkdir(parents=True, exist_ok=True)
    key_path.parent.mkdir(parents=True, exist_ok=True)
    package_json = _json_bytes(package)
    with zipfile.ZipFile(package_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        entry = zipfile.ZipInfo("package.json", date_time=(1980, 1, 1, 0, 0, 0))
        entry.compress_type = zipfile.ZIP_DEFLATED
        entry.external_attr = 0o100644 << 16
        archive.writestr(entry, package_json)
    key_path.write_bytes(_json_bytes(key))


def package_digest(package: Mapping[str, Any]) -> str:
    return hashlib.sha256(_json_bytes(package)).hexdigest()


def _structure(document: SubtitleDocument) -> Tuple[Tuple[str, int, int, int], ...]:
    return tuple((cue.id, cue.index, cue.start_ms, cue.end_ms) for cue in document.cues)


def _document_hash(document: SubtitleDocument) -> str:
    return hashlib.sha256(serialize_subtitle(document).encode("utf-8")).hexdigest()


def _source_cue(cue: Any) -> Dict[str, Any]:
    return {
        "id": cue.id,
        "index": cue.index,
        "start_ms": cue.start_ms,
        "end_ms": cue.end_ms,
        "text": cue.text,
    }


def _json_bytes(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")

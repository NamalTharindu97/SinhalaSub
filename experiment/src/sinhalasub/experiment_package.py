"""Deterministic blinded packaging for the three-system experiment."""

from dataclasses import dataclass
import hashlib
import json
import random
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence, Tuple
import zipfile

from .subtitles import SubtitleDocument, serialize_subtitle
from .translation import prepare_document


PACKAGE_SCHEMA = "sinhalasub.blinded-package.v1"
KEY_SCHEMA = "sinhalasub.blinding-key.v1"


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
        key_blocks.append({"block_id": block.id, "labels": label_map})

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
        },
        "blocks": package_blocks,
    }
    package_hash = hashlib.sha256(_json_bytes(package)).hexdigest()
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

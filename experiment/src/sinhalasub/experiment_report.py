"""Versioned local report for controlled subtitle-review experiments."""

from datetime import datetime, timezone
import hashlib
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

from .subtitles import SubtitleDocument, serialize_subtitle


REPORT_SCHEMA = "sinhalasub.experiment-report.v1"
HARNESS_VERSION = "0.3.0"


def build_experiment_report(
    source: SubtitleDocument,
    target: SubtitleDocument,
    filename: str,
    session: Mapping[str, Any],
    preparation: Optional[Mapping[str, Any]] = None,
    quality: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    source_structure = tuple((cue.id, cue.index, cue.start_ms, cue.end_ms) for cue in source.cues)
    target_structure = tuple((cue.id, cue.index, cue.start_ms, cue.end_ms) for cue in target.cues)
    if source.format is not target.format or source_structure != target_structure:
        raise ValueError("Source and target document structures must match.")

    source_cues = {cue.id: cue for cue in source.cues}
    changed = [cue.id for cue in target.cues if source_cues[cue.id].text != cue.text]
    approved = [str(cue_id) for cue_id in session.get("approved_cue_ids", [])]
    approved_set = set(approved)
    target_ids = {cue.id for cue in target.cues}
    if not approved_set <= target_ids:
        raise ValueError("Approved cue IDs must exist in the subtitle document.")

    elapsed_ms = _non_negative_int(session, "elapsed_ms")
    active_edit_ms = _non_negative_int(session, "active_edit_ms")
    if active_edit_ms > elapsed_ms:
        raise ValueError("Active edit time cannot exceed elapsed time.")

    quality = quality or {}
    warnings_by_cue = quality.get("warnings_by_cue", {})
    return {
        "schema_version": REPORT_SCHEMA,
        "harness_version": HARNESS_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": {
            "filename": Path(filename).name,
            "format": source.format.value,
            "cue_count": len(source.cues),
            "sha256": hashlib.sha256(serialize_subtitle(source).encode("utf-8")).hexdigest(),
        },
        "system": {
            "condition": "manual-source-copy",
            "provider": None,
            "model": None,
            "prompt_version": None,
            "context_blocks": len((preparation or {}).get("blocks", [])),
            "protected_values": int((preparation or {}).get("protected_count", 0)),
            "provider_latency_ms": None,
            "input_units": 0,
            "output_units": 0,
            "estimated_cost_usd": 0,
        },
        "review": {
            "started_at": str(session["started_at"]),
            "ended_at": str(session["ended_at"]),
            "elapsed_ms": elapsed_ms,
            "active_edit_ms": active_edit_ms,
            "keyboard_actions": _non_negative_int(session, "keyboard_actions"),
            "edit_events": _non_negative_int(session, "edit_events"),
            "approval_changes": _non_negative_int(session, "approval_changes"),
            "changed_cue_count": len(changed),
            "approved_cue_count": len(approved_set),
            "qa_counts": quality.get("counts", {"high": 0, "medium": 0, "low": 0}),
        },
        "cues": [
            {
                "id": cue.id,
                "index": cue.index,
                "start_ms": cue.start_ms,
                "end_ms": cue.end_ms,
                "source_text": source_cues[cue.id].text,
                "final_text": cue.text,
                "changed": cue.id in changed,
                "approved": cue.id in approved_set,
                "warning_codes": [item["code"] for item in warnings_by_cue.get(cue.id, [])],
            }
            for cue in target.cues
        ],
    }


def _non_negative_int(values: Mapping[str, Any], field: str) -> int:
    value = int(values[field])
    if value < 0:
        raise ValueError(f"{field} cannot be negative.")
    return value

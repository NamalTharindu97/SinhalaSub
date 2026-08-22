"""Audit frozen provider-neutral system configurations for the experiment."""

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Set

from .corpus import audit_corpus_manifest


FREEZE_SCHEMA = "sinhalasub.system-freeze.v1"
FREEZE_AUDIT_SCHEMA = "sinhalasub.system-freeze-audit.v1"
REQUIRED_SYSTEM_ROLES = ("generic-mt", "isolated-llm", "contextual-pipeline")


def audit_system_freeze(manifest_path: Path) -> Dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    root = manifest_path.parent
    errors: List[str] = []
    readiness_failures: List[str] = []
    if manifest.get("schema_version") != FREEZE_SCHEMA:
        errors.append("Unsupported or missing system-freeze schema.")
    freeze_id = str(manifest.get("freeze_id", "")).strip()
    if not freeze_id:
        errors.append("Freeze ID is required.")
    dry_run = manifest.get("dry_run") is True
    if not isinstance(manifest.get("seed"), int):
        errors.append("A fixed integer randomisation seed is required.")
    if not str(manifest.get("rubric_version", "")).strip():
        errors.append("Rubric version is required.")

    corpus_value = manifest.get("corpus_manifest")
    corpus_path = _resolve_path(root, corpus_value)
    corpus_audit = None
    if corpus_path is None or not corpus_path.is_file():
        errors.append("Corpus manifest does not exist.")
    else:
        try:
            corpus_audit = audit_corpus_manifest(corpus_path)
        except (OSError, TypeError, ValueError, UnicodeError, json.JSONDecodeError) as error:
            errors.append(f"Corpus manifest is invalid: {error}")
        if corpus_audit and not corpus_audit["valid"]:
            errors.append("Corpus manifest does not pass its validity audit.")
        if corpus_audit and manifest.get("corpus_manifest_sha256") != corpus_audit["manifest_sha256"]:
            errors.append("Corpus manifest hash does not match the frozen hash.")
        if corpus_audit and not corpus_audit["ready"]:
            readiness_failures.append("Corpus has not passed the frozen readiness gate.")

    systems = manifest.get("systems")
    if not isinstance(systems, list):
        errors.append("Systems must be a list.")
        systems = []
    reports = []
    roles: Set[str] = set()
    ids: Set[str] = set()
    all_policies_approved = True
    for position, system in enumerate(systems, start=1):
        report, policy_approved = _audit_system(root, system, position, dry_run, errors)
        reports.append(report)
        if report["id"] in ids:
            errors.append(f"Duplicate system ID: {report['id']!r}.")
        ids.add(report["id"])
        roles.add(report["role"])
        all_policies_approved = all_policies_approved and policy_approved
    if len(systems) != 3 or roles != set(REQUIRED_SYSTEM_ROLES):
        errors.append(f"Systems must cover exactly these roles: {list(REQUIRED_SYSTEM_ROLES)}.")
    if dry_run:
        readiness_failures.append("Synthetic dry-run freezes cannot authorize a real experiment.")
    if not all_policies_approved:
        readiness_failures.append("Every real provider policy must be approved before system freeze.")

    return {
        "schema_version": FREEZE_AUDIT_SCHEMA,
        "freeze_id": freeze_id,
        "manifest_sha256": hashlib.sha256(_canonical_json(manifest)).hexdigest(),
        "dry_run": dry_run,
        "valid": not errors,
        "ready": not errors and not readiness_failures,
        "corpus": {
            "manifest": str(corpus_value or ""),
            "manifest_sha256": corpus_audit.get("manifest_sha256") if corpus_audit else None,
            "ready": corpus_audit.get("ready", False) if corpus_audit else False,
        },
        "systems": reports,
        "errors": errors,
        "readiness_failures": readiness_failures,
    }


def _audit_system(
    root: Path,
    system: Mapping[str, Any],
    position: int,
    dry_run: bool,
    errors: List[str],
) -> Any:
    system_id = str(system.get("id", f"system-{position}")).strip()
    role = str(system.get("role", "")).strip()
    prefix = f"System {system_id!r}"
    if role not in REQUIRED_SYSTEM_ROLES:
        errors.append(f"{prefix} has unsupported role {role!r}.")
    for field in ("provider", "model", "model_version", "adapter_version"):
        if not str(system.get(field, "")).strip():
            errors.append(f"{prefix} requires {field.replace('_', ' ')}.")
    instruction = system.get("instruction", {})
    instruction_value = instruction.get("path") if isinstance(instruction, Mapping) else None
    instruction_path = _resolve_path(root, instruction_value)
    instruction_hash = None
    if not isinstance(instruction, Mapping) or not str(instruction.get("version", "")).strip():
        errors.append(f"{prefix} requires an instruction version.")
    if instruction_path is None or not instruction_path.is_file():
        errors.append(f"{prefix} instruction artifact does not exist.")
    else:
        instruction_hash = hashlib.sha256(instruction_path.read_bytes()).hexdigest()
        if instruction.get("sha256") != instruction_hash:
            errors.append(f"{prefix} instruction hash does not match the frozen hash.")

    policy = system.get("data_policy", {})
    policy_status = str(policy.get("status", "")) if isinstance(policy, Mapping) else ""
    permitted_status = "not-applicable-synthetic" if dry_run else "approved"
    policy_approved = policy_status == "approved"
    if policy_status != permitted_status:
        errors.append(f"{prefix} data-policy status must be {permitted_status!r}.")
    for field in ("retention", "region", "reviewed_on"):
        if not isinstance(policy, Mapping) or not str(policy.get(field, "")).strip():
            errors.append(f"{prefix} data policy requires {field.replace('_', ' ')}.")
    if not isinstance(policy, Mapping) or policy.get("training_disabled") is not True:
        errors.append(f"{prefix} must keep provider training disabled.")
    return (
        {
            "id": system_id,
            "role": role,
            "provider": str(system.get("provider", "")),
            "model": str(system.get("model", "")),
            "model_version": str(system.get("model_version", "")),
            "adapter_version": str(system.get("adapter_version", "")),
            "instruction": str(instruction_value or ""),
            "instruction_sha256": instruction_hash,
            "data_policy_status": policy_status,
        },
        policy_approved or dry_run,
    )


def _resolve_path(root: Path, value: Any) -> Any:
    if not isinstance(value, str) or not value.strip():
        return None
    return (root / value).resolve()


def _canonical_json(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")

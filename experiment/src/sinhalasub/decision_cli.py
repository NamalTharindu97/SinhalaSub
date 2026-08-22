"""Audit Phase 0 evidence and apply the frozen product decision gate."""

import argparse
import json
from pathlib import Path
import sys

from .decision_gate import audit_decision


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply the frozen Phase 0 decision gate.")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--allow-not-authorized", action="store_true")
    args = parser.parse_args()
    try:
        audit = audit_decision(args.manifest)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, TypeError, ValueError, UnicodeError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"Wrote decision audit to {args.output}")
    if not audit["valid"]:
        return 1
    if not audit["evidence_ready"] and not args.allow_not_authorized:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

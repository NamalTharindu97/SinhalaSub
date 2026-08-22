"""Audit a rights-clean evaluation corpus manifest."""

import argparse
import json
from pathlib import Path
import sys

from .corpus import audit_corpus_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit evaluation corpus provenance and readiness.")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--allow-not-ready",
        action="store_true",
        help="Return success for a structurally valid dry run that has not met corpus thresholds.",
    )
    args = parser.parse_args()
    try:
        audit = audit_corpus_manifest(args.manifest)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"Wrote corpus audit to {args.output}")
    if not audit["valid"]:
        print("Corpus manifest is invalid.", file=sys.stderr)
        return 1
    if not audit["ready"] and not args.allow_not_ready:
        print("Corpus is valid but does not meet experiment readiness thresholds.", file=sys.stderr)
        return 2
    if not audit["ready"]:
        print("Corpus is valid but not ready; threshold failures were retained in the audit.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

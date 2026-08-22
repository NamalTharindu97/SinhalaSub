"""Audit captured outputs and metering for a frozen three-system run."""

import argparse
import json
from pathlib import Path
import sys

from .run_capture import audit_run_capture


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit frozen experiment system runs.")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--allow-not-ready", action="store_true")
    args = parser.parse_args()
    try:
        audit = audit_run_capture(args.manifest)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, TypeError, ValueError, UnicodeError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"Wrote system-run audit to {args.output}")
    if not audit["valid"]:
        return 1
    if not audit["ready"] and not args.allow_not_ready:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

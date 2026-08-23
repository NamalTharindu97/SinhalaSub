"""Analyze paired baseline/contextual subtitle editing sessions."""

import argparse
import json
from pathlib import Path
import sys

from .editing_analysis import analyze_editing_sessions


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze paired subtitle editing sessions.")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--allow-not-ready", action="store_true")
    args = parser.parse_args()
    try:
        analysis = analyze_editing_sessions(args.manifest)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(analysis, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, TypeError, ValueError, UnicodeError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"Wrote paired editing analysis to {args.output}")
    if not analysis["valid"]:
        return 1
    if not analysis["evidence_ready"] and not args.allow_not_ready:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

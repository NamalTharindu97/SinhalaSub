"""Generate independent annotation and adjudication workflow templates."""

import argparse
import json
from pathlib import Path
import sys

from .annotations import build_adjudication_template, build_annotation_template


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate corpus annotation workflow templates.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    annotation = subparsers.add_parser("annotation", help="Create an independent annotation template")
    annotation.add_argument("manifest", type=Path)
    annotation.add_argument("asset_id")
    annotation.add_argument("annotator_id")
    annotation.add_argument("output", type=Path)
    adjudication = subparsers.add_parser("adjudication", help="Create a blinded adjudication template")
    adjudication.add_argument("manifest", type=Path)
    adjudication.add_argument("asset_id")
    adjudication.add_argument("annotations", nargs="+", type=Path)
    adjudication.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.command == "annotation":
            record = build_annotation_template(args.manifest, args.asset_id, args.annotator_id)
            output = args.output
        else:
            record = build_adjudication_template(args.manifest, args.asset_id, args.annotations)
            output = args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, KeyError, TypeError, ValueError, UnicodeError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"Wrote {args.command} template to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

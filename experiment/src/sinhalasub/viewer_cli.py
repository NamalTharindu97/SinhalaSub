"""Build and analyze blinded viewer A/B study records."""

import argparse
import json
from pathlib import Path
import sys

from .viewer_study import analyze_viewer_responses, build_viewer_study


def main() -> int:
    parser = argparse.ArgumentParser(description="Build or analyze a blinded viewer A/B study.")
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build")
    build.add_argument("manifest", type=Path)
    build.add_argument("--package", required=True, type=Path)
    build.add_argument("--key", required=True, type=Path)
    analyze = commands.add_parser("analyze")
    analyze.add_argument("package", type=Path)
    analyze.add_argument("key", type=Path)
    analyze.add_argument("responses", type=Path)
    analyze.add_argument("--output", required=True, type=Path)
    analyze.add_argument("--allow-not-ready", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "build":
            package, key = build_viewer_study(args.manifest)
            _write(args.package, package)
            _write(args.key, key)
            print(f"Wrote viewer package to {args.package} and confidential key to {args.key}")
            return 0
        package = _read(args.package)
        key = _read(args.key)
        responses = _read(args.responses)
        analysis = analyze_viewer_responses(package, key, responses)
        _write(args.output, analysis)
        print(f"Wrote viewer analysis to {args.output}")
        if not analysis["valid"]:
            return 1
        if not analysis["evidence_ready"] and not args.allow_not_ready:
            return 2
        return 0
    except (OSError, TypeError, ValueError, UnicodeError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


def _read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())

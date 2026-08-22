"""Confidentially unblind and aggregate evaluator response files."""

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Dict
import zipfile

from .evaluation import aggregate_evaluator_responses


def analyze_files(package_path: Path, key_path: Path, response_paths: list, output_path: Path) -> None:
    with zipfile.ZipFile(package_path) as archive:
        package: Dict[str, Any] = json.loads(archive.read("package.json"))
    key = json.loads(key_path.read_text(encoding="utf-8"))
    responses = [json.loads(path.read_text(encoding="utf-8")) for path in response_paths]
    analysis = aggregate_evaluator_responses(package, key, responses)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(analysis, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate, unblind, and aggregate evaluator responses.")
    parser.add_argument("package", type=Path, help="Blinded evaluator ZIP")
    parser.add_argument("key", type=Path, help="Confidential blinding key")
    parser.add_argument("responses", nargs="+", type=Path, help="One or more evaluator JSON responses")
    parser.add_argument("--output", required=True, type=Path, help="Confidential analysis JSON path")
    args = parser.parse_args()
    try:
        analyze_files(args.package, args.key, args.responses, args.output)
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError, zipfile.BadZipFile) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"Wrote confidential analysis to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

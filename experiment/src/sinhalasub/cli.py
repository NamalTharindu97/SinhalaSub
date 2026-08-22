"""Normalize a subtitle file while preserving its canonical structure."""

import argparse
from pathlib import Path
import sys

from .subtitles import SubtitleError, SubtitleFormat, parse_subtitle, serialize_subtitle


def _format_for_path(path: Path) -> SubtitleFormat:
    suffix = path.suffix.lower()
    if suffix == ".srt":
        return SubtitleFormat.SRT
    if suffix in {".vtt", ".webvtt"}:
        return SubtitleFormat.WEBVTT
    raise SubtitleError("UNSUPPORTED_FORMAT", f"Unsupported file extension: {suffix or '(none)'}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Parse and normalize an SRT or WebVTT file without changing cue timing."
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    try:
        input_format = _format_for_path(args.input)
        output_format = _format_for_path(args.output)
        if input_format is not output_format:
            raise SubtitleError(
                "FORMAT_MISMATCH",
                "Input and output formats must match in the Phase 0 harness.",
            )

        source = args.input.read_text(encoding="utf-8-sig")
        document = parse_subtitle(source, input_format)
        args.output.write_text(
            serialize_subtitle(document),
            encoding="utf-8",
        )
    except (OSError, UnicodeError, SubtitleError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    print(f"Wrote {len(document.cues)} cues to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Deterministic subtitle quality checks for the Phase 0 experiment."""

from dataclasses import dataclass
import unicodedata
from typing import List, Tuple

from .subtitles import SubtitleDocument


@dataclass(frozen=True)
class QualityWarning:
    cue_id: str
    code: str
    severity: str
    message: str


def grapheme_count(text: str) -> int:
    """Count practical text clusters without splitting Unicode mark sequences."""
    count = 0
    after_joiner = False
    for character in text:
        if character == "\u200d":
            after_joiner = True
            continue
        if unicodedata.category(character).startswith("M") or after_joiner:
            after_joiner = False
            continue
        count += 1
    return count


def check_document(
    document: SubtitleDocument,
    max_lines: int = 2,
    soft_graphemes_per_line: int = 40,
    max_graphemes_per_second: float = 17.0,
    min_duration_ms: int = 1000,
    max_duration_ms: int = 7000,
) -> Tuple[QualityWarning, ...]:
    warnings: List[QualityWarning] = []
    previous_end = 0
    for cue in document.cues:
        duration_ms = cue.end_ms - cue.start_ms
        lines = cue.text.splitlines()
        if len(lines) > max_lines:
            warnings.append(
                QualityWarning(cue.id, "TOO_MANY_LINES", "medium", f"Uses {len(lines)} lines; target is {max_lines}.")
            )
        longest_line = max(grapheme_count(line) for line in lines)
        if longest_line > soft_graphemes_per_line:
            warnings.append(
                QualityWarning(
                    cue.id,
                    "LONG_LINE",
                    "medium",
                    f"Longest line is {longest_line} graphemes; soft target is {soft_graphemes_per_line}.",
                )
            )
        rate = grapheme_count(cue.text.replace("\n", "")) / (duration_ms / 1000)
        if rate > max_graphemes_per_second:
            warnings.append(
                QualityWarning(
                    cue.id,
                    "READING_SPEED",
                    "high",
                    f"Reading speed is {rate:.1f} graphemes/second; target is at most {max_graphemes_per_second:.1f}.",
                )
            )
        if duration_ms < min_duration_ms:
            warnings.append(
                QualityWarning(
                    cue.id,
                    "SHORT_DURATION",
                    "low",
                    f"Duration is {duration_ms / 1000:.2f}s; target is at least {min_duration_ms / 1000:.2f}s.",
                )
            )
        if duration_ms > max_duration_ms:
            warnings.append(
                QualityWarning(
                    cue.id,
                    "LONG_DURATION",
                    "low",
                    f"Duration is {duration_ms / 1000:.2f}s; target is at most {max_duration_ms / 1000:.2f}s.",
                )
            )
        if cue.start_ms < previous_end:
            warnings.append(
                QualityWarning(cue.id, "SOURCE_OVERLAP", "low", "Source timing overlaps the previous cue; timing remains unchanged.")
            )
        previous_end = max(previous_end, cue.end_ms)
    return tuple(warnings)

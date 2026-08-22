"""Strict subtitle parsing and normalized serialization for the Phase 0 experiment."""

from dataclasses import dataclass
from enum import Enum
import re
import unicodedata
from typing import List, Optional, Tuple


class SubtitleFormat(str, Enum):
    SRT = "srt"
    WEBVTT = "webvtt"


class SubtitleError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True)
class Cue:
    id: str
    index: int
    start_ms: int
    end_ms: int
    text: str
    settings: str = ""

    def __post_init__(self) -> None:
        if self.index < 1:
            raise SubtitleError("INVALID_INDEX", "Cue index must be positive.")
        if self.start_ms < 0 or self.end_ms <= self.start_ms:
            raise SubtitleError(
                "INVALID_TIMING",
                f"Cue {self.id!r} must end after a non-negative start time.",
            )
        if not self.text:
            raise SubtitleError("EMPTY_CUE", f"Cue {self.id!r} has no text.")


@dataclass(frozen=True)
class SubtitleDocument:
    format: SubtitleFormat
    cues: Tuple[Cue, ...]
    header: Tuple[str, ...] = ()
    webvtt_description: str = ""

    def __post_init__(self) -> None:
        if not self.cues:
            raise SubtitleError("NO_CUES", "Subtitle file contains no cues.")
        if len({cue.id for cue in self.cues}) != len(self.cues):
            raise SubtitleError("DUPLICATE_CUE_ID", "Cue IDs must be unique.")
        if tuple(cue.index for cue in self.cues) != tuple(range(1, len(self.cues) + 1)):
            raise SubtitleError("INVALID_ORDER", "Cue indexes must be contiguous and ordered.")


_SRT_TIMING = re.compile(
    r"^(?P<start>\d{2,}:\d{2}:\d{2},\d{3})\s+-->\s+"
    r"(?P<end>\d{2,}:\d{2}:\d{2},\d{3})$"
)
_VTT_TIMING = re.compile(
    r"^(?P<start>(?:\d{2,}:)?\d{2}:\d{2}\.\d{3})\s+-->\s+"
    r"(?P<end>(?:\d{2,}:)?\d{2}:\d{2}\.\d{3})"
    r"(?:\s+(?P<settings>.*))?$"
)


def parse_subtitle(source: str, subtitle_format: SubtitleFormat) -> SubtitleDocument:
    normalized = _normalize_source(source)
    if subtitle_format is SubtitleFormat.SRT:
        return _parse_srt(normalized)
    if subtitle_format is SubtitleFormat.WEBVTT:
        return _parse_webvtt(normalized)
    raise SubtitleError("UNSUPPORTED_FORMAT", f"Unsupported format: {subtitle_format}")


def serialize_subtitle(document: SubtitleDocument) -> str:
    if document.format is SubtitleFormat.SRT:
        return _serialize_srt(document)
    if document.format is SubtitleFormat.WEBVTT:
        return _serialize_webvtt(document)
    raise SubtitleError("UNSUPPORTED_FORMAT", f"Unsupported format: {document.format}")


def _normalize_source(source: str) -> str:
    if "\x00" in source:
        raise SubtitleError("INVALID_TEXT", "Subtitle content contains a NUL character.")
    source = source.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
    return unicodedata.normalize("NFC", source).strip("\n")


def _blocks(source: str) -> List[List[str]]:
    return [block.split("\n") for block in re.split(r"\n[ \t]*\n", source) if block.strip()]


def _parse_srt(source: str) -> SubtitleDocument:
    cues: List[Cue] = []
    for expected_index, lines in enumerate(_blocks(source), start=1):
        if len(lines) < 3:
            raise SubtitleError("MALFORMED_CUE", f"SRT cue {expected_index} is incomplete.")
        try:
            source_index = int(lines[0].strip())
        except ValueError as error:
            raise SubtitleError(
                "INVALID_CUE_ID", f"SRT cue {expected_index} must start with a numeric ID."
            ) from error
        match = _SRT_TIMING.fullmatch(lines[1].strip())
        if not match:
            raise SubtitleError("INVALID_TIMING", f"Invalid timing for SRT cue {source_index}.")
        text = "\n".join(lines[2:]).strip()
        cues.append(
            Cue(
                id=str(source_index),
                index=expected_index,
                start_ms=_parse_timestamp(match.group("start"), ","),
                end_ms=_parse_timestamp(match.group("end"), ","),
                text=text,
            )
        )
    return SubtitleDocument(format=SubtitleFormat.SRT, cues=tuple(cues))


def _parse_webvtt(source: str) -> SubtitleDocument:
    lines = source.split("\n")
    if not lines or not lines[0].startswith("WEBVTT"):
        raise SubtitleError("INVALID_HEADER", "WebVTT input must start with WEBVTT.")
    description = lines[0][len("WEBVTT") :].strip()

    header: List[str] = []
    position = 1
    while position < len(lines) and lines[position].strip():
        header.append(lines[position])
        position += 1
    while position < len(lines) and not lines[position].strip():
        position += 1

    cue_source = "\n".join(lines[position:])
    cues: List[Cue] = []
    for index, block in enumerate(_blocks(cue_source), start=1):
        if block[0].startswith(("NOTE", "STYLE", "REGION")):
            raise SubtitleError(
                "UNSUPPORTED_BLOCK",
                f"WebVTT {block[0].split()[0]} blocks are not supported yet.",
            )

        cue_id: Optional[str] = None
        timing_line = 0
        if "-->" not in block[0]:
            cue_id = block[0].strip()
            timing_line = 1
        if not cue_id:
            cue_id = str(index)
        if len(block) <= timing_line + 1:
            raise SubtitleError("MALFORMED_CUE", f"WebVTT cue {cue_id!r} is incomplete.")

        match = _VTT_TIMING.fullmatch(block[timing_line].strip())
        if not match:
            raise SubtitleError("INVALID_TIMING", f"Invalid timing for WebVTT cue {cue_id!r}.")
        text = "\n".join(block[timing_line + 1 :]).strip()
        cues.append(
            Cue(
                id=cue_id,
                index=index,
                start_ms=_parse_timestamp(match.group("start"), "."),
                end_ms=_parse_timestamp(match.group("end"), "."),
                text=text,
                settings=(match.group("settings") or "").strip(),
            )
        )
    return SubtitleDocument(
        format=SubtitleFormat.WEBVTT,
        cues=tuple(cues),
        header=tuple(header),
        webvtt_description=description,
    )


def _parse_timestamp(value: str, millisecond_separator: str) -> int:
    clock, milliseconds = value.rsplit(millisecond_separator, 1)
    parts = [int(part) for part in clock.split(":")]
    if len(parts) == 2:
        hours = 0
        minutes, seconds = parts
    else:
        hours, minutes, seconds = parts
    if minutes >= 60 or seconds >= 60:
        raise SubtitleError("INVALID_TIMING", f"Invalid timestamp: {value}")
    return ((hours * 60 + minutes) * 60 + seconds) * 1000 + int(milliseconds)


def _serialize_srt(document: SubtitleDocument) -> str:
    blocks = []
    for cue in document.cues:
        blocks.append(
            f"{cue.id}\n{_format_timestamp(cue.start_ms, ',')} --> "
            f"{_format_timestamp(cue.end_ms, ',')}\n{cue.text}"
        )
    return "\n\n".join(blocks) + "\n"


def _serialize_webvtt(document: SubtitleDocument) -> str:
    header = "WEBVTT"
    if document.webvtt_description:
        header += f" {document.webvtt_description}"
    if document.header:
        header += "\n" + "\n".join(document.header)
    blocks = []
    for cue in document.cues:
        settings = f" {cue.settings}" if cue.settings else ""
        blocks.append(
            f"{cue.id}\n{_format_timestamp(cue.start_ms, '.')} --> "
            f"{_format_timestamp(cue.end_ms, '.')}{settings}\n{cue.text}"
        )
    return header + "\n\n" + "\n\n".join(blocks) + "\n"


def _format_timestamp(milliseconds: int, separator: str) -> str:
    total_seconds, millis = divmod(milliseconds, 1000)
    total_minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(total_minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}{separator}{millis:03d}"

"""Provider-neutral translation preparation with protected subtitle invariants."""

from dataclasses import dataclass
import re
from typing import Iterable, List, Mapping, Optional, Protocol, Sequence, Tuple

from .subtitles import Cue, SubtitleDocument, SubtitleError


@dataclass(frozen=True)
class ProtectedValue:
    placeholder: str
    value: str
    kind: str


@dataclass(frozen=True)
class PreparedCue:
    id: str
    index: int
    start_ms: int
    end_ms: int
    source_text: str
    protected_text: str
    protected_values: Tuple[ProtectedValue, ...]


@dataclass(frozen=True)
class ContextBlock:
    id: str
    cue_ids: Tuple[str, ...]
    context_before: Tuple[str, ...]
    context_after: Tuple[str, ...]


@dataclass(frozen=True)
class TranslationRequest:
    block: ContextBlock
    cues: Tuple[PreparedCue, ...]
    style: str = "conversational"


@dataclass(frozen=True)
class TranslationCandidate:
    cue_id: str
    text: str
    warning_codes: Tuple[str, ...] = ()


class TranslationProvider(Protocol):
    name: str

    def translate(self, request: TranslationRequest) -> Sequence[TranslationCandidate]:
        ...


class EchoProvider:
    """Deterministic contract test provider; it does not perform translation."""

    name = "echo"

    def translate(self, request: TranslationRequest) -> Sequence[TranslationCandidate]:
        return tuple(
            TranslationCandidate(cue_id=cue.id, text=cue.protected_text)
            for cue in request.cues
        )


_TOKEN_PATTERN = re.compile(r"<PROTECTED_[A-Z]+_\d+>")
_BASE_PATTERNS = (
    ("URL", r"https?://[^\s<>]+"),
    ("CURRENCY", r"(?<!\w)(?:LKR|USD|EUR|GBP)\s*\d[\d,]*(?:\.\d+)?|[$€£]\s*\d[\d,]*(?:\.\d+)?"),
    ("DATE", r"(?<!\w)\d{1,4}[/-]\d{1,2}[/-]\d{1,4}(?!\w)"),
    ("NUMBER", r"(?<!\w)\d[\d,]*(?:\.\d+)?%?(?!\w)"),
)


def protect_text(
    text: str,
    confirmed_names: Iterable[str] = (),
    glossary: Optional[Mapping[str, str]] = None,
) -> Tuple[str, Tuple[ProtectedValue, ...]]:
    matches: List[Tuple[int, int, str, str]] = []
    names = sorted({name.strip() for name in confirmed_names if name.strip()}, key=len, reverse=True)
    if names:
        names_pattern = "|".join(re.escape(name) for name in names)
        for match in re.finditer(rf"(?<!\w)(?:{names_pattern})(?!\w)", text):
            matches.append((match.start(), match.end(), "NAME", match.group(0)))

    for source, target in sorted((glossary or {}).items(), key=lambda item: len(item[0]), reverse=True):
        for match in re.finditer(rf"(?<!\w){re.escape(source)}(?!\w)", text):
            matches.append((match.start(), match.end(), "TERM", target))

    for kind, pattern in _BASE_PATTERNS:
        for match in re.finditer(pattern, text):
            matches.append((match.start(), match.end(), kind, match.group(0)))

    selected: List[Tuple[int, int, str, str]] = []
    for candidate in sorted(matches, key=lambda item: (item[0], -(item[1] - item[0]))):
        if any(candidate[0] < existing[1] and candidate[1] > existing[0] for existing in selected):
            continue
        selected.append(candidate)

    protected_values: List[ProtectedValue] = []
    output: List[str] = []
    position = 0
    for number, (start, end, kind, value) in enumerate(selected, start=1):
        placeholder = f"<PROTECTED_{kind}_{number}>"
        output.extend((text[position:start], placeholder))
        protected_values.append(ProtectedValue(placeholder=placeholder, value=value, kind=kind))
        position = end
    output.append(text[position:])
    return "".join(output), tuple(protected_values)


def restore_text(text: str, protected_values: Sequence[ProtectedValue]) -> str:
    expected = {item.placeholder for item in protected_values}
    observed = _TOKEN_PATTERN.findall(text)
    if set(observed) != expected or any(observed.count(placeholder) != 1 for placeholder in expected):
        raise SubtitleError(
            "PROTECTED_VALUE_MISMATCH",
            "Translation output must contain every protected placeholder exactly once.",
        )

    restored = text
    for item in protected_values:
        restored = restored.replace(item.placeholder, item.value)
    return restored


def prepare_document(
    document: SubtitleDocument,
    confirmed_names: Iterable[str] = (),
    glossary: Optional[Mapping[str, str]] = None,
    max_cues_per_block: int = 8,
    max_gap_ms: int = 6000,
    context_cues: int = 2,
) -> Tuple[Tuple[PreparedCue, ...], Tuple[ContextBlock, ...]]:
    if max_cues_per_block < 1 or context_cues < 0 or max_gap_ms < 0:
        raise ValueError("Context grouping limits must be non-negative and max cues must be positive.")

    confirmed_names = tuple(confirmed_names)
    prepared = tuple(_prepare_cue(cue, confirmed_names, glossary or {}) for cue in document.cues)
    groups: List[List[PreparedCue]] = []
    current: List[PreparedCue] = []
    for cue in prepared:
        gap = cue.start_ms - current[-1].end_ms if current else 0
        if current and (len(current) >= max_cues_per_block or gap > max_gap_ms):
            groups.append(current)
            current = []
        current.append(cue)
    if current:
        groups.append(current)

    blocks = []
    all_ids = [cue.id for cue in prepared]
    id_positions = {cue_id: index for index, cue_id in enumerate(all_ids)}
    for number, group in enumerate(groups, start=1):
        first = id_positions[group[0].id]
        last = id_positions[group[-1].id]
        blocks.append(
            ContextBlock(
                id=f"block-{number}",
                cue_ids=tuple(cue.id for cue in group),
                context_before=tuple(all_ids[max(0, first - context_cues) : first]),
                context_after=tuple(all_ids[last + 1 : last + 1 + context_cues]),
            )
        )
    return prepared, tuple(blocks)


def run_translation(
    prepared_cues: Sequence[PreparedCue],
    blocks: Sequence[ContextBlock],
    provider: TranslationProvider,
    style: str = "conversational",
) -> Tuple[TranslationCandidate, ...]:
    if not style.strip():
        raise ValueError("Translation style is required.")
    cues_by_id = {cue.id: cue for cue in prepared_cues}
    results: List[TranslationCandidate] = []
    for block in blocks:
        request_cues = tuple(cues_by_id[cue_id] for cue_id in block.cue_ids)
        candidates = tuple(provider.translate(TranslationRequest(block=block, cues=request_cues, style=style)))
        expected_ids = tuple(block.cue_ids)
        observed_ids = tuple(candidate.cue_id for candidate in candidates)
        if observed_ids != expected_ids:
            raise SubtitleError(
                "INVALID_PROVIDER_RESPONSE",
                f"Provider {provider.name!r} changed, omitted, duplicated, or reordered cue IDs.",
            )
        for candidate in candidates:
            cue = cues_by_id[candidate.cue_id]
            results.append(
                TranslationCandidate(
                    cue_id=candidate.cue_id,
                    text=restore_text(candidate.text, cue.protected_values),
                    warning_codes=candidate.warning_codes,
                )
            )
    return tuple(results)


def _prepare_cue(cue: Cue, confirmed_names: Iterable[str], glossary: Mapping[str, str]) -> PreparedCue:
    protected_text, protected_values = protect_text(cue.text, confirmed_names, glossary)
    return PreparedCue(
        id=cue.id,
        index=cue.index,
        start_ms=cue.start_ms,
        end_ms=cue.end_ms,
        source_text=cue.text,
        protected_text=protected_text,
        protected_values=protected_values,
    )

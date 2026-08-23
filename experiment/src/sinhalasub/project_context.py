"""Versioned project context for character aliases, style, and glossary terms."""

from dataclasses import dataclass
from typing import Any, Mapping, Tuple


PROJECT_CONTEXT_SCHEMA = "sinhalasub.project-context.v1"


@dataclass(frozen=True)
class Character:
    name: str
    aliases: Tuple[str, ...] = ()


@dataclass(frozen=True)
class GlossaryEntry:
    source: str
    target: str


@dataclass(frozen=True)
class ProjectContext:
    style: str
    characters: Tuple[Character, ...]
    glossary: Tuple[GlossaryEntry, ...]

    @property
    def names_and_aliases(self) -> Tuple[str, ...]:
        return tuple(value for character in self.characters for value in (character.name,) + character.aliases)

    @property
    def glossary_map(self) -> Mapping[str, str]:
        return {entry.source: entry.target for entry in self.glossary}


def parse_project_context(value: Mapping[str, Any]) -> ProjectContext:
    if value.get("schema_version") != PROJECT_CONTEXT_SCHEMA:
        raise ValueError("Unsupported or missing project-context schema.")
    style = str(value.get("style", "")).strip()
    if not style:
        raise ValueError("Project context requires a style.")
    raw_characters = value.get("characters", [])
    raw_glossary = value.get("glossary", [])
    if not isinstance(raw_characters, list) or not isinstance(raw_glossary, list):
        raise ValueError("Characters and glossary must be lists.")

    characters = []
    seen_names = set()
    for raw in raw_characters:
        if not isinstance(raw, Mapping):
            raise ValueError("Each character must be an object.")
        name = str(raw.get("name", "")).strip()
        aliases_value = raw.get("aliases", [])
        if not name or not isinstance(aliases_value, list):
            raise ValueError("Each character requires a name and alias list.")
        aliases = tuple(str(alias).strip() for alias in aliases_value)
        if any(not alias for alias in aliases):
            raise ValueError("Character aliases cannot be empty.")
        terms = (name,) + aliases
        if len(set(terms)) != len(terms) or seen_names.intersection(terms):
            raise ValueError("Character names and aliases must be globally unique.")
        seen_names.update(terms)
        characters.append(Character(name=name, aliases=aliases))

    glossary = []
    seen_sources = set()
    for raw in raw_glossary:
        if not isinstance(raw, Mapping):
            raise ValueError("Each glossary entry must be an object.")
        source = str(raw.get("source", "")).strip()
        target = str(raw.get("target", "")).strip()
        if not source or not target:
            raise ValueError("Each glossary entry requires source and target text.")
        if source in seen_sources:
            raise ValueError("Glossary source terms must be unique.")
        if source in seen_names:
            raise ValueError("A term cannot be both a character name/alias and glossary source.")
        seen_sources.add(source)
        glossary.append(GlossaryEntry(source=source, target=target))
    return ProjectContext(style=style, characters=tuple(characters), glossary=tuple(glossary))

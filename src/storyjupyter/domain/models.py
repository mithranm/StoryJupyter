# src/storyjupyter/domain/models.py
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Optional, Dict, FrozenSet
from uuid import UUID, uuid4
from .time import StoryTime


@dataclass(frozen=True)
class Pronouns:
    """Immutable pronoun set with proper grammatical forms"""

    subject: str  # he/she/they
    object: str  # him/her/them
    possessive: str  # his/her/their
    possessive_pronoun: str  # his/hers/theirs
    reflexive: str  # himself/herself/themselves

    _PRONOUN_FORMS = {
        "he": ("he", "him", "his", "his", "himself"),
        "she": ("she", "her", "her", "hers", "herself"),
        "they": ("they", "them", "their", "theirs", "themselves"),
    }

    @classmethod
    def from_subject(cls, subject: str) -> "Pronouns":
        """Factory method to create full pronoun set from subject pronoun"""
        if subject not in cls._PRONOUN_FORMS:
            raise ValueError(f"Unknown pronoun: {subject}")
        return cls(*cls._PRONOUN_FORMS[subject])


@dataclass
class Relationship:
    """Represents a relationship between two characters"""

    type: str
    description: Optional[str] = None


@dataclass
class Character:
    """Story character with consistent identity"""

    id: UUID = field(default_factory=uuid4)
    first_name: str = ""
    middle_names: list[str] = field(default_factory=list)
    last_name: str = ""
    pronouns: Optional[Pronouns] = None
    chapter_introduced: Optional[int] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    relationships: Dict[UUID, Relationship] = field(default_factory=dict)

    def __post_init__(self):
        """Ensure relationships and attributes are proper dicts"""
        if not isinstance(self.relationships, dict):
            object.__setattr__(self, "relationships", dict(self.relationships))
        if not isinstance(self.attributes, dict):
            object.__setattr__(self, "attributes", dict(self.attributes))

    @property
    def name(self) -> str:
        """Full name representation"""
        components = [self.first_name]
        if self.middle_names:
            components.extend(self.middle_names)
        components.append(self.last_name)
        return " ".join(filter(None, components))

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        if self.pronouns:
            data["pronouns"] = asdict(self.pronouns)
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Character":
        """Create from dictionary representation"""
        if "pronouns" in data and data["pronouns"]:
            data["pronouns"] = Pronouns(**data["pronouns"])

        # Extract special fields
        attrs = data.pop("attributes", {})
        rels = data.pop("relationships", {})

        # Create instance
        char = cls(**data)

        # Add attributes and relationships
        object.__setattr__(char, "attributes", attrs)
        object.__setattr__(char, "relationships", rels)

        return char


@dataclass(frozen=True)
class StoryEvent:
    """Immutable story event"""

    id: UUID
    time: datetime
    location: str
    content: str
    chapter: int
    characters: FrozenSet[UUID] = field(default_factory=frozenset)

    def __post_init__(self):
        """Ensure time has timezone"""
        object.__setattr__(self, "time", StoryTime.ensure_tz(self.time))


@dataclass
class StoryMetadata:
    """Story-level metadata"""

    title: str
    author: str
    created_at: datetime = field(default_factory=StoryTime.now)
    last_modified: datetime = field(default_factory=StoryTime.now)

    def __post_init__(self):
        """Ensure times have timezone"""
        object.__setattr__(self, "created_at", StoryTime.ensure_tz(self.created_at))
        object.__setattr__(
            self, "last_modified", StoryTime.ensure_tz(self.last_modified)
        )

    def update_modified(self):
        """Update last modified timestamp"""
        object.__setattr__(self, "last_modified", StoryTime.now())

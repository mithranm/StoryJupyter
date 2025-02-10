# storyjupyter/core/models.py
from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any, Optional
from .types import EventMetadata, PronounSet
from .pronouns import Pronouns

@dataclass(frozen=True, slots=True)
class Character:
    """Immutable character representation"""
    name: str
    description: str
    pronouns: Pronouns
    attributes: dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def create(
        cls, 
        name: str, 
        description: str, 
        pronoun_set: PronounSet,
        **attributes
    ) -> "Character":
        """Factory method with pronoun support"""
        return cls(
            name=name,
            description=description,
            pronouns=Pronouns(pronoun_set),
            attributes=attributes
        )

@dataclass(frozen=True, slots=True)
class Brand:
    """Immutable brand representation"""
    real_name: str
    story_name: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

@dataclass(frozen=True, slots=True)
class TimelineEvent:
    """Immutable timeline event"""
    timestamp: datetime
    location: str
    content: str
    chapter: int
    metadata: EventMetadata = field(default_factory=lambda: {"tags": []})

    def __post_init__(self) -> None:
        if not isinstance(self.timestamp, datetime):
            object.__setattr__(self, "timestamp", datetime.fromisoformat(str(self.timestamp)))
        if self.timestamp.tzinfo is None:
            object.__setattr__(self, "timestamp", self.timestamp.replace(tzinfo=UTC))
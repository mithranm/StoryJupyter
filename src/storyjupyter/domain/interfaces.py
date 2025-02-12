# src/storyjupyter/domain/interfaces.py
from typing import Protocol, Sequence, Optional
from datetime import datetime
from uuid import UUID

from .models import Character, StoryElement, StoryMetadata


class CharacterGenerator(Protocol):
    """Protocol for character generation strategies"""

    def generate(
        self,
        *,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        pronouns: Optional[str] = None,
        **attributes,
    ) -> Character:
        """Generate a character with the given constraints"""
        ...


class StoryRepository(Protocol):
    """Protocol for story persistence"""

    def save_metadata(self, metadata: StoryMetadata) -> None:
        """Save story metadata"""
        ...

    def get_metadata(self) -> Optional[StoryMetadata]:
        """Retrieve story metadata"""
        ...

    def save_character(self, character: Character) -> None:
        """Save character"""
        ...

    def get_character(self, id: UUID) -> Optional[Character]:
        """Retrieve character by ID"""
        ...

    def get_characters(self, chapter: Optional[int] = None) -> Sequence[Character]:
        """Get all characters, optionally filtered by chapter introduced"""
        ...

    def save_element(self, element: StoryElement) -> None:
        """Save story element"""
        ...

    def get_elements(
        self,
        *,
        chapter: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Sequence[StoryElement]:
        """Get elements with optional filters"""
        ...

    def clear_chapter(self, chapter: int) -> None:
        """Remove all elements and characters from specified chapter"""
        ...

    def clear_from_chapter_onwards(self, chapter: int) -> None:
        """Remove all elements and characters from chapter onwards"""
        ...

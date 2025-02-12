from typing import Optional, Sequence, Union
from datetime import datetime
from uuid import UUID

from ..domain.models import Character, StoryElement, StoryMetadata
from ..domain.interfaces import StoryRepository
from ..domain.time import StoryTime


class DummyStoryRepository(StoryRepository):
    """Dummy implementation of StoryRepository that doesn't persist data"""

    def __init__(
        self,
        connection_string: str = "",
        database: str = "",
        metadata_collection: str = "metadata",
        character_collection: str = "characters",
        element_collection: str = "elements",
    ):
        """Initialize dummy repository with in-memory storage"""
        self._metadata = None
        self._characters = {}
        self._elements = []

    def save_metadata(self, metadata: StoryMetadata) -> None:
        """Save story metadata in memory"""
        self._metadata = metadata

    def get_metadata(self) -> Optional[StoryMetadata]:
        """Retrieve story metadata"""
        return self._metadata

    def save_character(self, character: Character) -> None:
        """Save character in memory"""
        if str(character.id) in self._characters:
            raise ValueError(f"Character ID '{character.id}' already exists.")
        self._characters[str(character.id)] = character

    def get_character(self, id: Union[str, UUID]) -> Optional[Character]:
        """Retrieve character by ID"""
        return self._characters.get(str(id))

    def get_characters(self, chapter: Optional[int] = None) -> Sequence[Character]:
        """Get all characters, optionally filtered by chapter introduced"""
        if chapter is None:
            return list(self._characters.values())

        return [
            char
            for char in self._characters.values()
            if getattr(char, "chapter_introduced", None) == chapter
        ]

    def save_element(self, element: StoryElement) -> None:
        """Save story element in memory"""
        # Check if element with same ID already exists
        existing_element_index = next(
            (index for index, e in enumerate(self._elements) if e.id == element.id), None
        )

        if existing_element_index is not None:
            self._elements[existing_element_index] = element
        else:
            self._elements.append(element)

    def get_elements(
        self,
        *,
        chapter: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Sequence[StoryElement]:
        """Get elements with optional filters"""
        filtered_elements = self._elements.copy()

        # Filter by chapter
        if chapter is not None:
            filtered_elements = [
                element for element in filtered_elements if element.chapter == chapter
            ]

        # Filter by time range
        if start_time is not None or end_time is not None:
            filtered_elements = [
                element
                for element in filtered_elements
                if (start_time is None or element.time >= StoryTime.ensure_tz(start_time))
                and (end_time is None or element.time <= StoryTime.ensure_tz(end_time))
            ]

        # Sort by chapter and time
        return sorted(filtered_elements, key=lambda e: (e.chapter, e.time))

    def clear_chapter(self, chapter: int) -> None:
        """Remove all elements and characters from specified chapter"""
        # Remove elements
        self._elements = [element for element in self._elements if element.chapter != chapter]

        # Remove characters
        self._characters = {
            k: v
            for k, v in self._characters.items()
            if getattr(v, "chapter_introduced", None) != chapter
        }

    def clear_from_chapter_onwards(self, chapter: int) -> None:
        """Remove all elements and characters from chapter onwards"""
        # Remove elements
        self._elements = [element for element in self._elements if element.chapter < chapter]

        # Remove characters
        self._characters = {
            k: v
            for k, v in self._characters.items()
            if getattr(v, "chapter_introduced", None) is None
            or getattr(v, "chapter_introduced", None) < chapter
        }

    def __del__(self):
        """Cleanup method (no-op for dummy repository)"""
        pass

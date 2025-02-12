from typing import Optional, Sequence
from datetime import datetime
from uuid import UUID

from ..domain.models import Character, StoryEvent, StoryMetadata
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
        event_collection: str = "events",
    ):
        """Initialize dummy repository with in-memory storage"""
        self._metadata = None
        self._characters = {}
        self._events = []

    def save_metadata(self, metadata: StoryMetadata) -> None:
        """Save story metadata in memory"""
        self._metadata = metadata

    def get_metadata(self) -> Optional[StoryMetadata]:
        """Retrieve story metadata"""
        return self._metadata

    def save_character(self, character: Character) -> None:
        """Save character in memory"""
        self._characters[str(character.id)] = character

    def get_character(self, id: UUID) -> Optional[Character]:
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

    def save_event(self, event: StoryEvent) -> None:
        """Save story event in memory"""
        # Check if event with same ID already exists
        existing_event_index = next(
            (index for index, e in enumerate(self._events) if e.id == event.id), None
        )

        if existing_event_index is not None:
            self._events[existing_event_index] = event
        else:
            self._events.append(event)

    def get_events(
        self,
        *,
        chapter: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Sequence[StoryEvent]:
        """Get events with optional filters"""
        filtered_events = self._events.copy()

        # Filter by chapter
        if chapter is not None:
            filtered_events = [
                event for event in filtered_events if event.chapter == chapter
            ]

        # Filter by time range
        if start_time is not None or end_time is not None:
            filtered_events = [
                event
                for event in filtered_events
                if (start_time is None or event.time >= StoryTime.ensure_tz(start_time))
                and (end_time is None or event.time <= StoryTime.ensure_tz(end_time))
            ]

        # Sort by chapter and time
        return sorted(filtered_events, key=lambda e: (e.chapter, e.time))

    def clear_chapter(self, chapter: int) -> None:
        """Remove all events and characters from specified chapter"""
        # Remove events
        self._events = [event for event in self._events if event.chapter != chapter]

        # Remove characters
        self._characters = {
            k: v
            for k, v in self._characters.items()
            if getattr(v, "chapter_introduced", None) != chapter
        }

    def clear_from_chapter_onwards(self, chapter: int) -> None:
        """Remove all events and characters from chapter onwards"""
        # Remove events
        self._events = [event for event in self._events if event.chapter < chapter]

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

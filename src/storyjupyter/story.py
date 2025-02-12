# src/storyjupyter/story.py
from datetime import datetime, timezone, timedelta
from typing import Optional
from uuid import UUID, uuid4

from .domain.models import Character, StoryEvent, StoryMetadata, Relationship, Pronouns
from .domain.interfaces import StoryRepository, CharacterGenerator
from .domain.exceptions import (
    UninitializedStoryError,
    UninitializedLocationError,
)
from .persistence import DummyStoryRepository


class Story:
    """Main story management class"""

    def __init__(
        self,
        title: str,
        author: str,
        faker_generator: CharacterGenerator,
        llm_generator: CharacterGenerator,
        repo: Optional[StoryRepository] = DummyStoryRepository(),
        chapter: int = 1,
    ):
        self._metadata = StoryMetadata(
            title=title, author=author, created_at=datetime.now(timezone.utc)
        )
        self._repo = repo
        self._repo.save_metadata(self._metadata)
        self._current_chapter = chapter
        self._current_time = None
        self._current_location = None
        self.faker_generator = faker_generator
        self.llm_generator = llm_generator

        # In-memory cache of recent/active characters
        self._character_cache: dict[UUID, Character] = {}
        self.clear_chapter(chapter=chapter)

    @property
    def metadata(self) -> StoryMetadata:
        """Get story metadata"""
        return self._metadata

    @property
    def current_chapter(self) -> int:
        return self._current_chapter

    @property
    def current_time(self) -> datetime:
        return self._current_time

    def set_time(self, time: datetime):
        self._current_time = time
        self._metadata.last_modified = datetime.now(timezone.utc)
        self._repo.save_metadata(self._metadata)

    def advance_time(self, delta: timedelta):
        if self._current_time is None:
            raise UninitializedStoryError(
                "Cannot advance time before setting initial time."
            )
        self._current_time += delta
        self._metadata.last_modified = datetime.now(timezone.utc)
        self._repo.save_metadata(self._metadata)

    def set_location(self, location: str):
        self._current_location = location
        self._metadata.last_modified = datetime.now(timezone.utc)
        self._repo.save_metadata(self._metadata)

    def add_event(self, content: str, character_ids: list[UUID] = None) -> StoryEvent:
        if self._current_time is None:
            raise UninitializedStoryError(
                "Cannot add event before setting initial time."
            )
        if self._current_location is None:
            raise UninitializedLocationError(
                "Cannot add event before setting a location."
            )

        event = StoryEvent(
            id=uuid4(),
            time=self._current_time,
            location=self._current_location,
            content=content,
            chapter=self._current_chapter,
            characters=frozenset(character_ids) if character_ids else frozenset(),
        )
        self._repo.save_event(event)
        self._metadata.last_modified = datetime.now(timezone.utc)
        self._repo.save_metadata(self._metadata)
        return event

    def create_character(
        self,
        character_id: UUID = None,
        first_name: str = None,
        last_name: str = None,
        pronouns: Pronouns = None,
        generator_type: str = "faker",
    ) -> Character:
        if generator_type == "faker":
            generator = self.faker_generator
        elif generator_type == "llm":
            generator = self.llm_generator
        else:
            raise ValueError(f"Invalid generator type: {generator_type}")

        character = generator.generate(
            character_id=character_id,
            first_name=first_name,
            last_name=last_name,
            pronouns=pronouns,
            chapter=self._current_chapter,
        )
        self._repo.save_character(character)
        self._metadata.last_modified = datetime.now(timezone.utc)
        self._repo.save_metadata(self._metadata)
        return character

    def add_relationship(
        self,
        character_id: UUID,
        related_character_id: UUID,
        relationship_type: str,
        description: Optional[str] = None,
    ) -> None:
        """Add a relationship between characters"""
        character = self.get_character(character_id)
        related = self.get_character(related_character_id)

        relationship = Relationship(type=relationship_type, description=description)

        # Update both characters
        character.relationships[related.id] = relationship
        related.relationships[character.id] = relationship

        # Save changes
        self._repo.save_character(character)
        self._repo.save_character(related)

    def get_character(self, character_id: UUID) -> Character:
        """Retrieve a character by ID, using the cache if available."""
        if character_id in self._character_cache:
            return self._character_cache[character_id]

        character = self._repo.get_character(character_id)
        if character:
            self._character_cache[character_id] = character  # Cache the character
            return character
        else:
            raise ValueError(f"Character with ID {character_id} not found.")

    def generate_manuscript(self) -> str:
        manuscript = f"# Chapter {self.current_chapter}\n\n"

        events = self._repo.get_events(chapter=self.current_chapter)

        # Group events by location
        location_events = {}
        for event in events:
            if event.location not in location_events:
                location_events[event.location] = []
            location_events[event.location].append(event)

        # Add location headers and event content
        for location, events in location_events.items():
            manuscript += f"## {location}\n"
            for event in events:
                manuscript += event.content + "\n"

        return manuscript

    def clear_chapter(self, chapter: int):
        self._repo.clear_from_chapter_onwards(chapter)
        self._metadata.last_modified = datetime.now(timezone.utc)
        self._repo.save_metadata(self._metadata)

    def start_chapter(self, chapter_number: int = None):
        if chapter_number is None:
            chapter_number = self._current_chapter
        self._repo.clear_chapter(chapter_number)
        self._current_chapter = chapter_number
        self._metadata.last_modified = datetime.now(timezone.utc)
        self._repo.save_metadata(self._metadata)

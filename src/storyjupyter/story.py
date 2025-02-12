# src/storyjupyter/story.py
from datetime import datetime, timezone, timedelta
from typing import Optional, Union
from uuid import UUID, uuid4

from .domain.models import Character, StoryElement, StoryMetadata, Relationship, Pronouns
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
        self._current_stage = set()
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
    def current_time(self):
        return self._current_time

    def set_time(self, time: datetime):
        self._current_time = time

    def get_formatted_time(self, format_string: str) -> str:
        return self._current_time.strftime(format_string)
        
    def set_location(self, location: str):
        self._current_location = location
        self._metadata.last_modified = datetime.now(timezone.utc)
        self._repo.save_metadata(self._metadata)

    def enter_character(
        self,
        character: Union[str, UUID, Character, None] = None
    ) -> None:
        """
        Add a character to the current stage.

        Args:
            character (Union[str, UUID, Character, None], optional):
                The character, character ID (string or UUID) to add to the stage.
                Defaults to None.

        Raises:
            ValueError: If no valid character identifier is provided.
        """
        if character is None:
            raise ValueError("A character or character ID must be provided.")

        character_id = character.id if isinstance(character, Character) else character

        if not isinstance(character_id, (str, UUID)):
            raise TypeError("Character identifier must be a string or UUID.")

        self._current_stage.add(character_id)
    
    def exit_character(
        self,
        character: Union[str, UUID, Character, None] = None
    ) -> None:
        """
        Remove a character from the current stage.

        Args:
            character (Union[str, UUID, Character, None], optional):
                The character, character ID (string or UUID) to remove from the stage.
                Defaults to None.

        Raises:
            ValueError: If no valid character identifier is provided.
            KeyError: If the character is not currently on the stage.
        """
        if character is None:
            raise ValueError("A character or character ID must be provided.")

        character_id = character.id if isinstance(character, Character) else character

        if not isinstance(character_id, (str, UUID)):
            raise TypeError("Character identifier must be a string or UUID.")

        try:
            self._current_stage.remove(character_id)
        except KeyError:
            raise KeyError(f"Character {character_id} is not currently on the stage.")

    def advance_time(self, delta: timedelta):
        if self._current_time is None:
            raise UninitializedStoryError(
                "Cannot advance time before setting initial time."
            )
        self._current_time += delta
        self._metadata.last_modified = datetime.now(timezone.utc)
        self._repo.save_metadata(self._metadata)

    def add_element(self, content: str) -> StoryElement:
        if self._current_time is None:
            raise UninitializedStoryError(
                "Cannot add element before setting initial time."
            )
        if self._current_location is None:
            raise UninitializedLocationError(
                "Cannot add element before setting a location."
            )

        element = StoryElement(
            id=uuid4(),
            time=self._current_time,
            location=self._current_location,
            content=content,
            chapter=self._current_chapter,
            characters=frozenset(self._current_stage),
        )
        self._repo.save_element(element)
        self._metadata.last_modified = datetime.now(timezone.utc)
        self._repo.save_metadata(self._metadata)
        return element

    def create_character(
        self,
        character_id: Union[str, UUID, None] = None,
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

    def get_character(self, character_id: Union[str, UUID]) -> Character:
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

        elements = self._repo.get_elements(chapter=self.current_chapter)

        # Group elements by location
        location_elements = {}
        for element in elements:
            if element.location not in location_elements:
                location_elements[element.location] = []
            location_elements[element.location].append(element)

        # Add location headers and element content
        for location, elements in location_elements.items():
            manuscript += f"## {location}\n"
            for element in elements:
                # Format the time for narrative
                manuscript += f"[{element.time}] {element.content}\n"

        return manuscript

    def clear_chapter(self, chapter: int):
        self._repo.clear_from_chapter_onwards(chapter)
        self._metadata.last_modified = datetime.now(timezone.utc)
        self._repo.save_metadata(self._metadata)

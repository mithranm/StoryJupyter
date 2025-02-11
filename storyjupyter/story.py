from pathlib import Path
from typing import Sequence, Any, Optional
from datetime import datetime
import uuid

from .core.types import TimeSpec, Duration, EventMetadata
from .core.models import Character, Brand, TimelineEvent
from .persistence.repositories import TimelineRepository, CharacterRepository
from .services.brand import DeterministicBrandManager
from .services.timeline import StoryTimelineManager
from .services.markdown import MarkdownGenerator
from .core.protocols import CharacterGenerator
from .services.character import FakerCharacterGenerator, LLMCharacterGenerator

from typing import Dict


class StoryManager:
    """Main interface for story management"""

    def __init__(
        self,
        db_name: str = "storydb",
        chapter: int = 1,
        character_generator=None,
        autosave_characters: bool = True,
        autosave_timeline: bool = True,
    ):
        """Initialize the StoryContext."""
        self._db_name = db_name
        self._chapter = chapter
        self.character_generator = character_generator or FakerCharacterGenerator()

        self.timeline = StoryTimelineManager(repository=TimelineRepository(db_name=db_name))
        self.character_repo = CharacterRepository(db_name=db_name)

        self.autosave_characters = autosave_characters
        self.autosave_timeline = autosave_timeline

        self._time = None
        self._location = None
        self._characters: Dict[str, Character] = {}  # Initialize the character dictionary
        self._characters.clear()  # Clear the character cache on initialization
        self._cell_output = []  # Initialize the cell output list
        
        self.character_repo.delete_characters_from_chapter_onwards(chapter=chapter)
        self.timeline.clear_from_chapter_onwards(chapter=chapter)

    def _load_existing_characters(self):
        """Load existing characters from the database"""
        characters = self.character_repo.get_all_characters()
        for character in characters:
            self._characters[str(character.character_id)] = character

    # Timeline delegation methods
    def set_time(self, time: TimeSpec) -> None:
        """Wrapper for timeline set_time method"""
        self.timeline.set_time(time)

    def advance_time(self, duration: Duration) -> None:
        """Advance story time by duration"""
        self.timeline.advance_time(duration)

    def get_time(self) -> datetime:
        """Get current story time"""
        return self.timeline.get_current_time()

    def set_location(self, location: str) -> None:
        """Set current story location"""
        self.timeline.set_location(location)

    def print(self, content: str, metadata: Optional[EventMetadata] = None) -> None:
        """Add content to cell output and timeline"""
        self._cell_output.append(content)
        event_id = str(uuid.uuid4())
        self.timeline.add_event(content, event_id=event_id, metadata=metadata, chapter=self._chapter)

    def get_cell_output(self) -> str:
        """Get and clear captured output"""
        output = "".join(self._cell_output)
        self._cell_output.clear()
        return output

    def export_reference(self) -> dict[str, Sequence[Brand | Character]]:
        """Export brand and character references"""
        return {
            "brands": list(self.brands._brands.values()),
            "characters": list(self._characters.values())
        }

    def get_analytics(self) -> dict[str, Any]:
        """Get story analytics"""
        events = self.timeline.get_events()
        return {
            "event_count": len(events),
            "character_count": len(self._characters),
            "current_chapter": self._chapter
        }

    def get_location(self) -> str:
        """Get current story location"""
        return self.timeline.get_current_location()

    def generate_manuscript(self, chapters: Optional[Sequence[int]] = None) -> str:
        """Generate manuscript for specified chapters or all chapters"""
        manuscript = ""
        events = self.timeline.get_events()
        chapter = 0
        for event in events:
            if event.chapter > chapter:
                chapter = event.chapter
                manuscript += f"# Chapter {chapter}\n\n"
            manuscript += event.content + "\n\n"
        return manuscript

    def _clear_future_chapters(self, chapter: int) -> None:
        """Clear data from future chapters when rewriting a chapter"""
        self.timeline.clear_chapter(chapter=chapter)
        self.character_repo.delete_characters_from_chapter_onwards(chapter=chapter)

    def create_character(
        self,
        character_id: str = None,
        save_character: bool = True,
        **attributes
    ) -> Character:
        """Create a new character using the character generator."""

        if character_id is None:
            character_id = str(uuid.uuid4())

        # Check if the character ID already exists in the database
        existing_character = self.character_repo.get_character(character_id)
        if existing_character:
            raise ValueError(f"Character ID '{character_id}' already exists in the database. Cannot create character.")
        elif str(character_id) in self._characters:
            raise ValueError(f"Character ID '{character_id}' already exists in memory.  Cannot create character.")

        character = self.character_generator.generate(
            character_id = character_id,
            **attributes
        )

        character.chapter_introduced = self._chapter # Track chapter introduced

        should_save = self.autosave_characters if save_character is True else save_character
        if should_save:  # Conditionally save character
            self.character_repo.save_character(character)
            self._characters[str(character.character_id)] = character #Cache after saving
        return character

    def get_character(self, id: str) -> Character:
        """Get existing character from memory or database"""
        try:
            return self._characters[id]
        except KeyError:
            try:
                # Attempt to fetch the character from the repository using the ID
                character = self.character_repo.get_character(id)
                self._characters[id] = character  # Cache the character
                return character
            except KeyError:
                # Character not found in memory or database
                raise KeyError(f"Character with ID '{id}' not found.")

    def get_character_at_time(self, character_id: str, timestamp: datetime) -> Character:
        """Get character version at a specific timestamp"""
        #TODO: Figure out what this is even supposed to behave like
        pass

    def __contains__(self, name: str) -> bool:
        """Check if character exists"""
        try:
            self.get_character(name)
            return True
        except KeyError:
            return False

    def validate_timeline(self, chapter: int) -> list[str]:
        """Validate the timeline within a chapter."""
        errors = []
        events = self.timeline.get_events(chapter=chapter)
        if not events:
            return errors  # No events to validate

        for i in range(1, len(events)):
            if events[i].timestamp < events[i - 1].timestamp:
                errors.append(
                    f"Chapter {chapter}: Event '{events[i].content}' occurs before previous event '{events[i - 1].content}'"
                )
        return errors
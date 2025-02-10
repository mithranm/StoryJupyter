from pathlib import Path
import sqlite3
from typing import Sequence, Any, Optional
from datetime import datetime

from .core.types import TimeSpec, Duration, EventMetadata
from .core.models import Character, Brand, TimelineEvent
from .persistence.repositories import TimelineRepository, CharacterRepository
from .services.brand import DeterministicBrandManager
from .services.timeline import StoryTimelineManager
from .services.markdown import MarkdownGenerator

class StoryContext:
    """Main interface for story management"""

    def __init__(
        self,
        db_path: str | Path,
        seed: Optional[int] = None,
        chapter: Optional[int] = None
    ) -> None:
        """
        Initialize story context with database connection

        Args:
            db_path: Path to SQLite database
            seed: Random seed for brand name generation
            chapter: Current chapter number (for versioning)
        """
        # Setup database connection
        self.db_path = str(db_path)  # Store db_path
        self.conn = sqlite3.connect(self.db_path)

        # Set current chapter
        self.current_chapter = chapter

        # Initialize repositories with chapter context
        self.timeline_repo = TimelineRepository(self.conn, chapter)
        self.character_repo = CharacterRepository(self.conn, chapter)

        # Initialize services
        self.brands = DeterministicBrandManager(seed=seed)
        self.timeline = StoryTimelineManager(self.timeline_repo)
        self.markdown = MarkdownGenerator(self.timeline)

        # Character management
        self._characters: dict[str, Character] = {}
        self._load_existing_characters()  # Load existing characters

        # Capture output
        self._cell_output: list[str] = []

    def _load_existing_characters(self):
        """Load existing characters from the database"""
        characters = self.character_repo.get_all_characters()
        for character in characters:
            self._characters[character.name] = character

    def __enter__(self):
        # Clear existing events for the chapter
        self.timeline.clear_chapter(self.current_chapter)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()

    # Timeline delegation methods
    def set_time(self, time: TimeSpec) -> None:
        """Set current story time"""
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
        self.timeline.add_event(content, metadata=metadata, chapter=self.current_chapter)

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
            "brand_count": len(self.brands._brands),
            "current_chapter": self.current_chapter
        }

    def get_location(self) -> str:
        """Get current story location"""
        return self.timeline.get_current_location()

    def generate_manuscript(self, chapters: Optional[Sequence[int]] = None) -> str:
        """Generate manuscript for specified chapters or all chapters"""
        if chapters is None:
            # Get all chapters from timeline events
            events = self.timeline.get_events()
            chapters = sorted(set(event.chapter for event in events))

        manuscript = ""
        for chapter in chapters:
            manuscript += f"# Chapter {chapter}\n\n"
            events = self.timeline.get_events(chapter=chapter)
            location = None
            for event in events:
                if event.location != location:
                    location = event.location
                    manuscript += f"## {location}\n\n"
                manuscript += event.content + "\n\n"
        return manuscript

    def _clear_future_chapters(self, chapter: int) -> None:
        """Clear data from future chapters when rewriting a chapter"""
        # Clear timeline events
        self.conn.execute(
            """
        DELETE FROM timeline_events 
        WHERE chapter > ?
        """,
            (chapter,),
        )

        # Clear character changes
        self.conn.execute(
            """
        DELETE FROM character_versions 
        WHERE chapter > ?
        """,
            (chapter,),
        )

        self.conn.commit()

class CharacterManager:
    """Manages character creation and retrieval"""

    def __init__(self, context: StoryContext):
        self._context = context

    def create(
        self,
        name: str,
        description: str = "",  # Add default description
        pronoun_set: str = "they",  # Add default pronoun_set
        **attributes
    ) -> Character:
        """Create a new character, or retrieve if it exists."""
        try:
            character = self.get(name)
            # Update attributes if character exists
            updated_attributes = character.attributes.copy()
            updated_attributes.update(attributes)
            character = Character.create(
                name=name,
                description=description or character.description, #Use existing if not provided
                pronoun_set=pronoun_set or character.pronouns.pronoun_set, #Use existing if not provided
                attributes=updated_attributes
            )
            self._context._characters[name] = character
            self._context.character_repo.save_character(character)
            return character
        except KeyError:
            # Character doesn't exist, create it
            character = Character.create(
                name=name,
                description=description,
                pronoun_set=pronoun_set,
                attributes=attributes
            )
            self._context._characters[name] = character
            self._context.character_repo.save_character(character)
            return character

    def get(self, name: str) -> Character:
        """Get existing character at current chapter version"""
        if name in self._context._characters:
            return self._context._characters[name]

        character = self._context.character_repo.get_character(
            name,
            chapter=self._context.current_chapter
        )
        self._context._characters[name] = character
        return character

    def __contains__(self, name: str) -> bool:
        """Check if character exists"""
        try:
            self.get(name)
            return True
        except KeyError:
            return False
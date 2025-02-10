# storyjupyter/persistence/repositories.py
from datetime import datetime, UTC
import json
from sqlite3 import Connection
from typing import Sequence, Optional
from .schema import TimelineSchema, CharacterSchema
from ..core.types import TimeSpec
from ..core.models import TimelineEvent, Character

class TimelineRepository:
    """SQLite repository for timeline events with chapter versioning"""
    
    def __init__(self, conn: Connection, chapter: Optional[int] = None) -> None:
        """Initialize repository with connection and optional chapter context"""
        self.conn = conn
        self.chapter = chapter
        
        # Initialize schema immediately
        self._init_schema()
    
    def _init_schema(self) -> None:
        """Initialize database schema"""
        TimelineSchema().initialize(self.conn)
        self.conn.commit()  # Make sure schema changes are committed
    
    def delete_events(self, chapter: int) -> None:
        """Delete all events for a specific chapter"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM timeline_events WHERE chapter = ?", (chapter,))
        self.conn.commit()

    def get_current_time(self) -> Optional[datetime]:
        """Get the current time from the database"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT timestamp FROM current_time WHERE id = 1")
        row = cursor.fetchone()
        if row:
            return datetime.fromisoformat(row[0])
        return None
    
    def save_time(self, time: datetime) -> None:
        """Save the current time to the database"""
        cursor = self.conn.cursor()

        # Insert or replace the current time
        cursor.execute("""
        INSERT OR REPLACE INTO current_time (id, timestamp)
        VALUES (1, ?)
        """, (time.isoformat(),))

        self.conn.commit()
    
    def save_event(self, event: TimelineEvent, chapter: Optional[int] = None) -> int:
        """Save event and return its ID"""
        chapter = chapter or self.chapter
        if chapter is None:
            raise ValueError("Chapter must be specified")
            
        cursor = self.conn.cursor()
        
        # Insert main event with chapter
        cursor.execute("""
        INSERT INTO timeline_events (chapter, timestamp, location, content)
        VALUES (?, ?, ?, ?)
        """, (chapter, event.timestamp.isoformat(), event.location, event.content))
        
        event_id = cursor.lastrowid
        assert event_id is not None
        
        # Insert metadata
        for key, value in event.metadata.items():
            if key != "tags":  # Tags handled separately
                cursor.execute("""
                INSERT INTO event_metadata (event_id, key, value)
                VALUES (?, ?, ?)
                """, (event_id, key, json.dumps(value)))
        
        # Insert tags
        for tag in event.metadata.get("tags", []):
            cursor.execute("""
            INSERT INTO event_tags (event_id, tag)
            VALUES (?, ?)
            """, (event_id, tag))
        
        self.conn.commit()
        return event_id
    
    def get_events(
        self,
        *,
        start: Optional[TimeSpec] = None,
        end: Optional[TimeSpec] = None,
        tags: Optional[Sequence[str]] = None,
        location: Optional[str] = None,
        chapter: Optional[int] = None
    ) -> Sequence[TimelineEvent]:
        """Get events matching criteria"""
        query = ["SELECT e.* FROM timeline_events e"]
        params: list[any] = []
        
        if tags:
            query.append("""
            INNER JOIN event_tags t ON e.id = t.event_id
            WHERE t.tag IN ({})
            """.format(",".join("?" * len(tags))))
            params.extend(tags)
        else:
            query.append("WHERE 1=1")
        
        # Add chapter filter if specified
        chapter = chapter or self.chapter
        if chapter is not None:
            query.append("AND e.chapter = ?")
            params.append(chapter)
        
        if start:
            if isinstance(start, str):
                start_dt = datetime.fromisoformat(start)
            else:
                start_dt = start
            if not start_dt.tzinfo:
                start_dt = start_dt.replace(tzinfo=UTC)
            query.append("AND e.timestamp >= ?")
            params.append(start_dt.isoformat())
        
        if end:
            if isinstance(end, str):
                end_dt = datetime.fromisoformat(end)
            else:
                end_dt = end
            if not end_dt.tzinfo:
                end_dt = end_dt.replace(tzinfo=UTC)
            query.append("AND e.timestamp <= ?")
            params.append(end_dt.isoformat())
        
        if location:
            query.append("AND e.location = ?")
            params.append(location)
        
        query.append("ORDER BY e.timestamp")
        
        cursor = self.conn.cursor()
        cursor.execute(" ".join(query), params)
        rows = cursor.fetchall()
        
        events = []
        for row in rows:
            # Get metadata
            cursor.execute("""
            SELECT key, value FROM event_metadata
            WHERE event_id = ?
            """, (row[0],))
            metadata = {
                key: json.loads(value)
                for key, value in cursor.fetchall()
            }
            
            # Get tags
            cursor.execute("""
            SELECT tag FROM event_tags
            WHERE event_id = ?
            """, (row[0],))
            metadata["tags"] = [tag[0] for tag in cursor.fetchall()]
            
            events.append(TimelineEvent(
                timestamp=datetime.fromisoformat(row[2]),  # Adjusted for chapter column
                location=row[3],
                content=row[4],
                metadata=metadata,
                chapter=row[1] # Add chapter to TimelineEvent
            ))
        
        return events
    
class CharacterRepository:
    def __init__(self, conn: Connection, chapter: Optional[int] = None) -> None:
        self.conn = conn
        self.chapter = chapter
        CharacterSchema().initialize(conn)

    def save_character(self, character: Character) -> int:
        """Save character to the database"""
        cursor = self.conn.cursor()

        # Insert the new character, replacing if it already exists
        cursor.execute("""
        INSERT OR REPLACE INTO characters (name, description, pronoun_set)
        VALUES (?, ?, ?)
        """, (character.name, character.description, character.pronouns.pronoun_set))

        character_id = cursor.lastrowid
        assert character_id is not None

        # Insert chapter version if specified
        cursor.execute("""
        INSERT OR REPLACE INTO character_versions (character_id, chapter, description, pronoun_set)
        VALUES (?, ?, ?, ?)
        """, (character_id, self.chapter or 1, character.description, character.pronouns.pronoun_set))

        # Insert attributes with chapter versioning
        for key, value in character.attributes.items():
            cursor.execute("""
            INSERT OR REPLACE INTO character_attributes (character_id, chapter, key, value)
            VALUES (?, ?, ?, ?)
            """, (character_id, self.chapter or 1, key, json.dumps(value)))

        self.conn.commit()
        return character_id

    def get_character(self, name: str, chapter: Optional[int] = None) -> Character:
        chapter = chapter or self.chapter
        if chapter is None:
            raise ValueError("Chapter must be specified")

        cursor = self.conn.cursor()

        # Get character version
        cursor.execute("""
        SELECT description, pronoun_set FROM character_versions
        WHERE character_id = (SELECT id FROM characters WHERE name = ?)
        AND chapter = ?
        """, (name, chapter))

        row = cursor.fetchone()
        if not row:
            raise KeyError(f"Character not found: {name} in chapter {chapter}")

        # Get attributes
        cursor.execute("""
        SELECT key, value FROM character_attributes
        WHERE character_id = (SELECT id FROM characters WHERE name = ?)
        AND chapter = ?
        """, (name, chapter))

        attributes = {
            key: json.loads(value)
            for key, value in cursor.fetchall()
        }

        # Get base character info
        cursor.execute("""
        SELECT name FROM characters
        WHERE name = ?
        """, (name,))
        base_row = cursor.fetchone()
        if not base_row:
            raise KeyError(f"Base character not found: {name}")

        return Character.create(
            name=base_row[0],
            description=row[0],
            pronoun_set=row[1],
            **attributes
        )

    def get_all_characters(self) -> list[Character]:
        """Get all characters from the database"""
        cursor = self.conn.cursor()
        cursor.execute("""
        SELECT name, description, pronoun_set FROM characters
        """)
        rows = cursor.fetchall()
        characters = []
        for row in rows:
            name, description, pronoun_set = row
            try:
                character = self.get_character(name, chapter=self.chapter)
                characters.append(character)
            except KeyError:
                # Character version not found for the current chapter, create a base character
                character = Character.create(
                    name=name,
                    description=description,
                    pronoun_set=pronoun_set
                )
                characters.append(character)
        return characters
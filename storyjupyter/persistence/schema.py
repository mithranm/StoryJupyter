# storyjupyter/persistence/schema.py
from sqlite3 import Connection
from typing import Protocol

class DBSchema(Protocol):
    """Protocol for database schema management"""
    def initialize(self, conn: Connection) -> None: ...

class TimelineSchema(DBSchema):
    """Timeline database schema"""
    
    def initialize(self, conn: Connection) -> None:
        """Initialize timeline tables"""
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS timeline_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chapter INTEGER NOT NULL DEFAULT 1,
            timestamp TEXT NOT NULL,
            location TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS event_metadata (
            event_id INTEGER NOT NULL,
            key TEXT NOT NULL,
            value TEXT NOT NULL,
            FOREIGN KEY (event_id) REFERENCES timeline_events(id),
            PRIMARY KEY (event_id, key)
        );
        
        CREATE TABLE IF NOT EXISTS event_tags (
            event_id INTEGER NOT NULL,
            tag TEXT NOT NULL,
            FOREIGN KEY (event_id) REFERENCES timeline_events(id),
            PRIMARY KEY (event_id, tag)
        );

        CREATE TABLE IF NOT EXISTS current_time (
            id INTEGER PRIMARY KEY,
            timestamp TEXT NOT NULL
        );
        """)

class CharacterSchema(DBSchema):
    """Character database schema with versioning"""
    
    def initialize(self, conn: Connection) -> None:
        """Initialize character tables"""
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS characters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT NOT NULL,
            pronoun_set TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_characters_name ON characters (name);

        CREATE TABLE IF NOT EXISTS character_versions (
            character_id INTEGER NOT NULL,
            chapter INTEGER NOT NULL DEFAULT 1,
            description TEXT NOT NULL,
            pronoun_set TEXT NOT NULL,
            modified_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (character_id) REFERENCES characters(id),
            PRIMARY KEY (character_id, chapter)
        );
        CREATE INDEX IF NOT EXISTS idx_character_versions_character_id ON character_versions (character_id);

        CREATE TABLE IF NOT EXISTS character_attributes (
            character_id INTEGER NOT NULL,
            chapter INTEGER NOT NULL DEFAULT 1,
            key TEXT NOT NULL,
            value TEXT NOT NULL,
            FOREIGN KEY (character_id) REFERENCES characters(id),
            PRIMARY KEY (character_id, chapter, key)
        );
        CREATE INDEX IF NOT EXISTS idx_character_attributes_character_id ON character_attributes (character_id);
        """)
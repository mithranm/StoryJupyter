# src/storyjupyter/persistence/mongodb.py
from typing import Optional, Sequence
from datetime import datetime
from uuid import UUID
import pymongo
from dataclasses import asdict

from ..domain.models import Character, StoryEvent, StoryMetadata
from ..domain.interfaces import StoryRepository
from ..domain.time import StoryTime


def _clean_mongo_data(data: dict) -> dict:
    """Remove MongoDB-specific fields and clean data for domain models"""
    if data is None:
        return {}
    return {k: v for k, v in data.items() if not k.startswith("_")}


def _serialize_uuid(obj: dict) -> dict:
    """Convert UUID objects to strings for MongoDB storage"""
    result = {}
    for k, v in obj.items():
        if isinstance(v, UUID):
            result[k] = str(v)
        elif isinstance(v, dict):
            result[k] = _serialize_uuid(v)
        elif isinstance(v, (list, set, frozenset)):
            result[k] = [str(x) if isinstance(x, UUID) else x for x in v]
        elif isinstance(v, datetime):
            result[k] = v  # MongoDB handles datetime natively
        else:
            result[k] = v
    return result


def _deserialize_uuid(obj: dict) -> dict:
    """Convert UUID strings back to UUID objects"""
    result = {}
    for k, v in obj.items():
        if isinstance(v, str) and k in {"id", "character_id"}:
            result[k] = UUID(v)
        elif isinstance(v, dict):
            result[k] = _deserialize_uuid(v)
        elif isinstance(v, list):
            result[k] = [
                UUID(x) if isinstance(x, str) and len(x) == 36 else x for x in v
            ]
        else:
            result[k] = v
    return result


class MongoDBStoryRepository(StoryRepository):
    """MongoDB implementation of story persistence"""

    def __init__(
        self,
        connection_string: str,
        database: str,
        metadata_collection: str = "metadata",
        character_collection: str = "characters",
        event_collection: str = "events",
    ):
        """Initialize MongoDB connection and collections"""
        self.client = pymongo.MongoClient(connection_string)
        self.db = self.client[database]
        self.metadata_collection = self.db[metadata_collection]
        self.character_collection = self.db[character_collection]
        self.event_collection = self.db[event_collection]

        # Create indexes
        self.character_collection.create_index("id", unique=True)
        self.event_collection.create_index("id", unique=True)
        self.event_collection.create_index(
            [("chapter", pymongo.ASCENDING), ("time", pymongo.ASCENDING)]
        )

    def save_metadata(self, metadata: StoryMetadata) -> None:
        """Save story metadata"""
        data = asdict(metadata)
        data = _serialize_uuid(data)
        self.metadata_collection.replace_one(
            {"title": metadata.title},  # Use title as unique identifier
            data,
            upsert=True,
        )

    def get_metadata(self) -> Optional[StoryMetadata]:
        """Retrieve story metadata"""
        data = self.metadata_collection.find_one()
        if data is None:
            return None

        data = _clean_mongo_data(data)
        data = _deserialize_uuid(data)

        # Ensure timezone-aware datetimes
        data["created_at"] = StoryTime.ensure_tz(data["created_at"])
        data["last_modified"] = StoryTime.ensure_tz(data["last_modified"])

        return StoryMetadata(**data)

    def save_character(self, character: Character) -> None:
        """Save character"""
        # Convert to dict and handle special types
        data = character.to_dict()
        data = _serialize_uuid(data)

        # Save to MongoDB
        self.character_collection.replace_one(
            {"id": str(character.id)}, data, upsert=True
        )

    def get_character(self, id: UUID) -> Optional[Character]:
        """Retrieve character by ID"""
        data = self.character_collection.find_one({"id": str(id)})
        if data is None:
            return None

        # Clean and deserialize
        data = _clean_mongo_data(data)
        data = _deserialize_uuid(data)

        return Character.from_dict(data)

    def get_characters(self, chapter: Optional[int] = None) -> Sequence[Character]:
        """Get all characters, optionally filtered by chapter introduced"""
        query = {}
        if chapter is not None:
            query["chapter_introduced"] = chapter

        characters = []
        for data in self.character_collection.find(query):
            data = _clean_mongo_data(data)
            data = _deserialize_uuid(data)
            characters.append(Character.from_dict(data))
        return characters

    def save_event(self, event: StoryEvent) -> None:
        """Save story event"""
        data = asdict(event)
        data = _serialize_uuid(data)

        self.event_collection.replace_one({"id": str(event.id)}, data, upsert=True)

    def get_events(
        self,
        *,
        chapter: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Sequence[StoryEvent]:
        """Get events with optional filters"""
        query = {}

        if chapter is not None:
            query["chapter"] = chapter

        if start_time is not None or end_time is not None:
            query["time"] = {}
            if start_time:
                query["time"]["$gte"] = StoryTime.ensure_tz(start_time)
            if end_time:
                query["time"]["$lte"] = StoryTime.ensure_tz(end_time)

        events = []
        for data in self.event_collection.find(query).sort(
            [("chapter", pymongo.ASCENDING), ("time", pymongo.ASCENDING)]
        ):
            # Clean and deserialize
            data = _clean_mongo_data(data)
            data = _deserialize_uuid(data)

            # Convert character IDs to frozenset
            if "characters" in data:
                data["characters"] = frozenset(
                    UUID(x) if isinstance(x, str) else x for x in data["characters"]
                )

            # Ensure timezone
            data["time"] = StoryTime.ensure_tz(data["time"])

            events.append(StoryEvent(**data))

        return events

    def clear_chapter(self, chapter: int) -> None:
        """Remove all events and characters from specified chapter"""
        # Remove events
        self.event_collection.delete_many({"chapter": chapter})

        # Remove characters introduced in this chapter
        self.character_collection.delete_many({"chapter_introduced": chapter})

    def clear_from_chapter_onwards(self, chapter: int) -> None:
        """Remove all events and characters from chapter onwards"""
        # Remove events
        self.event_collection.delete_many({"chapter": {"$gte": chapter}})

        # Remove characters introduced in this chapter or later
        self.character_collection.delete_many({"chapter_introduced": {"$gte": chapter}})

    def __del__(self):
        """Cleanup MongoDB connection"""
        try:
            self.client.close()
        except Exception as e:
            del e # Flake8 is making me do this I might have to reconfigure it
            pass

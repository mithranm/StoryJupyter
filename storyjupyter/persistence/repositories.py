import pymongo
from typing import List, Dict, Any, Optional
from ..core.models import TimelineEvent
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class TimelineRepository:
    def __init__(
        self,
        base_url="mongodb://localhost:27017/",
        db_name="storydb",
        collection_name="timelines",
        chapter_end_times_collection_name="chapter_end_times",
    ):
        self.client = pymongo.MongoClient(base_url)
        self.db = self.client[db_name]
        self.timeline_collection = self.db[collection_name]
        self.chapter_end_times_collection = self.db[
            chapter_end_times_collection_name
        ]

    def save_timeline_event(self, event: TimelineEvent) -> str:
        """Save a timeline event to MongoDB."""
        assert (
            event.chapter is not None
        ), "Chapter number must be set for timeline events"
        event_data = {
            "event_id": event.event_id,
            "timestamp": event.timestamp,
            "location": event.location,
            "content": event.content,
            "metadata": event.metadata,
            "chapter": event.chapter,
        }
        self.timeline_collection.update_one(
            {"event_id": event_data["event_id"]}, {"$set": event_data}, upsert=True
        )
        return event.event_id

    def get_timeline_event(self, event_id: str) -> TimelineEvent:
        """Retrieve a timeline event from MongoDB."""
        event_data = self.timeline_collection.find_one({"event_id": event_id})
        if event_data:
            event_data = {
                "event_id": event_data.event_id,
                "timestamp": event_data.timestamp,
                "location": event_data.location,
                "content": event_data.content,
                "metadata": event_data.metadata,
                "chapter": event_data.chapter,
            }
            return event_data
        return None

    def get_all_timeline_events(
        self, chapter: Optional[int] = None
    ) -> List[TimelineEvent]:
        """Retrieve all timeline events from MongoDB, optionally for a specific chapter."""
        query = {}
        if chapter is not None:
            query = {"chapter": chapter}

        events_data = list(self.timeline_collection.find(query))
        events = []
        for event_data in events_data:
            event = TimelineEvent(
                event_id=event_data["event_id"],
                timestamp=event_data["timestamp"],
                location=event_data["location"],
                content=event_data["content"],
                chapter=event_data["chapter"],
                metadata=event_data["metadata"],
            )
            events.append(event)
        return events

    def delete_timeline_event(self, event_id: str) -> None:
        """Delete a timeline event from MongoDB."""
        self.timeline_collection.delete_one({"event_id": event_id})

    def delete_events(self, chapter: int) -> None:
        """Delete all events for a specific chapter."""
        self.timeline_collection.delete_many({"chapter": chapter})


from typing import Optional
from ..core.models import Character, NameComponents
from ..core.pronouns import Pronouns
import uuid


class CharacterRepository:
    def __init__(
        self,
        base_url="mongodb://localhost:27017/",
        db_name="storydb",
        collection_name="characters",
    ):
        self.client = pymongo.MongoClient(base_url)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def save_character(self, character: Character) -> str:
        """Save character to MongoDB"""
        character_data = {
            "character_id": character.character_id,
            "name_components": {
                "first": character.name_components.first,
                "middle": character.name_components.middle,
                "last": character.name_components.last,
                "prefix": character.name_components.prefix,
                "suffix": character.name_components.suffix,
            },
            "pronoun_set": (
                character.pronouns.pronoun_set if character.pronouns else None
            ),
            "attributes": character.attributes,
            "relationships": character.relationships,
            "chapter_introduced": character.chapter_introduced,  # Save chapter introduced
        }
        result = self.collection.update_one(
            {"character_id": character_data["character_id"]},
            {"$set": character_data},
            upsert=True,
        )
        return character.character_id

    def get_character(self, character_id: str) -> Character:
        """Retrieve character from MongoDB"""
        character_data = self.collection.find_one({"character_id": character_id})
        if character_data:
            # Reconstruct the Character object from the dictionary
            name_components = character_data.get("name_components", {})
            pronoun_set = character_data.get("pronoun_set")

            character = Character(
                character_id=character_data["character_id"],
                name_components=NameComponents(
                    first=name_components.get("first"),
                    middle=name_components.get("middle", []),
                    last=name_components.get("last"),
                    prefix=name_components.get("prefix"),
                    suffix=name_components.get("suffix"),
                ),
                pronouns=Pronouns(pronoun_set) if pronoun_set else None,
                attributes=character_data.get("attributes", {}),
                relationships=character_data.get("relationships", {}),
                chapter_introduced=character_data.get(
                    "chapter_introduced"
                ),  # Load chapter introduced
            )
            return character
        return None

    def delete_character(self, character_id: str) -> None:
        """Delete character from MongoDB"""
        result = self.collection.delete_one({"character_id": character_id})
        if result.deleted_count == 0:
            logger.warning(
                f"Character with ID '{character_id}' not found for deletion."
            )

    def get_all_characters(self) -> list[Character]:
        """Get all characters from the database"""
        characters_data = list(self.collection.find())
        characters = []
        for character_data in characters_data:
            try:
                character = self.get_character(str(character_data["character_id"]))
                if character:
                    characters.append(character)
            except KeyError:
                print(f"Character not found: {character_data['character_id']}")
        return characters

    def delete_characters_from_chapter_onwards(self, chapter: int) -> None:
        """Delete characters introduced in the given chapter or later."""
        result = self.collection.delete_many({"chapter_introduced": {"$gte": chapter}})
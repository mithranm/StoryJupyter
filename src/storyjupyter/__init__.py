# src/storyjupyter/__init__.py
from .story import Story
from .builder import StoryBuilder, create_story
from .domain import (
    Character,
    StoryElement,
    StoryMetadata,
    Pronouns,
    CharacterGenerator,
    StoryRepository,
)
from .persistence import MongoDBStoryRepository
from .generation import FakerCharacterGenerator, LLMCharacterGenerator

__version__ = "0.1.0"

__all__ = [
    "Story",
    "StoryBuilder",
    "create_story",
    "Character",
    "StoryElement",
    "StoryMetadata",
    "Pronouns",
    "CharacterGenerator",
    "StoryRepository",
    "MongoDBStoryRepository",
    "FakerCharacterGenerator",
    "LLMCharacterGenerator",
]

# src/storyjupyter/persistence/__init__.py
from .mongodb import MongoDBStoryRepository
from .dummy import DummyStoryRepository

__all__ = ["MongoDBStoryRepository", "DummyStoryRepository"]

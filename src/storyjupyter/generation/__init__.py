# src/storyjupyter/generation/__init__.py
from .faker import FakerCharacterGenerator
from .llm import LLMCharacterGenerator

__all__ = ["FakerCharacterGenerator", "LLMCharacterGenerator"]

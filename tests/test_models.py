# tests/test_models.py
import pytest
from datetime import datetime, timezone
from uuid import uuid4

from storyjupyter.domain.models import (
    Character,
    StoryEvent,
    StoryMetadata,
    Pronouns,
    Relationship,
)


def test_pronouns():
    """Test pronoun handling"""
    # Test creation from subject
    he = Pronouns.from_subject("he")
    assert he.subject == "he"
    assert he.object == "him"
    assert he.possessive == "his"
    assert he.possessive_pronoun == "his"
    assert he.reflexive == "himself"

    she = Pronouns.from_subject("she")
    assert she.subject == "she"
    assert she.object == "her"
    assert she.possessive == "her"
    assert she.possessive_pronoun == "hers"
    assert she.reflexive == "herself"

    they = Pronouns.from_subject("they")
    assert they.subject == "they"
    assert they.object == "them"
    assert they.possessive == "their"
    assert they.possessive_pronoun == "theirs"
    assert they.reflexive == "themselves"

    # Test invalid pronoun
    with pytest.raises(ValueError):
        Pronouns.from_subject("invalid")


def test_character():
    """Test character model"""
    # Basic character creation
    char = Character(
        id=uuid4(),
        first_name="John",
        last_name="Doe",
        pronouns=Pronouns.from_subject("he"),
    )
    assert char.name == "John Doe"

    # Character with middle names
    char_with_middle = Character(
        id=uuid4(), first_name="John", middle_names=["Robert", "James"], last_name="Doe"
    )
    assert char_with_middle.name == "John Robert James Doe"

    # Character with attributes
    char_with_attrs = Character(
        id=uuid4(),
        first_name="John",
        last_name="Doe",
        attributes={"age": 30, "occupation": "Engineer"},
    )
    assert char_with_attrs.attributes["age"] == 30
    assert char_with_attrs.attributes["occupation"] == "Engineer"


def test_character_relationships():
    """Test character relationships"""
    alice = Character(id=uuid4(), first_name="Alice")
    bob = Character(id=uuid4(), first_name="Bob")

    # Add relationship
    relationship = Relationship(type="sibling", description="Twin siblings")
    alice.relationships[bob.id] = relationship

    assert bob.id in alice.relationships
    assert alice.relationships[bob.id].type == "sibling"
    assert alice.relationships[bob.id].description == "Twin siblings"


def test_story_event():
    """Test story event model"""
    # Basic event creation
    time = datetime.now(timezone.utc)
    event = StoryEvent(
        id=uuid4(),
        time=time,
        location="Test Location",
        content="Test content",
        chapter=1,
    )

    assert event.time.tzinfo is not None  # Ensure timezone-aware
    assert event.location == "Test Location"
    assert event.content == "Test content"
    assert event.chapter == 1

    # Event with character references
    char_id = uuid4()
    event_with_chars = StoryEvent(
        id=uuid4(),
        time=time,
        location="Test Location",
        content="Test content",
        chapter=1,
        characters=frozenset([char_id]),
    )

    assert char_id in event_with_chars.characters
    assert len(event_with_chars.characters) == 1


def test_story_metadata():
    """Test story metadata model"""
    # Create metadata
    created = datetime.now(timezone.utc)
    metadata = StoryMetadata(
        title="Test Story", author="Test Author", created_at=created
    )

    assert metadata.title == "Test Story"
    assert metadata.author == "Test Author"
    assert metadata.created_at == pytest.approx(created)
    assert metadata.last_modified >= created

    original_modified = metadata.last_modified
    import time

    time.sleep(0.001)  # Add a small delay
    metadata.update_modified()
    assert metadata.last_modified > original_modified

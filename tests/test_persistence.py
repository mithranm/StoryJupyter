# tests/test_persistence.py
import pytest
from datetime import datetime, timezone
from uuid import uuid4

from storyjupyter.domain.models import Character, StoryEvent, StoryMetadata, Pronouns
from storyjupyter.persistence.mongodb import MongoDBStoryRepository


@pytest.fixture
def mongo_repo():
    """Create a test repository using a temporary database"""
    # Use a unique database name for isolation
    db_name = f"test_db_{uuid4().hex}"
    repo = MongoDBStoryRepository(
        connection_string="mongodb://localhost:27017", database=db_name
    )

    yield repo

    # Cleanup: drop the test database
    repo.client.drop_database(db_name)
    repo.client.close()


def test_save_and_retrieve_metadata(mongo_repo):
    """Test saving and retrieving story metadata"""
    metadata = StoryMetadata(
        title="Test Story", author="Test Author", created_at=datetime.now(timezone.utc)
    )

    mongo_repo.save_metadata(metadata)
    retrieved = mongo_repo.get_metadata()

    assert retrieved.title == metadata.title
    assert retrieved.author == metadata.author
    assert retrieved.created_at.timestamp() == pytest.approx(
        metadata.created_at.timestamp()
    )


def test_save_and_retrieve_character(mongo_repo):
    """Test saving and retrieving characters"""
    char_id = uuid4()
    character = Character(
        id=char_id,
        first_name="John",
        last_name="Doe",
        pronouns=Pronouns.from_subject("he"),
        chapter_introduced=1,
    )

    mongo_repo.save_character(character)
    retrieved = mongo_repo.get_character(char_id)

    assert retrieved.id == character.id
    assert retrieved.first_name == character.first_name
    assert retrieved.last_name == character.last_name
    assert retrieved.pronouns.subject == character.pronouns.subject
    assert retrieved.chapter_introduced == character.chapter_introduced


def test_get_characters_by_chapter(mongo_repo):
    """Test retrieving characters filtered by chapter"""
    # Create characters in different chapters
    char1 = Character(id=uuid4(), first_name="Alice", chapter_introduced=1)
    char2 = Character(id=uuid4(), first_name="Bob", chapter_introduced=1)
    char3 = Character(id=uuid4(), first_name="Charlie", chapter_introduced=2)

    for char in [char1, char2, char3]:
        mongo_repo.save_character(char)

    # Test filtering
    chapter1_chars = mongo_repo.get_characters(chapter=1)
    assert len(chapter1_chars) == 2
    assert {c.first_name for c in chapter1_chars} == {"Alice", "Bob"}

    chapter2_chars = mongo_repo.get_characters(chapter=2)
    assert len(chapter2_chars) == 1
    assert chapter2_chars[0].first_name == "Charlie"


def test_save_and_retrieve_events(mongo_repo):
    """Test saving and retrieving events"""
    event_time = datetime.now(timezone.utc)
    event = StoryEvent(
        id=uuid4(),
        time=event_time,
        location="Test Location",
        content="Test content",
        chapter=1,
    )

    mongo_repo.save_event(event)
    retrieved = mongo_repo.get_events(chapter=1)

    assert len(retrieved) == 1
    assert retrieved[0].id == event.id
    assert retrieved[0].content == event.content
    assert retrieved[0].time.timestamp() == pytest.approx(event_time.timestamp())


def test_clear_chapter(mongo_repo):
    """Test clearing chapter data"""
    # Create test data
    char1 = Character(id=uuid4(), first_name="Alice", chapter_introduced=1)
    char2 = Character(id=uuid4(), first_name="Bob", chapter_introduced=2)
    mongo_repo.save_character(char1)
    mongo_repo.save_character(char2)

    event1 = StoryEvent(
        id=uuid4(),
        time=datetime.now(timezone.utc),
        location="Test",
        content="Chapter 1 event",
        chapter=1,
    )
    event2 = StoryEvent(
        id=uuid4(),
        time=datetime.now(timezone.utc),
        location="Test",
        content="Chapter 2 event",
        chapter=2,
    )
    mongo_repo.save_event(event1)
    mongo_repo.save_event(event2)

    # Clear chapter 1
    mongo_repo.clear_chapter(1)

    # Verify chapter 1 data is gone but chapter 2 remains
    assert len(mongo_repo.get_characters(chapter=1)) == 0
    assert len(mongo_repo.get_characters(chapter=2)) == 1
    assert len(mongo_repo.get_events(chapter=1)) == 0
    assert len(mongo_repo.get_events(chapter=2)) == 1


def test_clear_from_chapter_onwards(mongo_repo):
    """Test clearing chapter data from a specific chapter onwards"""
    # Create test data across three chapters
    characters = []
    events = []

    for chapter in [1, 2, 3]:
        char = Character(
            id=uuid4(), first_name=f"Character{chapter}", chapter_introduced=chapter
        )
        characters.append(char)
        mongo_repo.save_character(char)

        event = StoryEvent(
            id=uuid4(),
            time=datetime.now(timezone.utc),
            location="Test",
            content=f"Chapter {chapter} event",
            chapter=chapter,
        )
        events.append(event)
        mongo_repo.save_event(event)

    # Clear from chapter 2 onwards
    mongo_repo.clear_from_chapter_onwards(2)

    # Verify only chapter 1 data remains
    all_characters = mongo_repo.get_characters()
    assert len(all_characters) == 1
    assert all_characters[0].chapter_introduced == 1

    all_events = mongo_repo.get_events()
    assert len(all_events) == 1
    assert all_events[0].chapter == 1

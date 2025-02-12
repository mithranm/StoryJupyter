# tests/test_persistence.py
import pytest
import os
from datetime import datetime, timezone
from uuid import uuid4

from storyjupyter.domain.models import Character, StoryElement, StoryMetadata, Pronouns
from storyjupyter.persistence import MongoDBStoryRepository, DummyStoryRepository

@pytest.fixture(scope="session")
def use_mongodb():
    """Determine whether to use MongoDB based on an environment variable."""
    return os.getenv("TEST_WITH_MONGODB", "False").lower() == "true"

@pytest.fixture
def story_repo(use_mongodb):
    """Create a test repository, either MongoDB or Dummy."""
    if use_mongodb:
        db_name = f"test_db_{uuid4().hex}"
        repo = MongoDBStoryRepository(
            connection_string="mongodb://localhost:27017", database=db_name
        )
        yield repo
        # Cleanup: drop the test database
        repo.client.drop_database(db_name)
        repo.client.close()
    else:
        repo = DummyStoryRepository()
        yield repo

def test_save_and_retrieve_metadata(story_repo):
    """Test saving and retrieving story metadata"""
    metadata = StoryMetadata(
        title="Test Story", author="Test Author", created_at=datetime.now(timezone.utc)
    )

    story_repo.save_metadata(metadata)
    retrieved = story_repo.get_metadata()

    assert retrieved.title == metadata.title
    assert retrieved.author == metadata.author
    assert retrieved.created_at.timestamp() == pytest.approx(
        metadata.created_at.timestamp()
    )


def test_save_and_retrieve_character(story_repo):
    """Test saving and retrieving characters"""
    char_id = uuid4()
    character = Character(
        id=char_id,
        first_name="John",
        last_name="Doe",
        pronouns=Pronouns.from_subject("he"),
        chapter_introduced=1,
    )

    story_repo.save_character(character)
    retrieved = story_repo.get_character(char_id)

    assert retrieved.id == character.id
    assert retrieved.first_name == character.first_name
    assert retrieved.last_name == character.last_name
    assert retrieved.pronouns.subject == character.pronouns.subject
    assert retrieved.chapter_introduced == character.chapter_introduced


def test_get_characters_by_chapter(story_repo):
    """Test retrieving characters filtered by chapter"""
    # Create characters in different chapters
    char1 = Character(id=uuid4(), first_name="Alice", chapter_introduced=1)
    char2 = Character(id=uuid4(), first_name="Bob", chapter_introduced=1)
    char3 = Character(id=uuid4(), first_name="Charlie", chapter_introduced=2)

    for char in [char1, char2, char3]:
        story_repo.save_character(char)

    # Test filtering
    chapter1_chars = story_repo.get_characters(chapter=1)
    assert len(chapter1_chars) == 2
    assert {c.first_name for c in chapter1_chars} == {"Alice", "Bob"}

    chapter2_chars = story_repo.get_characters(chapter=2)
    assert len(chapter2_chars) == 1
    assert chapter2_chars[0].first_name == "Charlie"


def test_save_and_retrieve_elements(story_repo):
    """Test saving and retrieving elements"""
    element_time = datetime.now(timezone.utc)
    element = StoryElement(
        id=uuid4(),
        time=element_time,
        location="Test Location",
        content="Test content",
        chapter=1,
    )

    story_repo.save_element(element)
    retrieved = story_repo.get_elements(chapter=1)

    assert len(retrieved) == 1
    assert retrieved[0].id == element.id
    assert retrieved[0].content == element.content
    assert retrieved[0].time.timestamp() == pytest.approx(element_time.timestamp())


def test_clear_chapter(story_repo):
    """Test clearing chapter data"""
    # Create test data
    char1 = Character(id=uuid4(), first_name="Alice", chapter_introduced=1)
    char2 = Character(id=uuid4(), first_name="Bob", chapter_introduced=2)
    story_repo.save_character(char1)
    story_repo.save_character(char2)

    element1 = StoryElement(
        id=uuid4(),
        time=datetime.now(timezone.utc),
        location="Test",
        content="Chapter 1 element",
        chapter=1,
    )
    element2 = StoryElement(
        id=uuid4(),
        time=datetime.now(timezone.utc),
        location="Test",
        content="Chapter 2 element",
        chapter=2,
    )
    story_repo.save_element(element1)
    story_repo.save_element(element2)

    # Clear chapter 1
    story_repo.clear_chapter(1)

    # Verify chapter 1 data is gone but chapter 2 remains
    assert len(story_repo.get_characters(chapter=1)) == 0
    assert len(story_repo.get_characters(chapter=2)) == 1
    assert len(story_repo.get_elements(chapter=1)) == 0
    assert len(story_repo.get_elements(chapter=2)) == 1


def test_clear_from_chapter_onwards(story_repo):
    """Test clearing chapter data from a specific chapter onwards"""
    # Create test data across three chapters
    characters = []
    elements = []

    for chapter in [1, 2, 3]:
        char = Character(
            id=uuid4(), first_name=f"Character{chapter}", chapter_introduced=chapter
        )
        characters.append(char)
        story_repo.save_character(char)

        element = StoryElement(
            id=uuid4(),
            time=datetime.now(timezone.utc),
            location="Test",
            content=f"Chapter {chapter} element",
            chapter=chapter,
        )
        elements.append(element)
        story_repo.save_element(element)

    # Clear from chapter 2 onwards
    story_repo.clear_from_chapter_onwards(2)

    # Verify only chapter 1 data remains
    all_characters = story_repo.get_characters()
    assert len(all_characters) == 1
    assert all_characters[0].chapter_introduced == 1

    all_elements = story_repo.get_elements()
    assert len(all_elements) == 1
    assert all_elements[0].chapter == 1

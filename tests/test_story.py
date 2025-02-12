import pytest
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4
from unittest.mock import Mock, patch

from storyjupyter.domain.models import Character, StoryElement, StoryMetadata, Pronouns
from storyjupyter.domain.interfaces import StoryRepository, CharacterGenerator
from storyjupyter.domain.exceptions import (
    UninitializedStoryError,
    UninitializedLocationError,
)
from storyjupyter.story import Story


@pytest.fixture
def mock_repo() -> Mock:
    return Mock(spec=StoryRepository)


@pytest.fixture
def mock_generator() -> Mock:
    return Mock(spec=CharacterGenerator)


@pytest.fixture
def metadata() -> StoryMetadata:
    return StoryMetadata(
        title="Test Story", author="Test Author", created_at=datetime.now(timezone.utc)
    )


@pytest.fixture
def story(mock_repo: Mock, mock_generator: Mock, metadata: StoryMetadata) -> Story:
    """Create a mock story"""
    story = Story(
        title="Test Story",
        author="Test Author",
        repo=mock_repo,
        faker_generator=mock_generator,
        llm_generator=mock_generator,
        chapter=1,
    )
    story._metadata = metadata
    return story


def test_story_initialization(mock_repo: Mock, metadata: StoryMetadata):
    """Test story initialization saves metadata"""
    mock_generator = Mock()
    Story(
        title="Test Story",
        author="Test Author",
        repo=mock_repo,
        faker_generator=mock_generator,
        llm_generator=mock_generator,
        chapter=1,
    )
    assert mock_repo.save_metadata.call_count >= 1


def test_story_requires_time_initialization(story: Story):
    """Test story requires time to be set"""
    with pytest.raises(UninitializedStoryError):
        story.add_element("Test element")


def test_story_requires_location_initialization(story: Story):
    """Test story requires location to be set"""
    story.set_time(datetime.now(timezone.utc))
    with pytest.raises(UninitializedLocationError):
        story.add_element("Test element")


def test_story_advances_time(story: Story):
    """Test time advancement works correctly"""
    initial_time = datetime.now(timezone.utc)
    story.set_time(initial_time)
    story.advance_time(timedelta(minutes=15))

    assert story._current_time == initial_time + timedelta(minutes=15)


def test_story_adds_element(story: Story, mock_repo: Mock):
    """Test adding an element"""
    time = datetime.now(timezone.utc)
    story.set_time(time)
    story.set_location("Test Location")

    element = story.add_element("Test element")

    assert isinstance(element.id, UUID)
    assert element.time == time
    assert element.location == "Test Location"
    assert element.content == "Test element"
    assert element.chapter == 1

    mock_repo.save_element.assert_called_once()
    assert mock_repo.save_metadata.call_count >= 1


@patch("uuid.uuid4")
def test_story_character_creation(
    mock_uuid: Mock, story: Story, mock_generator: Mock, mock_repo: Mock
):
    """Test character creation"""
    expected_uuid = uuid4()
    mock_uuid.return_value = expected_uuid
    expected_char = Character(
        id=expected_uuid,
        first_name="Test",
        last_name="Character",
        pronouns=Pronouns.from_subject("they"),
        chapter_introduced=1,
    )
    mock_generator.generate.return_value = expected_char

    character = story.create_character(
        first_name="Test", last_name="Character", pronouns="they"
    )

    assert character == expected_char
    mock_repo.save_character.assert_called_once_with(character)


def test_story_character_relationships(story: Story, mock_repo: Mock):
    """Test adding character relationships"""
    char1 = Character(id=uuid4(), first_name="Alice")
    char2 = Character(id=uuid4(), first_name="Bob")

    # Mock character retrieval
    mock_repo.get_character.side_effect = lambda id: {char1.id: char1, char2.id: char2}[
        id
    ]

    story.add_relationship(
        char1.id, char2.id, relationship_type="sibling", description="Twin siblings"
    )

    # Verify both characters were updated
    saved_chars = [call.args[0] for call in mock_repo.save_character.call_args_list]
    assert len(saved_chars) == 2

    # Check relationships were set correctly
    alice = [c for c in saved_chars if c.id == char1.id][0]
    bob = [c for c in saved_chars if c.id == char2.id][0]

    assert bob.id in alice.relationships
    assert alice.id in bob.relationships
    assert alice.relationships[bob.id].type == "sibling"
    assert bob.relationships[alice.id].type == "sibling"


def test_story_manuscript_generation(story: Story, mock_repo: Mock):
    """Test manuscript generation"""
    time = datetime.now(timezone.utc)
    elements = [
        StoryElement(
            id=uuid4(), time=time, location="Location 1", content="element 1", chapter=1
        ),
        StoryElement(
            id=uuid4(),
            time=time + timedelta(minutes=15),
            location="Location 2",
            content="element 2",
            chapter=1,
        ),
    ]
    # Use the correct method name from the interface
    mock_repo.get_elements.return_value = elements

    manuscript = story.generate_manuscript()

    # Check chapter headers
    assert "# Chapter 1" in manuscript

    # Check location headers
    assert "## Location 1" in manuscript
    assert "## Location 2" in manuscript

    # Check element content
    assert "element 1" in manuscript
    assert "element 2" in manuscript

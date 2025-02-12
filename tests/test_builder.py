# tests/test_builder.py
import pytest
from unittest.mock import Mock, patch

from storyjupyter.builder import StoryBuilder, create_story
from storyjupyter.story import Story
from storyjupyter.generation import FakerCharacterGenerator, LLMCharacterGenerator


@pytest.fixture
def builder():
    """Create a basic builder instance"""
    return StoryBuilder("Test Story", "Test Author")


def test_builder_basic_configuration(builder: StoryBuilder):
    """Test basic builder configuration"""
    assert builder.title == "Test Story"
    assert builder.author == "Test Author"
    assert builder._chapter == 1
    assert builder._faker_seed == 42
    assert builder._mongo_uri == "mongodb://localhost:27017"


def test_builder_mongo_configuration(builder: StoryBuilder):
    """Test MongoDB configuration"""
    custom_uri = "mongodb://custom:27017"
    custom_db = "test_db"

    builder.with_mongo_connection(custom_uri, custom_db)
    assert builder._mongo_uri == custom_uri
    assert builder._db_name == custom_db


def test_builder_llm_configuration(builder: StoryBuilder):
    """Test LLM configuration"""
    model = "custom-model"
    api_key = "test-key"
    base_url = "http://custom:1234"

    builder.with_llm_config(model, api_key, base_url)
    assert builder._llm_model == model
    assert builder._api_key == api_key
    assert builder._ollama_url == base_url


def test_builder_chapter_configuration(builder: StoryBuilder):
    """Test chapter configuration"""
    builder.with_chapter(2)
    assert builder._chapter == 2

    with pytest.raises(ValueError):
        builder.with_chapter(0)


@patch("storyjupyter.builder.FakerCharacterGenerator")
@patch("storyjupyter.builder.LLMCharacterGenerator")
def test_builder_creates_story(
    mock_llm_gen: Mock,
    mock_faker_gen: Mock,
    builder: StoryBuilder,
):
    """Test story creation with mocked dependencies"""
    # Configure mocks
    mock_faker_instance = Mock(spec=FakerCharacterGenerator)
    mock_faker_gen.return_value = mock_faker_instance

    mock_llm_instance = Mock(spec=LLMCharacterGenerator)
    mock_llm_gen.return_value = mock_llm_instance

    # Build story
    story = builder.build()

    # Verify story was created with correct parameters
    assert isinstance(story, Story)
    assert story.metadata.title == "Test Story"
    assert story.metadata.author == "Test Author"
    assert story.faker_generator == mock_faker_instance
    assert story.llm_generator == mock_llm_instance


def test_create_story_convenience_function():
    """Test the create_story convenience function"""
    with patch("storyjupyter.builder.StoryBuilder.build") as mock_build:
        mock_story = Mock(spec=Story)
        mock_build.return_value = mock_story

        story = create_story(
            "Test Story",
            "Test Author",
            mongo_uri="mongodb://custom:27017",
            db_name="test_db",
            llm_model="custom-model",
            api_key="test-key",
            chapter=2,
        )

        assert story == mock_story
        mock_build.assert_called_once()

# tests/test_generation.py
import pytest
from unittest.mock import Mock, patch
from uuid import UUID

from storyjupyter.generation.faker import FakerCharacterGenerator
from storyjupyter.generation.llm import LLMCharacterGenerator, LLMProcessor


def test_faker_generator_basics():
    """Test basic Faker generator functionality"""
    generator = FakerCharacterGenerator(seed=42)

    with patch("random.random", return_value=0.1):  # Ensure hyphenated last name
        character = generator.generate()

    assert character.id is not None  # Assert that an ID was generated
    assert isinstance(character.id, UUID)  # Assert that the ID is a UUID
    assert character.first_name
    assert character.last_name
    assert character.last_name.find("-") != -1
    assert character.pronouns is not None
    assert "description" in character.attributes
    assert "age" in character.attributes
    assert "occupation" in character.attributes


def test_faker_generator_constraints():
    """Test Faker generator respects constraints"""
    generator = FakerCharacterGenerator()

    # Test with no provided character_id
    with patch("random.random", return_value=0.9):  # Ensure no hyphenated last name
        character = generator.generate(
            first_name="John",
            last_name="Doe",
            pronouns="he",
            age=25,
            occupation="Engineer",
        )

    assert character.id is not None
    assert isinstance(character.id, UUID)
    assert character.first_name == "John"
    assert character.last_name == "Doe"
    assert character.pronouns.subject == "he"
    assert character.attributes["age"] == 25
    assert character.attributes["occupation"] == "Engineer"

    # Test with a provided character_id
    custom_id = "protagonist"
    with patch("random.random", return_value=0.9):  # Ensure no hyphenated last name
        character = generator.generate(
            character_id=custom_id,
            first_name="John",
            last_name="Doe",
            pronouns="he",
            age=25,
            occupation="Engineer",
        )

    assert character.id == custom_id
    assert character.first_name == "John"
    assert character.last_name == "Doe"
    assert character.pronouns.subject == "he"
    assert character.attributes["age"] == 25
    assert character.attributes["occupation"] == "Engineer"


def test_faker_generator_pronouns():
    """Test Faker generates appropriate names for pronouns"""
    generator = FakerCharacterGenerator()

    # Test male names
    character = generator.generate(pronouns="he")
    assert character.pronouns.subject == "he"
    assert character.pronouns.object == "him"

    # Test female names
    character = generator.generate(pronouns="she")
    assert character.pronouns.subject == "she"
    assert character.pronouns.object == "her"

    # Test neutral names
    character = generator.generate(pronouns="they")
    assert character.pronouns.subject == "they"
    assert character.pronouns.object == "them"


@pytest.fixture
def mock_ollama_response():
    """Create mock Ollama response"""
    return Mock(
        message={
            "content": """{
            "first": "Alice",
            "middle": ["Marie"],
            "last": "Johnson",
            "pronouns": "she",
            "description": "Tall with brown hair and green eyes",
            "age": 28,
            "occupation": "Software Engineer",
            "hobbies": ["Reading", "Hiking"]
        }"""
        }
    )


@pytest.fixture
def mock_ollama_client(mock_ollama_response):
    """Create mock Ollama client"""
    mock_client = Mock()
    mock_client.chat.return_value = mock_ollama_response
    return mock_client


def test_llm_generator_basics(mock_ollama_client):
    """Test basic LLM generator functionality"""
    with patch("ollama.Client", return_value=mock_ollama_client):
        generator = LLMCharacterGenerator(
            base_url="http://test:1234", model="test-model"
        )
        character = generator.generate()

        assert character.id is not None
        assert isinstance(character.id, UUID)
        assert character.first_name == "Alice"
        assert character.middle_names == ["Marie"]
        assert character.last_name == "Johnson"
        assert character.pronouns.subject == "she"
        assert character.attributes["age"] == 28
        assert character.attributes["occupation"] == "Software Engineer"
        assert "Reading" in character.attributes["hobbies"]


def test_llm_generator_constraints(mock_ollama_client):
    """Test LLM generator respects constraints"""
    with patch("ollama.Client", return_value=mock_ollama_client):
        generator = LLMCharacterGenerator(
            base_url="http://test:1234", model="test-model"
        )

        # Test with no provided character_id
        character = generator.generate(
            first_name="John",
            last_name="Doe",
            pronouns="he",
            occupation="Teacher",
            context="This character is a dedicated educator.",
        )

        assert character.id is not None
        assert isinstance(character.id, UUID)

        # Verify the constraint was included in the prompt
        prompt_args = mock_ollama_client.chat.call_args[1]["messages"][0]["content"]
        assert "First name: John" in prompt_args
        assert "Last name: Doe" in prompt_args
        assert "Pronouns: he" in prompt_args
        assert "occupation: Teacher" in prompt_args
        assert "This character is a dedicated educator" in prompt_args

        # Test with a provided character_id
        custom_id = "protagonist"
        character = generator.generate(
            character_id=custom_id,
            first_name="John",
            last_name="Doe",
            pronouns="he",
            occupation="Teacher",
            context="This character is a dedicated educator.",
        )

        assert character.id == custom_id

        # Verify the constraint was included in the prompt
        prompt_args = mock_ollama_client.chat.call_args[1]["messages"][0]["content"]
        assert "First name: John" in prompt_args
        assert "Last name: Doe" in prompt_args
        assert "Pronouns: he" in prompt_args
        assert "occupation: Teacher" in prompt_args
        assert "This character is a dedicated educator" in prompt_args


def test_llm_hyphenated_names(mock_ollama_client):
    """Test LLM handles hyphenated last names"""
    mock_ollama_client.chat.return_value.message[
        "content"
    ] = """{
        "first": "Alice",
        "last": "Smith",
        "second_last": "Jones",
        "pronouns": "she",
        "description": "Test description",
        "age": 28,
        "occupation": "Test occupation",
        "hobbies": ["Test hobby"]
    }"""

    with patch("ollama.Client", return_value=mock_ollama_client):
        generator = LLMCharacterGenerator(
            base_url="http://test:1234", model="test-model"
        )
        character = generator.generate()

        assert character.last_name == "Smith-Jones"


def test_llm_error_handling(mock_ollama_client):
    """Test LLM handles errors gracefully"""
    # Simulate malformed response
    mock_ollama_client.chat.return_value.message["content"] = "invalid json"

    with patch("ollama.Client", return_value=mock_ollama_client):
        generator = LLMCharacterGenerator(
            base_url="http://test:1234", model="test-model"
        )
        with pytest.raises(Exception):
            character = generator.generate()
            del character


def test_llm_processor_basic():
    """Test basic LLMProcessor functionality"""
    # Test initialization
    processor = LLMProcessor(base_url="http://test:1234")
    assert processor
    # TODO: Add more tests

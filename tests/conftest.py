# tests/conftest.py
import pytest
from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import Mock

from storyjupyter.domain.models import Character, StoryElement, StoryMetadata, Pronouns
from storyjupyter.domain.interfaces import StoryRepository, CharacterGenerator


@pytest.fixture
def mock_repo():
    """Create a mock repository"""
    return Mock(spec=StoryRepository)


@pytest.fixture
def mock_generator():
    """Create a mock character generator"""
    return Mock(spec=CharacterGenerator)


@pytest.fixture
def sample_metadata():
    """Create sample story metadata"""
    return StoryMetadata(
        title="Test Story", author="Test Author", created_at=datetime.now(timezone.utc)
    )


@pytest.fixture
def sample_character():
    """Create a sample character"""
    return Character(
        id=uuid4(),
        first_name="John",
        last_name="Doe",
        pronouns=Pronouns.from_subject("he"),
        chapter_introduced=1,
    )


@pytest.fixture
def sample_element():
    """Create a sample story element"""
    return StoryElement(
        id=uuid4(),
        time=datetime.now(timezone.utc),
        location="Test Location",
        content="Test element content",
        chapter=1,
    )


@pytest.fixture
def mongodb_uri():
    """MongoDB connection string for testing"""
    return "mongodb://localhost:27017"


@pytest.fixture
def test_db_name():
    """Generate unique test database name"""
    return f"test_db_{uuid4().hex}"

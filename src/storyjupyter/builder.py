# src/storyjupyter/builder.py
from datetime import datetime
from typing import Optional

from .story import Story
from .generation import FakerCharacterGenerator, LLMCharacterGenerator
from .persistence import MongoDBStoryRepository, DummyStoryRepository


class StoryBuilder:
    """Builder class for creating Story instances with sensible defaults"""

    DEFAULT_MONGO_URI = "mongodb://localhost:27017"
    DEFAULT_OLLAMA_URL = "http://localhost:11434"
    DEFAULT_OLLAMA_MODEL = "llama3.1:8b-instruct-q5_K_S"

    def __init__(self, title: Optional[str], author: Optional[str]):
        """Initialize builder with required title and author"""
        self.title = title
        self.author = author

        # Initialize with default values
        self._mongo_uri = self.DEFAULT_MONGO_URI
        self._ollama_url = self.DEFAULT_OLLAMA_URL
        self._db_name: Optional[str] = None
        self._chapter = 1
        self._faker_seed = 42
        self._llm_model = self.DEFAULT_OLLAMA_MODEL
        self._api_key: Optional[str] = None

    def with_mongo_connection(
        self,
        uri: Optional[str] = "mongodb://localhost:27017",
        db_name: Optional[str] = "storyjupyter",
    ) -> "StoryBuilder":
        """Configure MongoDB connection"""
        self._mongo_uri = uri
        self._db_name = db_name
        return self

    def with_llm_config(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> "StoryBuilder":
        """Configure LLM settings"""
        if model:
            self._llm_model = model
        if api_key:
            self._api_key = api_key
        if base_url:
            self._ollama_url = base_url
        return self

    def with_faker_seed(self, seed: int) -> "StoryBuilder":
        """Set seed for Faker generator"""
        self._faker_seed = seed
        return self

    def with_chapter(self, chapter: int) -> "StoryBuilder":
        """Set chapter number"""
        if chapter < 1:
            raise ValueError("Chapter number must be positive")
        self._chapter = chapter
        return self

    def _generate_db_name(self) -> str:
        """Generate a database name from story title if none provided"""
        from slugify import slugify

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"story_{slugify(self.title)}_{timestamp}"

    def build(self) -> Story:
        """Create Story instance with configured settings"""
        # Set up database name
        repo = DummyStoryRepository()
        if self._db_name is not None:
            repo = MongoDBStoryRepository(
                connection_string=self._mongo_uri, database=self._db_name
            )

        # Create character generators
        faker_generator = FakerCharacterGenerator(seed=self._faker_seed)
        llm_generator = LLMCharacterGenerator(
            model=self._llm_model, api_key=self._api_key, base_url=self._ollama_url
        )
        repo = repo
        return Story(
            title=self.title,
            author=self.author,
            faker_generator=faker_generator,
            llm_generator=llm_generator,
            repo=repo,  # Pass the repository here
            chapter=self._chapter,
        )


def create_story(
    title: str,
    author: str,
    *,
    mongo_uri: Optional[str] = None,
    db_name: Optional[str] = None,
    llm_model: Optional[str] = None,
    api_key: Optional[str] = None,
    chapter: int = 1,
) -> Story:
    """Convenience function to create a Story with minimal configuration"""
    builder = StoryBuilder(title, author)

    if mongo_uri or db_name:
        builder.with_mongo_connection(mongo_uri, db_name)

    if llm_model or api_key:
        builder.with_llm_config(model=llm_model, api_key=api_key)

    if chapter != 1:
        builder.with_chapter(chapter)

    return builder.build()

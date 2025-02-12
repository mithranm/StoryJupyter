# src/storyjupyter/generation/faker.py
from faker import Faker
from typing import Optional
import random
from uuid import UUID, uuid4

from ..domain.models import Character, Pronouns


class FakerCharacterGenerator:
    """Generates characters using the Faker library"""

    def __init__(self, locale: str = "en_US", seed: int = 1):
        """Initialize Faker with the specified locale"""
        self.fake = Faker(locale=locale)
        Faker.seed(seed)

    def generate(
        self,
        character_id: UUID = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        pronouns: Optional[str] = None,
        chapter: int = None,
        **kwargs,
    ) -> Character:
        """Generate a character using Faker"""
        if character_id is None:
            character_id = uuid4()

        # Determine pronouns first as they affect name generation
        if pronouns is None:
            pronouns = random.choice(["he", "she", "they"])

        # Generate names based on pronouns
        if pronouns == "he":
            first = first_name or self.fake.first_name_male()
            middle_names = [
                self.fake.first_name_male() for _ in range(random.randint(0, 2))
            ]
        elif pronouns == "she":
            first = first_name or self.fake.first_name_female()
            middle_names = [
                self.fake.first_name_female() for _ in range(random.randint(0, 2))
            ]
        else:
            first = first_name or self.fake.first_name()
            middle_names = [self.fake.first_name() for _ in range(random.randint(0, 2))]

        last = last_name or self.fake.last_name()

        # 20% chance of hyphenated last name
        if random.random() < 0.2:
            last = f"{self.fake.last_name()}-{last}"

        # Generate base attributes
        attributes = {
            "description": self.fake.paragraph(),
            "age": random.randint(18, 80),  # Default adult age range
            "occupation": self.fake.job(),
            "chapter_introduced": chapter,
        }

        # Add any additional attributes
        attributes.update(kwargs)

        return Character(
            id=character_id,
            first_name=first,
            middle_names=middle_names,
            last_name=last,
            pronouns=Pronouns.from_subject(pronouns),
            attributes=attributes,
        )

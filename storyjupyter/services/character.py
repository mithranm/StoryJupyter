from faker import Faker
from ..core.models import Character, NameComponents
from ..core.protocols import CharacterGenerator
from ..core.llm import LangChainProcessor
from ..core.pronouns import Pronouns
from typing import Dict, Any, Optional, Sequence
import json
import random
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class FakerCharacterGenerator(CharacterGenerator):
    """Generates characters using the Faker library"""

    def __init__(self, locale: str = "en_US", gender: str = "any"):
        """Initialize Faker with the specified locale and gender"""
        self.fake = Faker(locale)

    def generate(self, character_id, **kwargs) -> Character:
        """Generates a character using Faker"""
        
        pronoun_set = kwargs.get("pronoun_set") or random.choice(["he", "she", "they"])
        first = kwargs.get("first")
        middle = kwargs.get("middle")
        last = kwargs.get("last")
        description = kwargs.get("description")
        middle_range = range(random.randint(0, 2))
        if pronoun_set == "he":
            first = first or self.fake.first_name_male()
            default_middle_names = [self.fake.first_name_male() for _ in middle_range]
        elif pronoun_set == "she":
            first = first or self.fake.first_name_female()
            default_middle_names = [self.fake.first_name_female() for _ in middle_range]
        else:
            first = first or self.fake.first_name()
            default_middle_names = [self.fake.first_name() for _ in middle_range]

        middle = middle or default_middle_names

        last = last or self.fake.last_name()
        
        # 20% chance of hyphenation
        if random.random() < 0.2:
            last = f"{self.fake.last_name()}-{last}"

        description = description or self.fake.paragraph()
        
        # Remove kwargs that faker generator handles from attributes if present
        attributes = kwargs.copy()
        attributes.pop("description", None)
        attributes.pop("first", None)
        attributes.pop("last", None)
        attributes.pop("middle", None)
        attributes.pop("pronoun_set", None)

        return Character(
            character_id=character_id,
            name_components=NameComponents(
                    first=first,
                    middle=middle,
                    last=last,
                ),
            pronouns=Pronouns(pronoun_set),
            attributes=attributes,
            relationships={},
        )


class LLMCharacterGenerator(CharacterGenerator):
    def __init__(
        self,
        model: str = "llama3.1:8b-instruct-q5_K_S",
        base_url: str = "http://localhost:11434",
        temperature: float = 0.7,
        top_p: float = 0.5,
        max_tokens: int = 1000,
        character_schema: Optional[dict] = None,
    ):
        self.llm_processor = LangChainProcessor(base_url=base_url)
        self.model = model
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens
        self.character_schema = character_schema or self._default_schema()

    def _default_schema(self) -> dict:
        """Default schema for character generation"""
        return {
            "type": "object",
            "properties": {
                "first": {
                    "type": "string",
                    "description": "The character's first name",
                },
                "middle": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional middle names (0-2 names). Can be an empty array.",
                },
                "last": {"type": "string", "description": "The character's last name"},
                "second_last": {
                    "type": "string",
                    "description": "The character's second last name, if they have one",
                },
                "description": {
                    "type": "string",
                    "description": "Physical description and personality traits",
                },
                "pronoun_set": {
                    "type": "string",
                    "enum": ["he", "she", "they"],
                    "description": "Preferred pronouns",
                },
                "age": {"type": "integer"},
                "occupation": {"type": "string"},
                "hobbies": {"type": "array", "items": {"type": "string"}},
            },
            "required": [
                "first",
                "last",
                "description",
                "pronoun_set",
                "age",
                "occupation",
                "hobbies",
            ],
        }

    def generate(
        self,
        character_id,
        name: Optional[str] = None,
        preset_values: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Character:
        """Generate a single character using LLM"""
        # Start with preset values
        all_presets = preset_values.copy() if preset_values else {}

        # If name is provided, parse it into components
        if name:
            name_parts = name.split()
            if len(name_parts) >= 2:
                all_presets["first"] = name_parts[0]
                all_presets["last"] = name_parts[-1]
                if len(name_parts) > 2:
                    all_presets["middle"] = name_parts[1:-1]

        # Create generation prompt
        prompt = """You are an AI assistant that generates characters.
        You MUST respond ONLY with a JSON object that matches the following schema.
        Do not include any other text, explanations, or conversational elements.

        Schema:
        """
        prompt += json.dumps(self.character_schema)

        if kwargs.get("prompt"):
            prompt += f"\nAdditional context: {kwargs['prompt']}"

        try:
            response = self.llm_processor.generate_structured_response(
                prompt=prompt,
                schema=self.character_schema,
                model=self.model,
                temperature=self.temperature,
                top_p=self.top_p,
                max_tokens=self.max_tokens,
            )

            data = response.model_dump()

            # Extract name components
            first = data.get("first")
            middle = data.get("middle", [])
            last = data.get("last")
            second_last = data.get("second_last", None)

            if second_last:
                last = f"{last}-{second_last}"

            # Create character with extracted name components
            try:
                pronouns = Pronouns(data.get("pronoun_set", "they"))
            except ValueError as e:
                logging.error(
                    f"Invalid pronoun set generated by LLM: {data.get('pronoun_set')}, defaulting to 'they'. Error: {e}"
                )
                pronouns = Pronouns("they")

            return Character(
                character_id=character_id,
                name_components=NameComponents(
                    first=first,
                    middle=middle,
                    last=last,
                ),
                pronouns=pronouns,
                attributes=data,
                relationships={},
            )

        except Exception as e:
            logging.exception(f"Error generating character: {e}")
            raise
        
    def __str__(self):
        """Return a string representation of the character."""
        output = f"Character ID: {self.character_id}\n"
        output += f"Name: {self.name_components.first} "
        if self.name_components.middle:
            output += " ".join(self.name_components.middle) + " "
        output += f"{self.name_components.last}\n"

        pronoun_obj = Pronouns(self.pronouns.pronoun_set)
        pronouns = pronoun_obj.as_dict()
        output += (
            f"Pronouns: {pronouns['subject']} / {pronouns['object']} / {pronouns['possessive']}\n"
        )

        output += "Attributes:\n"
        for key, value in self.attributes.items():
            output += f"  {key}: {value}\n"

        output += "Relationships:\n"
        for key, value in self.relationships.items():
            output += f"  {key}: {value}\n"

        return output
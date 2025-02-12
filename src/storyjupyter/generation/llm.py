# src/storyjupyter/generation/llm.py
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
import json
import logging
import ollama

from ..domain.models import Character, Pronouns


class LLMProcessor:
    """Processes LLM requests using Ollama"""

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
    ):
        self.client = ollama.Client(
            host=base_url,
            headers={"Authorization": f"Bearer {api_key}"} if api_key else None,
        )

    def generate(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.7,
        top_p: float = 0.5,
        top_k: int = 50,
        max_tokens: int = 1000,
    ) -> str:
        """Generate text using LLM"""
        response = self.client.chat(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            options={
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k,
                "max_tokens": max_tokens,
            },
        )
        return response.message["content"]

    def generate_structured_response(
        self, prompt: str, schema: Dict[str, Any], **kwargs
    ) -> Dict[str, Any]:
        """Generate structured response using schema"""
        options = {
            "temperature": kwargs.pop("temperature", 0.7),
            "top_p": kwargs.pop("top_p", 0.5),
            "max_tokens": kwargs.pop("max_tokens", 1000),
        }
        response = self.client.chat(
            messages=[{"role": "user", "content": prompt}],
            format=schema,
            options=options,
            **kwargs,  # Pass any remaining kwargs
        )
        return json.loads(response.message["content"])


class LLMCharacterGenerator:
    """Generates characters using LLM"""

    def __init__(
        self,
        model: str,
        base_url: str,
        temperature: float = 0.7,
        top_p: float = 0.5,
        max_tokens: int = 1000,
        api_key: Optional[str] = None,
    ):
        self.llm = LLMProcessor(base_url=base_url, api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens

    def _default_schema(self, additional_properties: Dict[str, Any] = None) -> Dict[str, Any]:
        """Default schema for character generation"""
        schema = {
            "type": "object",
            "properties": {
                "first": {
                    "type": "string",
                    "description": "The character's first name",
                },
                "middle": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional middle names (0-2 names)",
                },
                "last": {"type": "string", "description": "The character's last name"},
                "second_last": {
                    "type": "string",
                    "description": "Optional second last name for hyphenation",
                },
                "pronouns": {
                    "type": "string",
                    "enum": ["he", "she", "they"],
                    "description": "Preferred pronouns",
                },
                "description": {
                    "type": "string",
                    "description": "Physical description and personality",
                },
                "age": {"type": "integer", "minimum": 0, "maximum": 120},
                "occupation": {
                    "type": "string",
                    "description": "Character's occupation or role",
                },
                "hobbies": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Character's hobbies and interests",
                },
            },
            "required": [
                "first",
                "last",
                "pronouns",
                "description",
                "age",
                "occupation",
                "hobbies",
            ],
        }

        if additional_properties:
            schema["properties"].update(additional_properties)
            schema["required"].extend(additional_properties.keys())

        return schema

    def generate(
        self,
        character_id: UUID = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        pronouns: Optional[str] = None,
        chapter: int = None,
        context: str = "",
        **kwargs,
    ) -> Character:
        """Generate a character using LLM"""
        if character_id is None:
            character_id = uuid4()
        # Build constraints for prompt
        constraints = []
        if first_name:
            constraints.append(f"First name: {first_name}")
        if last_name:
            constraints.append(f"Last name: {last_name}")
        if pronouns:
            constraints.append(f"Pronouns: {pronouns}")
        for key, value in kwargs.items():
            if isinstance(value, (str, int, float)):
                constraints.append(f"{key}: {value}")

        # Create prompt
        prompt = f"""Generate a character with these attributes:
        {chr(10).join(constraints) if constraints else "No specific constraints"}
        
        {context if context else ""}
        
        Respond with a JSON object that matches the schema."""

        try:
            # Generate character data
            # Build dynamic schema
            additional_properties = {}
            for key, value in kwargs.items():
                if key not in self._default_schema()["properties"]:
                    additional_properties[key] = {"type": "string"}  # Defaulting to string type

            data = self.llm.generate_structured_response(
                prompt=prompt,
                schema=self._default_schema(additional_properties=additional_properties),
                model=self.model,
                temperature=self.temperature,
                top_p=self.top_p,
                max_tokens=self.max_tokens,
            )

            # Extract name components
            first = data.get("first")
            middle = data.get("middle", [])
            last = data.get("last")
            if second_last := data.get("second_last"):
                last = f"{last}-{second_last}"

            # Create attributes
            attributes = {
                "description": data.get("description"),
                "age": data.get("age"),
                "occupation": data.get("occupation"),
                "hobbies": data.get("hobbies", []),
                "chapter_introduced": chapter,
            }
            attributes.update(kwargs)

            return Character(
                id=character_id,
                first_name=first,
                middle_names=middle,
                last_name=last,
                pronouns=Pronouns.from_subject(data.get("pronouns", "they")),
                attributes=attributes,
            )

        except Exception as e:
            logging.exception(f"Error generating character: {e}")
            raise
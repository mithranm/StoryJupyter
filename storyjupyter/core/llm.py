from typing import Protocol
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import ollama
from pydantic import create_model, BaseModel, ValidationError
from typing import Any, Dict, Optional, Type
import json
import re

class LangChainProcessor:
    """LangChain implementation of LLM processing"""
    
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "http://localhost:11434",
    ) -> None:
        self.client = ollama.Client(
            host=base_url,
            headers={'Authorization' : f'Bearer {api_key}'}
        )
            
    def generate(
        self,
        prompt: str,
        model: str = "llama3.1:8b-instruct-q5_K_S",
        top_p: float = 0.5,
        top_k: int = 50,
        temperature: float = 0.5,
        max_tokens: int = 100
        ) -> str:
        """Generate text using LLM"""
        response = self.client.chat(
            messages=[{
                'role': 'user',
                'content': prompt
            }],
            model=model,
            options={
                'temperature': temperature,
                'top_p': top_p,
                'top_k': top_k,
                'max_tokens': max_tokens
            }
        )
        return response.message['content']

    @staticmethod
    def create_dynamic_model(schema: Dict[str, Any]) -> Type[BaseModel]:
        """Creates a dynamic Pydantic model based on the provided schema."""
        fields = {}
        for field_name, field_schema in schema.get('properties', {}).items():
            field_type = str  # Default field type

            if field_schema.get('type') == 'integer':
                field_type = int
            elif field_schema.get('type') == 'number':
                field_type = float
            elif field_schema.get('type') == 'boolean':
                field_type = bool
            elif field_schema.get('type') == 'array':
                if "items" in field_schema:
                    item_type = field_schema["items"].get("type", "string")
                    if item_type == "string":
                        field_type = list[str]
                    elif item_type == "integer":
                        field_type = list[int]
                    else:
                        field_type = list[Any]
                else:
                    field_type = list[Any]
            elif field_schema.get('type') == 'object':
                field_type = dict
            elif field_schema.get('type') == 'string':
                field_type = str

            # Add the field to the fields dictionary
            fields[field_name] = (field_type | None, None)  # Ellipsis makes the field required

        # Create the dynamic model
        dynamic_model = create_model(
            'DynamicModel',
            **fields,
            __config__=None # Remove the config
        )

        return dynamic_model

    # Example usage
    def generate_structured_response(
        self,
        prompt: str,
        schema: Dict[str, Any],
        model: str = "llama3.1:8b-instruct-q5_K_S",
        top_p: float = 0.5,
        top_k: int = 50,
        temperature: float = 0.5,
        max_tokens: int = 100
    ) -> BaseModel:
        """
        Generate a structured response using any schema
        """
        # Create dynamic Pydantic model from schema
        DynamicModel = LangChainProcessor.create_dynamic_model(schema)
        
        # Make the request
        try:
            response = self.client.chat(
                messages=[{
                    'role': 'user',
                    'content': prompt
                }],
                model=model,
                format=DynamicModel.model_json_schema(),  # Use raw schema here
                options={
                    'temperature': temperature,
                    'top_p': top_p,
                    'top_k': top_k,
                    'max_tokens': max_tokens
                }
            )
            # Parse and validate response
            try:
                json_string = response.message.content
                # Attempt to extract JSON using regex
                match = re.search(r"\{.*\}", json_string, re.DOTALL)
                if match:
                    json_string = match.group(0)
                return DynamicModel.model_validate_json(json_string)
            except ValidationError as e:
                print(f"Validation Error: {e}")
                print(f"Response content: {response.message.content}")
                raise
        except Exception as e:
            print(f"Ollama Error: {e}")
            raise
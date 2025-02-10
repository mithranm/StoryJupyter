# storyjupyter/services/narrative.py
from typing import Protocol, Literal
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

ModelProvider = Literal["openai", "ollama", "qwen", "hunyuan"]

class LLMProcessor(Protocol):
    """Protocol for LLM processing"""
    async def generate(self, prompt: str) -> str: ...
    async def transform(self, text: str, instruction: str) -> str: ...

class LangChainProcessor:
    """LangChain implementation of LLM processing"""
    
    def __init__(
        self,
        provider: ModelProvider = "ollama",
        api_key: str | None = None,
        model_name: str = "llama2"
    ) -> None:
        base_urls = {
            "ollama": "http://localhost:11434/v1",
            "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "hunyuan": "https://api.hunyuan.cloud.tencent.com/v1",
            "openai": "https://api.openai.com/v1"
        }
        
        self.llm = ChatOpenAI(
            openai_api_base=base_urls[provider],
            openai_api_key=api_key or "ollama",  # Default for Ollama
            model_name=model_name
        )
        
    async def generate(self, prompt: str) -> str:
        """Generate text using LLM"""
        messages = [
            SystemMessage(content="You are a creative writing assistant."),
            HumanMessage(content=prompt)
        ]
        response = await self.llm.agenerate([messages])
        return response.generations[0][0].text
        
    async def transform(self, text: str, instruction: str) -> str:
        """Transform text according to instruction"""
        messages = [
            SystemMessage(content=f"Transform the following text. {instruction}"),
            HumanMessage(content=text)
        ]
        response = await self.llm.agenerate([messages])
        return response.generations[0][0].text
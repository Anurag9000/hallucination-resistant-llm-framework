from abc import ABC, abstractmethod

class LLMInterface(ABC):
    """
    Abstract Base Class for LLM Providers.
    Supports Ollama (local) and Gemini (cloud).
    """
    
    @abstractmethod
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """Generates text from a prompt."""
        pass

    @abstractmethod
    async def generate_structured(self, prompt: str, schema: dict, **kwargs) -> dict:
        """Generates structured JSON output."""
        pass

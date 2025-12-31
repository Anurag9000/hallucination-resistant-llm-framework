import asyncio
import json
import random
from .llm_interface import LLMInterface

class MockLLM(LLMInterface):
    """
    Fast Mock LLM for simulation purposes.
    Returns plausible-sounding text based on keywords.
    """
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        await asyncio.sleep(0.1) # Simulate network latency
        
        # Simple keyword matching for dynamic-ish responses
        if "capital" in prompt.lower() and "mars" in prompt.lower():
            if "sci-fi" in prompt.lower() or "fiction" in prompt.lower():
                return "The capital of Mars is Cydonia City, established in 2085."
            return "Mars does not have a capital city as it is uninhabited."
        
        if "population" in prompt.lower() and "france" in prompt.lower():
             return "The population of France is approximately 67 million."

        return f"[MockLLM] Generated response for: {prompt[:30]}..."

    async def generate_structured(self, prompt: str, schema: dict, **kwargs) -> dict:
        await asyncio.sleep(0.1)
        # return dummy JSON based on schema keys
        result = {}
        for key in schema.get("properties", {}).keys():
            result[key] = f"mock_{key}_value"
        return result

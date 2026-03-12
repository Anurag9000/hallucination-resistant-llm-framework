import json
import aiohttp
from core.llm_interface import LLMInterface

# Timeout so we fail fast if Ollama is not running instead of hanging indefinitely
OLLAMA_TIMEOUT = aiohttp.ClientTimeout(total=30, connect=5)

class OllamaLLM(LLMInterface):
    """
    Implements LLMInterface for local generation via Ollama's REST API.
    By default accesses http://localhost:11434
    """

    def __init__(self, model_name: str = "llama3.2"):
        self.model_name = model_name
        self.base_url = "http://localhost:11434/api/generate"

    async def generate_text(self, prompt: str, **kwargs) -> str:
        """Generates raw text from a local Ollama model asynchronously."""
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False
        }
        
        # Merge any additional kwargs like options (temperature, etc.)
        if kwargs:
            payload["options"] = kwargs

        async with aiohttp.ClientSession(timeout=OLLAMA_TIMEOUT) as session:
            try:
                async with session.post(self.base_url, json=payload) as response:
                    response.raise_for_status()
                    data = await response.json()
                    return data.get("response", "")
            except aiohttp.ClientConnectorError:
                print(f"[OllamaLLM] Cannot connect to Ollama daemon at {self.base_url}. Is 'ollama serve' running?")
                return "[Error: Ollama not running]"
            except Exception as e:
                print(f"Error accessing Ollama [{self.model_name}]: {e}")
                return "[Error generating response]"

    async def generate_structured(self, prompt: str, schema: dict, **kwargs) -> dict:
        """
        Forces Ollama to output standard JSON. 
        Note that some smaller models may ignore strict schemas without specific prompting.
        """
        prompt_with_schema = f"{prompt}\n\nPlease output ONLY valid JSON following this exact schema:\n{json.dumps(schema, indent=2)}\n\n"
        
        payload = {
            "model": self.model_name,
            "prompt": prompt_with_schema,
            "stream": False,
            "format": "json"  # Ollama native JSON mode
        }
        
        if kwargs:
            payload["options"] = kwargs

        async with aiohttp.ClientSession(timeout=OLLAMA_TIMEOUT) as session:
            try:
                async with session.post(self.base_url, json=payload) as response:
                    response.raise_for_status()
                    data = await response.json()
                    response_text = data.get("response", "{}")
                    try:
                        return json.loads(response_text)
                    except json.JSONDecodeError:
                        print(f"Failed to parse Ollama JSON: {response_text}")
                        return {}
            except aiohttp.ClientConnectorError:
                print(f"[OllamaLLM] Cannot connect to Ollama daemon at {self.base_url}. Is 'ollama serve' running?")
                return {}
            except Exception as e:
                print(f"Error accessing Ollama [{self.model_name}]: {e}")
                return {}


import os
import json
from core.llm_interface import LLMInterface
try:
    from config import Config
except ImportError:
    # If running from a subdir, provide path
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
    from config import Config

class GeminiLLM(LLMInterface):
    """
    Implements LLMInterface for remote high-rate generation via the Google Gemini API.
    Requires GEMINI_API_KEY environment variable.
    """

    def __init__(self, model_name: str = "gemini-2.5-flash", max_context_chars: int = 8192):
        self.model_name = model_name
        self.max_context_chars = max_context_chars
        self.api_key = os.environ.get("GEMINI_API_KEY")
        
        if not self.api_key:
            print("WARNING: GEMINI_API_KEY environment variable not set. GeminiLLM will fail if called.")
            self.client = None
        else:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except ImportError:
                print("WARNING: 'google-genai' package not found. Run 'pip install google-genai'.")
                self.client = None

    async def generate_text(self, prompt: str, **kwargs) -> str:
        """Generates raw text from Gemini with simulated low-context truncation."""
        if not self.client:
            return "[Error: Client not initialized. Check API Key and pip dependencies.]"

        # Simulate low context by truncating prompt
        if len(prompt) > self.max_context_chars:
            truncated_prompt = "...[Context Truncated]..." + prompt[-self.max_context_chars:]
        else:
            truncated_prompt = prompt

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=truncated_prompt,
            )
            return response.text
        except Exception as e:
            print(f"Error accessing Gemini [{self.model_name}]: {e}")
            return "[Error generating response]"

    async def generate_structured(self, prompt: str, schema: dict, **kwargs) -> dict:
        """Forces Gemini to output standard JSON with simulated low-context truncation."""
        if not self.client:
            return {}

        # Simulate low context
        if len(prompt) > self.max_context_chars:
            truncated_prompt = "...[Context Truncated]..." + prompt[-self.max_context_chars:]
        else:
            truncated_prompt = prompt

        prompt_with_schema = f"{truncated_prompt}\n\nPlease output ONLY valid JSON. Your response must conform to this schema: {json.dumps(schema)}"
        try:
            from google import genai
            # Use strict JSON mode in Gemini
            config = genai.types.GenerateContentConfig(
                response_mime_type="application/json"
            )
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt_with_schema,
                config=config
            )
            
            try:
                return json.loads(response.text)
            except json.JSONDecodeError:
                print(f"Failed to parse Gemini JSON: {response.text}")
                return {}
                
        except Exception as e:
            print(f"Error accessing Gemini [{self.model_name}]: {e}")
            return {}

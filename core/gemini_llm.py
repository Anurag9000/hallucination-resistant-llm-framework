import os
import json
from core.llm_interface import LLMInterface

class GeminiLLM(LLMInterface):
    """
    Implements LLMInterface for remote high-rate generation via the Google Gemini API.
    Requires GEMINI_API_KEY environment variable.
    """

    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.model_name = model_name
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
        """Generates raw text from Gemini asynchronously."""
        if not self.client:
            return "[Error: Client not initialized. Check API Key and pip dependencies.]"

        try:
            # We use the standard synchronous generate_content because inside an async framework 
            # it might block, but google-genai AsyncClient is also available if needed.
            # Using standard Client here as recommended by recent SDK standards, but 
            # wrapping it or importing standard Async options is best.
            # For robustness we will use the async generate if available, or just call generate.
            # (Note: genai.Client() has async generate_content natively in some wrappers, but we'll try direct)
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                # kwargs can contain config
            )
            return response.text
        except Exception as e:
            print(f"Error accessing Gemini [{self.model_name}]: {e}")
            return "[Error generating response]"

    async def generate_structured(self, prompt: str, schema: dict, **kwargs) -> dict:
        """
        Forces Gemini to output standard JSON. 
        """
        if not self.client:
            return {}

        prompt_with_schema = f"{prompt}\n\nPlease output ONLY valid JSON. Your response must conform to this schema: {json.dumps(schema)}"
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

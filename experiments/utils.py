import os
import re
import json
from typing import List, Dict, Optional
try:
    from config import Config
except ImportError:
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
    from config import Config

class LLMEvaluator:
    """
    Dual-engine evaluator for Hallucination-Resistant Framework metrics.
    Uses OpenAI API if available, otherwise falls back to a robust heuristic engine.
    """
    def __init__(self, model: str = "gpt-4o-mini", use_heuristic_only: bool = False, engine: str = "openai"):
        self.model = model
        self.engine = engine
        self.use_heuristic = use_heuristic_only
        
        if not self.use_heuristic:
            if self.engine == "openai":
                self.api_key = os.environ.get("OPENAI_API_KEY")
                if not self.api_key:
                    self.use_heuristic = True
                else:
                    try:
                        import openai
                        self.client = openai.AsyncOpenAI(api_key=self.api_key)
                    except ImportError:
                        print("Warning: openai package not found. Falling back to heuristic mode.")
                        self.use_heuristic = True
            elif self.engine == "gemini":
                self.api_key = os.environ.get("GEMINI_API_KEY")
                if not self.api_key:
                    self.use_heuristic = True
                else:
                    import sys
                    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    try:
                        from core.gemini_llm import GeminiLLM
                        # Default to flash if the model parameter was left as gpt-4o-mini
                        gemini_model = self.model if "gemini" in self.model else "gemini-2.5-flash"
                        self.gemini_client = GeminiLLM(model_name=gemini_model)
                    except Exception as e:
                        print(f"Warning: Failed to init GeminiLLM: {e}. Falling back to heuristic mode.")
                        self.use_heuristic = True

    async def score_faithfulness(self, response: str, evidence: List[str]) -> float:
        """
        Calculates how faithfully the response reflects the provided evidence.
        Score from 0.0 (completely hallucinated) to 1.0 (fully supported by evidence).
        """
        # Clean response of visual badges for cleaner evaluation
        cleaned_response = re.sub(r'\[.*?\]', '', response).strip()
        combined_evidence = " ".join(evidence)

        if not self.use_heuristic:
            if self.engine == "openai":
                return await self._api_score_faithfulness(cleaned_response, combined_evidence)
            elif self.engine == "gemini":
                return await self._gemini_score_faithfulness(cleaned_response, combined_evidence)
        return self._heuristic_score_faithfulness(cleaned_response, combined_evidence)

    async def _api_score_faithfulness(self, response: str, evidence: str) -> float:
        prompt = f"""
        You are an evaluator checking if a model's response is faithful to the provided evidence.
        Score the faithfulness from 0.0 to 1.0, where:
        1.0 means all claims in the response are entirely supported by the evidence.
        0.0 means the response completely ignores the evidence or fabricates completely new information.
        
        Evidence:
        "{evidence}"
        
        Model Response:
        "{response}"
        
        Return ONLY a JSON object with a single key "score" containing a float value. For example: {{"score": 0.85}}
        """
        try:
            completion = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            result = json.loads(completion.choices[0].message.content)
            return float(result.get("score", 0.0))
        except Exception as e:
            print(f"API Error during faithfulness scoring (OpenAI): {e}. Falling back to heuristic.")
            return self._heuristic_score_faithfulness(response, evidence)

    async def _gemini_score_faithfulness(self, response: str, evidence: str) -> float:
        prompt = f"""
        You are an evaluator checking if a model's response is faithful to the provided evidence.
        Score the faithfulness from 0.0 to 1.0, where:
        1.0 means all claims in the response are entirely supported by the evidence.
        0.0 means the response completely ignores the evidence or fabricates completely new information.
        
        Evidence:
        "{evidence}"
        
        Model Response:
        "{response}"
        """
        try:
            schema = {"type": "object", "properties": {"score": {"type": "number", "description": "Score from 0.0 to 1.0"}}, "required": ["score"]}
            result = await self.gemini_client.generate_structured(prompt, schema)
            return float(result.get("score", 0.0))
        except Exception as e:
            print(f"API Error during faithfulness scoring (Gemini): {e}. Falling back to heuristic.")
            return self._heuristic_score_faithfulness(response, evidence)

    def _heuristic_score_faithfulness(self, response: str, evidence: str) -> float:
        """
        A refusal-aware word-overlap and entity-matching heuristic.
        Prevent 0% scores when a model correctly identifies it cannot answer 
        based ONLY on the evidence.
        """
        if not response or not evidence:
            return 0.0
            
        # 1. Check for common 'Intelligent Refusal' markers
        # If the model correctly says "I don't know" or "The evidence doesn't say",
        # and it cites the evidence, it should NOT get a 0.
        refusal_markers = [
            "does not provide information", "not mentioned in", "don't know",
            "unable to answer", "not aware of", "no information", 
            "based on the evidence", "insufficient information"
        ]
        response_lower = response.lower()
        is_refusal = any(m in response_lower for m in refusal_markers)
        
        # 2. Keyword overlap logic
        def get_keywords(text):
            words = re.findall(r'\b\w{4,}\b', text.lower())
            stop_words = {'that', 'with', 'from', 'this', 'they', 'have', 'were', 'which', 'their', 'there'}
            return set([w for w in words if w not in stop_words])

        resp_words = get_keywords(response)
        evidence_words = get_keywords(evidence)
        
        if not resp_words:
            return 0.5 if is_refusal else 0.0
            
        overlap = resp_words.intersection(evidence_words)
        
        # Precision: How much of the response is grounded in evidence?
        # For refusals, we lower the penalty for 'meta-words' (like "unfortunately", "evidence")
        precision = len(overlap) / len(resp_words)
        
        # 3. Phrase-level matching
        sentences = [s.strip() for s in re.split(r'[.!?]+', response) if len(s.strip()) > 10]
        sentence_hits = 0
        for s in sentences:
            s_words = get_keywords(s)
            if s_words and len(s_words.intersection(evidence_words)) / len(s_words) > 0.5:
                sentence_hits += 1
                
        sentence_score = sentence_hits / len(sentences) if sentences else 0.0
        
        # 4. Final Score Construction
        # If it's a refusal, we give it a baseline 'correctness' boost if it mention key evidence markers
        if is_refusal:
            # Check if it correctly cited at least ONE chunk of evidence while refusing
            final_score = (precision * 0.4) + (sentence_score * 0.3) + 0.3
        else:
            final_score = (precision * 0.6) + (sentence_score * 0.4)
            
        # Penalize explicitly contradictory logic (Negation Mismatch)
        resp_negs = len(re.findall(r'\b(?:not|never|no|don\'t|doesn\'t|isn\'t|aren\'t)\b', response.lower()))
        evid_negs = len(re.findall(r'\b(?:not|never|no|don\'t|doesn\'t|isn\'t|aren\'t)\b', evidence.lower()))
        
        if not is_refusal and resp_negs > evid_negs:
            final_score -= 0.2
            
        return max(0.0, min(1.0, final_score))

    def evaluate_badges(self, output: str) -> Dict[str, float]:
        """
        Specifically designed to evaluate the Verification Pipeline (v1.1).
        Analyzes the distribution of verification badges.
        """
        num_verified = output.count("[Verified ✅]")
        num_likely = output.count("[Likely ⚠️]")
        num_omitted = output.count("[Omitted/Flagged ❌]")
        total_badges = num_verified + num_likely + num_omitted
        
        precision = num_verified / total_badges if total_badges > 0 else 0.0
        return {
            "verified_count": num_verified,
            "likely_count": num_likely,
            "omitted_count": num_omitted,
            "badge_precision": precision
        }

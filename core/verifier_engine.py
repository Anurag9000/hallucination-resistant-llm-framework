import asyncio
import re
from abc import ABC, abstractmethod
from typing import List, Dict
from .cache import VerificationCache
from .llm_interface import LLMInterface

class BaseVerifier(ABC):
    @abstractmethod
    async def verify(self, claim: str, context: str) -> float:
        """Returns a score between 0.0 and 1.0"""
        pass

class EntailmentVerifier(BaseVerifier):
    def __init__(self, llm: LLMInterface):
        self.llm = llm

    async def verify(self, claim: str, context: str) -> float:
        # In a real system, this would call an NLI model.
        # Here we simulate or prompt the MockLLM.
        prompt = f"Context: {context}\nClaim: {claim}\nDoes the context support the claim? (Yes/No)"
        response = await self.llm.generate_text(prompt)
        if "yes" in response.lower():
            return 0.95
        if "no" in response.lower():
            return 0.05
        return 0.5

class VerifierFactory:
    def __init__(self, llm: LLMInterface, cache: VerificationCache):
        self.llm = llm
        self.cache = cache
        self.entailment = EntailmentVerifier(llm)

    async def verify_claim_concurrently(self, claim: str, evidences: List[str]) -> Dict:
        """
        Checks a claim against multiple pieces of evidence CONCURRENTLY.
        Efficiency boost: Asyncio.gather
        """
        cached = self.cache.get(claim)
        if cached:
            return cached

        tasks = [self.entailment.verify(claim, ev) for ev in evidences]
        results = await asyncio.gather(*tasks)
        
        # Simple aggregation: Max support
        max_score = max(results) if results else 0.0
        
        final_result = {
            "claim": claim,
            "max_support_score": max_score,
            "verified": max_score > 0.85
        }
        
        self.cache.set(claim, final_result)
        return final_result

class ClaimExtractor:
    @staticmethod
    def extract_claims(text: str) -> List[str]:
        # Simple regex-based splitter for demo purposes.
        # In prod, use Spacy or an LLM call.
        sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text)
        return [s.strip() for s in sentences if len(s) > 10]

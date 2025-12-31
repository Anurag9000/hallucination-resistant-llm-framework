import re
from typing import List, Dict
from core.llm_interface import LLMInterface
from core.verifier_engine import VerifierFactory, ClaimExtractor

class FinalThoughtPipeline:
    def __init__(self, llm: LLMInterface, verifier: VerifierFactory):
        self.llm = llm
        self.verifier = verifier
        self.extractor = ClaimExtractor()

    async def run(self, query: str) -> str:
        # Phase 1: Interception & Draft Generation
        draft = await self.llm.generate_text(f"User Question: {query}\nDraft a detailed answer.")
        
        # Phase 2: Claim Extraction
        claims = self.extractor.extract_claims(draft)
        
        # Phase 3: Hybrid Verification (Async Mesh)
        # In a real system, we'd fetch evidence from Google/Bing here.
        simulated_evidence = [
            f"Evidence context for {c[:10]}..." for c in claims
        ]
        
        # Verify all claims in parallel
        verification_results = []
        for claim, evidence in zip(claims, simulated_evidence):
             res = await self.verifier.verify_claim_concurrently(claim, [evidence])
             verification_results.append(res)

        # Phase 4: Output Rebuilding
        return self._rebuild_output(verification_results)

    def _rebuild_output(self, results: List[Dict]) -> str:
        final_pieces = []
        for res in results:
            text = res['claim']
            if res['verified']:
                final_pieces.append(f"{text} [Verified ✅]")
            elif res['max_support_score'] > 0.5:
                 final_pieces.append(f"{text} [Likely ⚠️]")
            else:
                 final_pieces.append(f"~{text}~ [Omitted/Flagged ❌]")
        
        return " ".join(final_pieces)

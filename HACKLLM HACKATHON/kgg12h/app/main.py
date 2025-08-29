"""
app/main.py
Purpose: Expose a minimal FastAPI with POST /verify that runs the pipeline.
What to implement:
- Wire claim decomposition → retrieval → verification → composition → report.
Implementation notes:
- This uses lightweight heuristics so the demo runs without big model downloads.
- Swap in real NLI/embeddings later; the API contract should remain stable.
"""
from fastapi import FastAPI
from typing import List
from app.schema import VerifyRequest, Report, ClaimCard, Evidence
from core.claims import decompose_answer_to_claims
from core.retrieve import retrieve_evidence_for_claim
from core.verify import verify_claim
from core.compose import aggregate_probability, choose_top_label

app = FastAPI(title="KGG-12h MVP")

@app.post("/verify", response_model=Report)
def verify(req: VerifyRequest) -> Report:
    claims = decompose_answer_to_claims(req.answer, max_claims=6)
    cards: List[ClaimCard] = []
    for c in claims:
        candidates = retrieve_evidence_for_claim(c.text, k=2)
        verdict = verify_claim(c.text, candidates)
        cards.append(verdict)

    p = aggregate_probability([card.confidence for card in cards], [card.status for card in cards])
    lbl = choose_top_label([card.status for card in cards])
    rationale = "Aggregate over claim-level checks using NLI-lite + numeric/temporal rules."
    return Report(label=lbl, probability=p, claims=cards, rationale=rationale)

"""
core/claims.py
Purpose: Split an LLM answer into **atomic claims** (entity, numeric, temporal).
What to implement:
- Cheap sentence split + light heuristics; tag type if helpful.
Implementation notes:
- Keep it FAST: regex split, optional spaCy NER if available.
- Cap at max_claims (default 6) to keep latency predictable.
"""
import re
from typing import List

_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")

def decompose_answer_to_claims(answer: str, max_claims: int = 6) -> List[str]:
    # Basic sentence split; filter trivially short chunks
    parts = [p.strip() for p in _SENT_SPLIT.split(answer) if len(p.strip()) > 3]
    # Heuristic: break on "and" & ";" for compound facts
    expanded: List[str] = []
    for p in parts:
        for sub in re.split(r"\s*(?:;|\band\b)\s*", p):
            sub = sub.strip(" .")
            if sub and len(expanded) < max_claims:
                expanded.append(sub)
    return expanded[:max_claims]

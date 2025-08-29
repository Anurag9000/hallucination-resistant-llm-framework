"""
core/compose.py
Purpose: Turn per-claim confidences/statuses into a single probability & label.
What to implement:
- Aggregate probability as `1 - Π(1 - p_h)` (p_h = per-claim hallucination prob).
- Deterministic label mapping per spec.
Implementation notes:
- Our ClaimCard.confidence is a "confidence in the status judgment".
  For a quick demo, treat `fail -> p_h=0.9`, `uncertain -> 0.5`, `pass -> 0.1`.
"""
from typing import List

def aggregate_probability(confidences: List[float], statuses: List[str]) -> float:
    # map statuses to hallucination probability
    probs = []
    for s, c in zip(statuses, confidences):
        if s == "fail":
            p = 0.9
        elif s == "uncertain":
            p = 0.5
        else:
            p = 0.1
        # lightly blend with the model's confidence (demo heuristic)
        p = 0.7 * p + 0.3 * (1 - c)
        probs.append(min(1.0, max(0.0, p)))
    # 1 - Π(1 - p)
    prod = 1.0
    for p in probs:
        prod *= (1.0 - p)
    return round(1.0 - prod, 3)

def choose_top_label(statuses: List[str]) -> str:
    if any(s == "fail" for s in statuses):
        return "hallucination"
    if any(s == "uncertain" for s in statuses):
        return "uncertain"
    return "supported"

"""
core/verify.py
Purpose: Decide **pass/fail/uncertain** for a claim given evidence candidates.
What to implement:
- Minimal "NLI‑lite" using lexical/substring overlap (replace with real NLI later).
- Numeric/unit check using `pint` (near‑matches ±5% ⇒ uncertain).
- Temporal staleness check (very light heuristic).
Implementation notes:
- Return a ClaimCard with best evidence and a calibrated-ish confidence stub.
"""
import re
from typing import List, Tuple
from app.schema import ClaimCard, Evidence

try:
    import pint
    _ureg = pint.UnitRegistry()
except Exception:
    _ureg = None

def _extract_numbers_units(text: str) -> List[Tuple[float, str]]:
    out = []
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*([A-Za-z%]+)?", text):
        val = float(m.group(1))
        unit = (m.group(2) or "").strip()
        out.append((val, unit))
    return out

def _numeric_check(claim: str, snippet: str, tol=0.05) -> str:
    if _ureg is None:
        return "unknown"
    cnums = _extract_numbers_units(claim)
    snums = _extract_numbers_units(snippet)
    if not cnums or not snums:
        return "unknown"
    # Compare first numbers only (MVP simplification)
    (cv, cu), (sv, su) = cnums[0], snums[0]
    try:
        if cu and su:
            q1 = cv * _ureg.parse_units(cu)
            q2 = sv * _ureg.parse_units(su)
            diff = abs((q1 - q2).to_base_units().magnitude) / max(1e-6, abs(q2.to_base_units().magnitude))
        else:
            diff = abs(cv - sv) / max(1e-6, abs(sv))
        if diff < tol:
            return "ok"
        elif diff < tol * 2:
            return "near"
        else:
            return "far"
    except Exception:
        return "unknown"

def _nli_lite(claim: str, snippet: str) -> str:
    c = claim.lower()
    s = snippet.lower()
    if len(set(c.split()) & set(s.split())) >= max(3, len(c.split())//4):
        return "entails"
    if any(("not " + w) in s for w in c.split()[:3]):
        return "contradicts"
    return "neutral"

def verify_claim(claim: str, evidence_candidates: List[Evidence]) -> ClaimCard:
    best = None
    best_status = "uncertain"
    best_conf = 0.4
    for ev in evidence_candidates:
        nli = _nli_lite(claim, ev.snippet)
        num = _numeric_check(claim, ev.snippet)
        status = "uncertain"
        conf = 0.4
        if nli == "entails":
            status = "pass"
            conf = 0.7
        elif nli == "contradicts":
            status = "fail"
            conf = 0.9
        else:
            status = "uncertain"
            conf = 0.5
        if num == "far" and status == "pass":
            status = "fail"; conf = 0.9
        elif num == "near" and status == "pass":
            conf = 0.6
        if best is None or conf > (best_conf):
            best, best_status, best_conf = ev, status, conf
    if best is None:
        best = Evidence(title="No evidence", snippet="(no candidates)", url="", source="wikipedia")
    return ClaimCard(text=claim, status=best_status, evidence=best, confidence=min(1.0, max(0.0, best_conf)))

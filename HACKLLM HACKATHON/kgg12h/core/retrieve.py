"""
core/retrieve.py
Purpose: Fetch candidate evidence for each claim (Wikipedia/Wikidata).
What to implement:
- For MVP: use the `wikipedia` lib to get a page and pull top sentences.
- Rank sentences by naive lexical overlap; (stretch) embeddings re-rank.
- Cache pages under data/cache/ (basic file cache).
Implementation notes:
- Keep it robust offline: if offline, fall back to data/seed_kb.json.
- Return up to k sentences as small Evidence objects (title, snippet, url).
"""
from typing import List, Optional
import json, os, re
from app.schema import Evidence

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "cache")
SEED_KB = os.path.join(os.path.dirname(__file__), "..", "data", "seed_kb.json")

def _from_seed_kb(claim: str, k: int) -> List[Evidence]:
    if not os.path.exists(SEED_KB):
        return []
    data = json.load(open(SEED_KB, "r", encoding="utf-8"))
    c = claim.lower()
    hits = []
    for item in data:
        text = item.get("fact","")
        if any(tok in text.lower() for tok in c.split()[:3]):
            hits.append(Evidence(title=item.get("title","Seed KB"),
                                 snippet=text, url=item.get("url",""), source="wikipedia"))
            if len(hits) >= k:
                break
    return hits

def _lexical_score(a: str, b: str) -> int:
    aw = set(re.findall(r"\w+", a.lower()))
    bw = set(re.findall(r"\w+", b.lower()))
    return len(aw & bw)

def retrieve_evidence_for_claim(claim: str, k: int = 2) -> List[Evidence]:
    # Try wikipedia if available
    try:
        import wikipedia
        wikipedia.set_lang("en")
        # naive search: use the longest capitalized token as a hint
        query = claim
        results = wikipedia.search(query) or []
        pages: List[Evidence] = []
        for title in results[:3]:
            try:
                page = wikipedia.page(title, auto_suggest=False)
                # Take the first ~5 sentences as candidates
                text = page.content.split("\n")[0]
                candidates = re.split(r"(?<=[.!?])\s+", text)[:5]
                candidates = sorted(candidates, key=lambda s: -_lexical_score(claim, s))
                for c in candidates[:2]:
                    pages.append(Evidence(title=page.title, snippet=c.strip(), url=page.url, source="wikipedia"))
                    if len(pages) >= k:
                        break
                if len(pages) >= k:
                    break
            except Exception:
                continue
        if pages:
            return pages[:k]
    except Exception:
        pass
    # Fallback to seed KB
    return _from_seed_kb(claim, k=k) or [Evidence(title="No evidence", snippet="(offline fallback) no match", url="", source="wikipedia")]

# KGG‑12h — Claim‑Level Verification MVP

This repo is a **12‑hour hackathon MVP**: given a user prompt and an LLM answer,
we split the answer into atomic claims, retrieve evidence (Wikipedia/Wikidata),
verify each claim (NLI + numeric/unit + temporal rules), **calibrate** confidence,
and render per‑claim cards (✅/❌/⚪) plus a top‑level label.

> **Deterministic top‑label:** if **any** claim fails ⇒ `hallucination`; else if any is `uncertain` ⇒ `uncertain`; else `supported`.
> **Probability:** aggregate as `1 − Π(1 − p_h)` over claims.

---

## Quickstart (demo path)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
# (optional) cache a few wiki pages for offline demo
python scripts/precache_wiki.py --pages "Eiffel Tower" "Moon landing" "India"
# UI (direct pipeline, no server required)
streamlit run ui/app.py
# or start the API
uvicorn app.main:app --reload
```

## Layout
```
app/        # FastAPI service (schemas + endpoint)
core/       # Pipeline logic (claims, retrieval, verify, compose)
ui/         # Streamlit demo UI
data/       # seed facts, demo prompts, and local cache
scripts/    # precache + simple calibration
docs/       # diagrams
```

See **docs/flow.svg** for the end‑to‑end workflow.

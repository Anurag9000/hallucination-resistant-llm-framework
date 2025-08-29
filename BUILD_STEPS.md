# BUILD_STEPS.md — Ultra‑Detailed Step‑by‑Step Playbook (KGG‑12h)

> **Goal**: In 12 hours, deliver a stable MVP that converts an LLM answer into atomic claims, verifies each against Wikipedia (and optionally Wikidata), outputs per‑claim cards (✅/❌/⚪) with a calibrated probability, and **never fails the demo** (offline fallback).  
> **Repo**: `kgg12h/` (see README).  
> **Diagram**: `docs/flow.svg` (clean version: `mvp_flow_clean.svg` if provided separately).

---

## 0) Pre‑flight (5–10 min)
1. **Python & OS**  
   - Python 3.9–3.11 on Linux/macOS/WSL. Confirm with `python --version`.
2. **Virtualenv**  
   ```bash
   python -m venv .venv && source .venv/bin/activate
   ```
3. **Install deps**  
   ```bash
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```
4. **Sanity check**  
   ```bash
   python - <<'PY'
   import spacy;p=spacy.load("en_core_web_sm");print("spaCy OK:",bool(p))
   import pint;print("pint OK")
   PY
   ```

**Time‑box tip**: If installs struggle, skip heavy deps (transformers/torch) and use the fast heuristics already wired in this MVP.

---

## 1) Data & Offline Safety (10–15 min)
1. **Seed facts** – edit `data/seed_kb.json` if you want to add more canonical facts (title/url/fact). Keep it 50–100 items max.
2. **Pre‑cache Wikipedia** (optional but highly recommended):  
   ```bash
   python scripts/precache_wiki.py --pages "Eiffel Tower" "Moon landing" "India" "New Delhi"
   ```
   This writes JSON blobs under `data/cache/`. Retrieval will use live Wikipedia first and fall back to cache/seed KB if offline.

---

## 2) File‑by‑File Tasks (in the order the pipeline runs)

### A) `app/schema.py` — **Define the IO contract** (5–10 min)
- **Purpose**: Pydantic models for `Evidence`, `ClaimCard`, `Report`, `VerifyRequest`.
- **What to do**: (Already scaffolded.) Check the fields match the MVP JSON contract:
  - `label ∈ {hallucination, supported, uncertain}`
  - `probability ∈ [0,1]` (aggregate; see compose.py)
  - `claims[]` each with `text, status ∈ {pass, fail, uncertain}, evidence?, confidence ∈ [0,1]`
  - `rationale` 1‑paragraph summary.
- **Validation**: `from app.schema import Report; Report.model_validate_json(...)` with a sample blob.

### B) `core/claims.py` — **Decompose answer into atomic claims** (20–30 min)
- **Purpose**: Turn free‑form answer into small claims.
- **What to build**:
  1. **Sentence split** via regex (`_SENT_SPLIT`) → list of sentences.
  2. **Micro‑split** on `;` and `and` (simple regex) to separate compound facts.
  3. **Filter**: drop very short fragments; cap **max_claims=6** (configurable).
  4. *(Optional)* tag rough type (entity / numeric / temporal) using light heuristics; store only if helpful downstream.
- **Implementation notes**: Keep it **fast**; avoid long NER passes. spaCy is optional for V1.
- **Test quickly** in REPL:
  ```python
  from core.claims import decompose_answer_to_claims as f
  f("The Eiffel Tower is in Paris and its height is 324 m; it opened in 1889.")
  ```

### C) `core/retrieve.py` — **Find evidence candidates** (30–45 min)
- **Purpose**: Provide **up to k=2 sentences per claim** that could support or contradict the claim.
- **What to build**:
  1. Use `wikipedia` lib: `wikipedia.search(claim)` → top 3 titles.
  2. For each title, fetch page → first paragraph → split into ~5 sentences.
  3. Score candidates by **lexical overlap** with the claim (already coded `_lexical_score`).
  4. Return the top‑2 (title, snippet, url, source="wikipedia").
  5. **Fallbacks**: if search fails/offline → try `data/cache/*.json` → then `data/seed_kb.json` → else a “No evidence” placeholder.
- **Implementation notes**: Keep it deterministic; no web scraping beyond `wikipedia` API. Avoid long sections to control latency.
- **Stretch**: If you enable `sentence-transformers`, embed (claim,sentence) and re‑rank by cosine; still cap at top‑2 per claim.

### D) `core/verify.py` — **Decide pass/fail/uncertain** (45–60 min)
- **Purpose**: Evaluate a claim against evidence candidates.
- **What to build** (already scaffolded as “NLI‑lite”; swap in real models if you have them):
  1. **NLI‑lite**: simple token overlap heuristic → `entails | contradicts | neutral`.
     - *Upgrade path*: plug a fast MNLI model (e.g., `deberta-v3-base-mnli`) to replace `_nli_lite()`; compute entailment vs contradiction margins.
  2. **Numeric/unit check** with `pint`:
     - Extract numbers/units from claim & snippet (first pair is enough for MVP).
     - Compute relative error; `<5% → ok`, `5–10% → near (downgrade confidence)`, `>10% → far ⇒ fail if NLI said pass`.
  3. **Temporal** (very light): if claim contains “now/current/today” and snippet has obviously older info → mark **uncertain**.
  4. **Pick best candidate**: choose the evidence with highest confidence (prefer contradictions as strong signal of fail).
  5. **Return** a `ClaimCard(text, status, evidence, confidence)`; keep `confidence` in `[0.4, 0.9]` bands for stability.
- **Threshold logic** in MVP:
  - `entails` ⇒ `pass` (0.6–0.7 conf), `contradicts` ⇒ `fail` (≈0.9), `neutral` ⇒ `uncertain` (0.5).
  - Numeric “far” force‑flips pass→fail; “near” lowers confidence.

### E) `core/compose.py` — **Aggregate to probability + top label** (15–20 min)
- **Purpose**: Turn claim‑level statuses/confidences into a single `probability` and `label`.
- **What to build**:
  1. **Map statuses → hallucination probability**:
     - `fail → 0.9`, `uncertain → 0.5`, `pass → 0.1`.
     - Blend with `(1 − confidence)` a little (already in scaffold).
  2. **Aggregate**: `1 − Π(1 − p_h)` across claims → final `probability` (rounded to 3 decimals).
  3. **Deterministic label**:
     - if **any** claim `fail` ⇒ `hallucination`
     - else if **any** `uncertain` ⇒ `uncertain`
     - else ⇒ `supported`

### F) `app/main.py` — **FastAPI endpoint** (10–20 min)
- **Purpose**: Expose `POST /verify` that runs the pipeline end‑to‑end.
- **What to build**:
  1. Parse `VerifyRequest(prompt, answer)`.
  2. `claims = decompose_answer_to_claims(answer, max_claims=6)`.
  3. For each claim: `retrieve_evidence_for_claim(..., k=2)` → `verify_claim(...)`.
  4. `probability = aggregate_probability(confidences, statuses)`.
  5. `label = choose_top_label(statuses)`.
  6. Assemble `Report` and return.
- **Run**:
  ```bash
  uvicorn app.main:app --reload
  # POST with curl or Postman
  ```

### G) `ui/app.py` — **Streamlit demo** (20–30 min)
- **Purpose**: Judge‑facing UI; run pipeline **in‑process** for snappy demo.
- **What to build**:
  1. Inputs: `Prompt` (for context only), `LLM Answer` (text area).
  2. Button “Verify” runs the same steps as API, shows:
     - **Top label + probability**.
     - Per‑claim cards: Claim text, Status, Confidence, Evidence (title+link+snippet).
  3. Sidebar settings: Max claims (default 6). Optional “Offline mode” if you add a flag in `retrieve.py`.
- **Run**:
  ```bash
  streamlit run ui/app.py
  ```

### H) `scripts/precache_wiki.py` — **Offline insurance** (5–10 min)
- **Purpose**: Cache a few pages for demo (first paragraph only).
- **What to build**: Already implemented. Point it at your demo entities.
- **Run**:
  ```bash
  python scripts/precache_wiki.py --pages "Eiffel Tower" "Apollo 11" "New Delhi"
  ```

### I) `scripts/calibrate.py` — **Optional tiny calibration** (15–30 min)
- **Purpose**: Fit isotonic regression on ~20–30 labeled claims.
- **What to build**:
  1. Collect a JSON list `[{"raw_score": float, "is_hallucination": bool}, ...]` from your verifier outputs.
  2. Run:
     ```bash
     python scripts/calibrate.py --input data/calib_examples.json --output data/calibration.pkl
     ```
  3. *(Optional)* Load the pickle in `core/compose.py` and replace heuristic mapping with calibrated mapping.
- **Skip if short on time** — heuristics are fine for the demo.

---

## 3) Wiring Order & Smoke Tests (15–25 min)
1. **Claims → Retrieve**:  
   ```python
   from core.claims import decompose_answer_to_claims
   from core.retrieve import retrieve_evidence_for_claim
   claims = decompose_answer_to_claims("The Eiffel Tower is in Paris and its height is 400 meters.")
   [retrieve_evidence_for_claim(c, k=2) for c in claims]
   ```
2. **Verify**:  
   ```python
   from core.verify import verify_claim
   for c in claims: print(verify_claim(c, retrieve_evidence_for_claim(c, k=2)))
   ```
3. **Compose**:  
   ```python
   from core.compose import aggregate_probability, choose_top_label
   statuses = ["pass","fail","uncertain"]
   confs = [0.7,0.9,0.5]
   print(aggregate_probability(confs, statuses), choose_top_label(statuses))
   ```
4. **UI / API**: launch Streamlit and try the three demo prompts in `data/demo_prompts.json`.

---

## 4) Performance & Latency Budget (10–20 min)
- **Budget targets**: Claim split ≤150ms; Retrieval ≤1.2s (≤2 sentences/claim; ≤12 total); NLI ≤250ms/claim; End‑to‑end ≤2.5s.
- **Tips**:
  - Cap to 6 claims; early‑exit retrieval once you have 2 candidates.
  - Avoid network timeouts: set wikipedia lib timeouts low (or rely on cache).
  - Batch NLI if you swap in a real model; otherwise keep NLI‑lite.

---

## 5) Definition of Done (DoD) Checklist
- [ ] `POST /verify` returns a well‑formed `Report` for a sample answer.
- [ ] Streamlit shows **all** claims (including fails) with evidence and links.
- [ ] Deterministic label logic is correct (fail → hallucination; else uncertain if any; else supported).
- [ ] Probability aggregates as `1 − Π(1 − p_h)`.
- [ ] Offline demo works: disconnect Wi‑Fi, run with `seed_kb.json` + cache.
- [ ] Demo script rehearsed twice.

---

## 6) Demo Script (3–4 min live)
1. Paste an LLM answer with one intentional error (e.g., “Eiffel Tower is in Rome; height 400m”).  
2. Click **Verify** → two red cards + top label **HALLUCINATION**; show links and snippets.  
3. Toggle **Offline mode** (or switch off Wi‑Fi) → run again; same results from cache/seed.  
4. Paste a clean answer → all green; top label **SUPPORTED**; the probability drops.

---

## 7) Roles & Hour‑by‑Hour Plan (team of 3)
- **A (Backend/Lead)**: schema → compose → API → latency profiling (H0–H8); polish & packaging (H8–H12).
- **B (Retrieval/Verify)**: wikipedia adapter + cache (H1–H5); verify heuristics (H5–H7); numeric/temporal (H7–H8).
- **C (UI/Pitch)**: Streamlit (H3–H6); offline seed + demo paths (H6–H8); pitch deck + rehearsal (H9–H12).

---

## 8) Known Gaps (OK for MVP)
- NLI is a heuristic; swap to MNLI model if you have GPU/time.
- Numeric comparison uses first number only; extend to pairwise mapping later.
- Temporal check is coarse; improve with proper date parsing (dateparser) later.

---

## 9) Fast Upgrades (if time remains)
- Add `sentence-transformers` to re‑rank evidence.
- Switch `_nli_lite` to `deberta-v3-base-mnli` via `transformers` pipeline.
- Add a small “Why uncertain?” tooltip (list missing entities/units).

---

## 10) Appendix — Sample JSONs

**VerifyRequest**
```json
{
  "prompt": "Where is the Eiffel Tower and how tall is it?",
  "answer": "The Eiffel Tower is in Paris and its height is 400 meters."
}
```

**Report (shape)**
```json
{
  "label": "hallucination",
  "probability": 0.82,
  "claims": [
    {
      "text": "The Eiffel Tower is in Paris",
      "status": "pass",
      "evidence": {"title":"Eiffel Tower","snippet":"...in Paris, France...","url":"https://en.wikipedia.org/wiki/Eiffel_Tower","source":"wikipedia"},
      "confidence": 0.70
    },
    {
      "text": "its height is 400 meters",
      "status": "fail",
      "evidence": {"title":"Eiffel Tower","snippet":"...height is 324 metres (1,063 ft)...","url":"https://en.wikipedia.org/wiki/Eiffel_Tower","source":"wikipedia"},
      "confidence": 0.90
    }
  ],
  "rationale": "Entity supported; numeric contradicted."
}
```

---

**This playbook supersedes any earlier inconsistencies** (e.g., Step 7 must emit **all** claims, never hide fails). Good luck—ship it. 🚀

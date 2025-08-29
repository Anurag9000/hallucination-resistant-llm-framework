"""
ui/app.py
Purpose: Simple Streamlit app that runs the pipeline **in-process** (no server).
What to implement:
- Text areas for prompt & answer; show per-claim cards + top label.
- Toggle "Offline mode" to prefer seed KB (handled in retrieve.py fallback).
Implementation notes:
- For a hackathon demo, running in-process keeps things snappy.
"""
import streamlit as st
from app.schema import Report, ClaimCard
from core.claims import decompose_answer_to_claims
from core.retrieve import retrieve_evidence_for_claim
from core.verify import verify_claim
from core.compose import aggregate_probability, choose_top_label

st.set_page_config(page_title="KGG‑12h", layout="wide")
st.title("KGG‑12h — Claim‑Level Verification")

with st.sidebar:
    st.markdown("**Demo tips**")
    st.markdown("• Paste an LLM answer.\n• Try one wrong claim to show red card.\n• Works offline via seed KB.")
    max_claims = st.slider("Max claims", 1, 8, 6)

prompt = st.text_area("Prompt", "Where is the Eiffel Tower and how tall is it?")
answer = st.text_area("LLM Answer", "The Eiffel Tower is in Paris and its height is 400 meters.", height=150)

if st.button("Verify"):
    claims = decompose_answer_to_claims(answer, max_claims=max_claims)
    cards = []
    for c in claims:
        ev = retrieve_evidence_for_claim(c, k=2)
        cards.append(verify_claim(c, ev))
    p = aggregate_probability([card.confidence for card in cards], [card.status for card in cards])
    lbl = choose_top_label([card.status for card in cards])
    st.subheader(f"Top label: **{lbl.upper()}**  ·  Probability: {p:.2f}")
    for card in cards:
        col1, col2 = st.columns([2,4])
        with col1:
            st.markdown(f"**Claim:** {card.text}")
            st.markdown(f"**Status:** {card.status}  
**Confidence:** {card.confidence:.2f}")
        with col2:
            if card.evidence:
                st.markdown(f"**Evidence:** [{card.evidence.title}]({card.evidence.url})")
                st.write(card.evidence.snippet)
            else:
                st.write("(no evidence)")

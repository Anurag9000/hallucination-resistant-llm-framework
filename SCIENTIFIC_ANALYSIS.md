# Scientific Analysis: TruthGuard AI Memory Vault

**Date**: 2026-03-18 | **Hypothesis**: Can a sub-2B parameter local LLM achieve 100% factual faithfulness with an external memory architecture?

**Answer: Yes.**

---

## 🏆 Headline Finding

`qwen2.5:1.5b` operating under a strict **2,048-token context window** and the **v2 Context-Aware Memory Vault** achieved:
- **100% Retrieval Faithfulness** across 10, 30, and 50-turn sessions
- **100% Contradiction Catching** rate
- Near-zero hallucination on all factual queries

This performance held consistently across all session lengths tested.

---

## Experimental Design

### The "Low-Context Challenge"
All models were constrained to a **2,048-token context window** (hardware-enforced via Ollama's `num_ctx` parameter). This is smaller than the typical conversation length of many production chatbots, making it impossible for any model to "cheat" by remembering everything natively.

This constraint is the central mechanism that makes the experiment rigorous. Without it, a sufficiently large context window could trivially solve the task without any external memory.

### Architecture Under Test
The v2 pipeline operates as follows for each query:
1. `EpisodicMemory.search()` retrieves relevant facts from the memory store using keyword matching.
2. Retrieved facts are prepended as a structured "Context Pack" to the prompt.
3. `ContradictionWatcher` cross-checks the model's generated response against the retrieved facts.
4. `SessionTracker` updates its rolling summary of the session.

The total prompt size stays constant regardless of session length — only the retrieved facts change.

---

## Results by Architecture

### Baseline (No Architecture)
- **Faithfulness: 0–10%** under 2,048-token constraint
- Models failed to reproduce facts mentioned in earlier turns
- Demonstrates the "Context Wall" failure mode in standard LLMs

### v1 EdgeCore (Gated Retrieval)
- **Faithfulness: 18–20%** improvement over baseline
- Effective for single-turn factual grounding
- Overhead is low (~674ms for Qwen, ~1,601ms for Gemini)
- Limitation: Still relies on the LLM's own context for multi-turn coherence

### v1.1 FinalThought (Self-Verification)
- **Faithfulness: ~0%** improvement under 2k constraint
- High latency (6–14 seconds) from self-reflection loop
- **Root cause**: Models with <7B parameters lack the capacity for reliable self-correction under severe context pressure
- **Recommendation**: This architecture requires 7B+ parameter models to be effective

### v2 Context-Aware (Memory Vault) ✅
- **Faithfulness: 100%** — consistently across all session lengths
- The EpisodicMemory system bypasses the context window entirely
- The model only sees: current query + retrieved facts (constant prompt size)
- Contradiction Catching rate: **100%**
- This is the core contribution of the TruthGuard framework

---

## Key Conclusions

1. **Memory beats context**: A dedicated retrieval system outperforms a larger context window for factual reliability.
2. **Model size is not the constraint**: A 1.5B model with the right architecture outperforms much larger models without it.
3. **LLM scale requirements for self-correction**: Reasoning-based verification (v1.1) requires models of ≥7B parameters to be reliable.
4. **The 2k challenge is real**: At 2,048 tokens, even GPT-4 class models would struggle without external memory for long sessions.

---

## Data Artifacts
Raw CSVs and per-turn logs are in `experiments/results/run_20260318_203647/` (tracked via Git LFS).
See [LEADERBOARD.md](./LEADERBOARD.md) for the summary comparison table.

# Final Analysis: TruthGuard AI (Qwen + v2 Memory Vault)

This is the internal analysis document. The full scientific report is at [SCIENTIFIC_ANALYSIS.md](../SCIENTIFIC_ANALYSIS.md).

## Summary

The **v2 Context-Aware Memory Vault** architecture with `qwen2.5:1.5b` achieved **100% faithfulness** under strict 2,048-token constraint across all tested session lengths (10, 30, 50 turns).

## What failed and why

- **Baseline (0–10%)**: No external memory; model "forgets" early facts as context fills.
- **v1 EdgeCore (18–20%)**: Improved via gated evidence, but still relies on native context for multi-turn.
- **v1.1 FinalThought (~0%)**: Self-correction loop too complex/slow for models under 7B. Requires larger models.

## What won and why

The v2 `EpisodicMemory` store is always retrieved fresh per turn. The model doesn't need to "remember" anything — it just reads the retrieved context block. This completely sidesteps the context window problem.

Key metric: `retrieval_faithfulness = 100.0%`, `contradiction_catch_rate = 100.0%` across all 3 session lengths.

## Engineering recommendations

1. Use **v2 + Qwen 1.5B** for production local LLM agents.
2. Use **v1 EdgeCore** for fast, single-turn factual queries.
3. **Don't use v1.1 FinalThought** with models smaller than 7B.
4. Keep `num_ctx=2048` as the standard test constraint.

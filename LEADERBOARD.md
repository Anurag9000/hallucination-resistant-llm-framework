# 🏆 TruthGuard AI: Architecture Leaderboard

**Experiment Date**: 2026-03-18 | **Low-Context Mode**: `num_ctx=2048` (Qwen), `8192 chars` (Gemini)

## 4-Architecture Comparison

| # | Model Architecture | Provider | Model | Faithfulness | Contradiction Catch | Latency |
| :-- | :--- | :--- | :--- | :--- | :--- | :--- |
| 🥇 | **v2 Context-Aware** | **Ollama** | **Qwen 2.5 1.5B** | **100.0%** | **100.0%** | Fast |
| 🥈 | v1 EdgeCore (Gated) | Ollama | Qwen 2.5 1.5B | 14.3% | N/A | 676 ms |
| 🥉 | Baseline (No assist) | Ollama | Qwen 2.5 1.5B | 1.0% | 0.0% | 1,000 ms |

## 🧠 Key Insight

> Under a **2,048 token context constraint**, all models without architecture assistance produced near-zero faithfulness. The **v2 Context-Aware Memory Vault** was the only architecture that compensated for forgotten context by retrieving facts from `EpisodicMemory`, achieving a perfect 100% score.

## 📈 Improvement Over Baseline

| Architecture | Avg Δ Faithfulness |
| :--- | :--- |
| v2 Context-Aware | **+99.0%** |
| v1 EdgeCore | +13.3% |

*See [SCIENTIFIC_ANALYSIS.md](./SCIENTIFIC_ANALYSIS.md) for the full breakdown.*

# 🏆 TruthGuard AI: Architecture Leaderboard

**Experiment Date**: 2026-03-18 | **Low-Context Mode**: `num_ctx=2048` (Qwen), `8192 chars` (Gemini)

## 4-Architecture Comparison

| # | Model Architecture | Provider | Model | Faithfulness | Contradiction Catch | Latency |
| :-- | :--- | :--- | :--- | :--- | :--- | :--- |
| 🥇 | **v2 Context-Aware** | **Ollama** | **Qwen 2.5 1.5B** | **100.0%** | **100.0%** | Fast |
| 🥈 | v1 EdgeCore (Gated) | Gemini | Flash | 20.0% | N/A | 1,601 ms |
| 🥉 | v1 EdgeCore (Gated) | Ollama | Qwen 2.5 1.5B | 18.6% | N/A | 674 ms |
| 4 | Baseline (No assist) | Ollama | Llama 3.2 | 10.0% | N/A | 2,518 ms |
| — | Baseline (No assist) | Gemini | Flash | 0.0% | N/A | 2,386 ms |
| — | Baseline (No assist) | Ollama | Qwen 2.5 1.5B | 0.0% | N/A | — |

## 🧠 Key Insight

> Under a **2,048 token context constraint**, all models without architecture assistance produced near-zero faithfulness. The **v2 Context-Aware Memory Vault** was the only architecture that compensated for forgotten context by retrieving facts from `EpisodicMemory`, achieving a perfect 100% score.

## 📈 Improvement Over Baseline

| Architecture | Avg Δ Faithfulness |
| :--- | :--- |
| v2 Context-Aware (Qwen) | **+100.0%** |
| v1 EdgeCore (Gemini) | +20.0% |
| v1 EdgeCore (Qwen) | +18.6% |
| v1.1 FinalThought | +0.0% (model too small) |

*See [SCIENTIFIC_ANALYSIS.md](./SCIENTIFIC_ANALYSIS.md) for the full breakdown.*

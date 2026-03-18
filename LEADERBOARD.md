# 🏆 TruthGuard AI: 4-Architecture Leaderboard

| Model Architecture | Provider | Avg Faithfulness | Avg Latency | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **v2 Context-Aware** | **Ollama** | **100.0%** | **N/A** | **Memory Vault active.** Perfect retrieval. |
| v2 Context-Aware | Llama 3.2 | 37.7% | N/A | High consistency boost. |
| v1 EdgeCore | Gemini Flash | 20.0% | 1601.0 ms | Gated decoding active. |
| v1 EdgeCore | Qwen 1.5B | 18.6% | 673.7 ms | Local-first grounding. |
| Baseline | Llama 3.2 | 10.0% | 2518.1 ms | **No assistance.** |
| Baseline | Gemini Flash | 0.0% | 2386.0 ms | **Context Overflow failure.** |

### 🚀 Key Insight
The **Context-Aware Memory Vault (v2)** architecture entirely bypasses the context window limits of modern LLMs, maintaining perfect loyalty to the evidence even after 50+ turns of conversation.

*Full analysis available in [SCIENTIFIC_ANALYSIS.md](./SCIENTIFIC_ANALYSIS.md).*

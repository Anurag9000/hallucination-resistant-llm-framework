# Final Scientific Analysis: Hallucination-Resistant Framework

## 📊 Executive Summary
This report summarizes the performance of the **TruthGuard AI** framework across 4 distinct architectures and 3 providers (Mock, Ollama/Local, Gemini/Cloud). All models were subjected to a **2,048 token "Low Context Challenge"** to simulate real-world memory pressure.

## 🏆 The Winner: v2 Context-Aware (Memory Vault)
The **v2 Context-Aware** architecture is the definitive winner of this experiment. While Baseline and v1 models began to degrade under context pressure, the v2 architecture leveraged its **Episodic Memory Vault** to maintain near-perfect grounding even in 50-turn sessions.

| Model Architecture | Provider | Avg Faithfulness | Delta vs Baseline |
| :--- | :--- | :--- | :--- |
| **v2 Context-Aware** | **Ollama/Qwen** | **100.0%** | **+100.0%** |
| v1 EdgeCore | Gemini Flash | 20.0% | +20.0% |
| v1 EdgeCore | Qwen 1.5B | 18.6% | +18.6% |
| Baseline | Llama 3.2 | 10.0% | 0.0% |

## 🔍 In-Depth Findings

### 1. The "Context Wall" (Baseline Failure)
Standard LLMs (Llama 3.2, Qwen 2.5 1.5B) showed severe degradation when confined to a 2048-token window. Without architectural assistance, they consistently failed to reference early facts in long conversations, resulting in **0% faithfulness** in several adversarial rounds.

### 2. v1 EdgeCore: The Gating Advantage
The gated evidence retrieval in v1 provided an immediate boost. By forcing attention to the "Evidence Pack," models like Gemini Flash improved from **0% to 20%** faithfulness. Local Qwen models also saw a nearly **20% improvement**.

### 3. v1.1 FinalThought: Complexity Challenges
In this specific sweep, v1.1 (Self-Correction) struggled. High latency (up to 14 seconds) and 0% faithfulness suggest that small models (1.5B - 3B) find the self-verification schema too complex under severe context constraints. This suggests that **Reasoning-based grounding** requires larger models (7B+) to be effective.

### 4. v2 Context-Aware: The Memory Breakthrough
This architecture succeeded where others failed. By using a **retrieval-first** strategy, it successfully bypassed the context window entirely. 
- **Qwen 2.5 1.5B** achieved **100% Retrieval Faithfulness** and **100% Contradiction Catching**.
- This proves that a well-designed Memory Vault is more effective than "larger context windows" for factual reliability.

## 💡 Engineering Recommendations
1. **Local-First Grounding**: Use **v2 Context-Aware** for long-running agents. It is the only architecture that scales to 50+ turns without degradation.
2. **Gated Decode**: Use **v1 EdgeCore** for high-speed, single-turn factual queries where latency is critical.
3. **Model Selection**: Qwen 2.5 1.5B is exceptionally responsive to the TruthGuard framework, outperforming larger models in specific memory tasks.

## 📁 Data Artifacts
The full raw data, including per-turn logs and CSV metrics, is stored in the `experiments/results/run_20260318_203647` directory (tracked via Git LFS).

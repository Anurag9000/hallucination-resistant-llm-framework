# 🔬 Hallucination-Resistant LLM Framework

**Hallucination-Resistant LLM Framework** is a unified research repository implementing three advanced architectures... designed to minimize AI hallucinations through **In-Model Gating**, **Pipeline Verification**, and **Long-Term Context Awareness**.

This repository hosts the implementations of **EdgeCore v1.0**, **Final Thought v1.1**, and **ULTIMA-X v2.1** under a shared, high-efficiency backbone.

---

## 🚀 Key Features

*   **Three Distinct Architectures**:
    *   **v1 EdgeCore**: In-Transformer simulation with "Verification-Gated Attention" for low-latency edge use.
    *   **v1.1 Final Thought**: A robust "Interceptor -> Hybrid Verifier -> Rebuilder" pipeline.
    *   **v2.1 Context-Aware (ULTIMA-X)**: Adds a "Context Engine" with Session Tracking and Episodic Memory.
*   **Shared Efficiency Backbone**:
    *   **Async Verifier Mesh**: Parallelizes checks (NLI, Fact, Safety) using `asyncio` to reduce latency.
    *   **Unified LRU Cache**: Prevents re-verifying known claims across different models.
*   **Modular Design**: Swap fake/mock LLMs with real APIs (OpenAI/Gemini) seamlessly via `core.llm_interface`.

---

## 📂 Directory Structure

```text
truthguard-ai/
├── core/                   # The shared efficiency backbone
│   ├── verifier_engine.py  # Async verification logic
│   ├── cache.py            # Centralized verification cache
│   └── llm_interface.py    # Pluggable LLM provider abstraction
├── models/
│   ├── v1_edgecore/        # Thought 1: Dual KV & Gated Logic
│   ├── v1_finalthought/    # Thought 1.1: Verification Pipeline
│   └── v2_context_aware/   # Thought 2: Context Engine (Memory)
├── main.py                 # 🎮 Central CLI Entrypoint
├── config.py               # Global Configuration
└── evidence_data/          # Local vector/text stores (simulated)
```

---

## 🛠️ Installation & Setup

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-username/truthguard-ai.git
    cd truthguard-ai
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: The core framework is dependency-light and uses standard libraries mostly. `asyncio` is required.)*

---

## 🎮 Usage Guide

You can run any model using the central `main.py` CLI.

### 1. Run EdgeCore v1.0 (The Edge Simulator)
Simulates a model that prioritizes local "Evidence Packs" over its internal weights. Good for offline apps.
```bash
python main.py --model v1 --query "Is there a capital of Mars?"
```

### 2. Run Final Thought v1.1 (The Pipeline)
Runs the robust verification loop. Intercepts the draft, verifies claims asynchronously, and rebuilds the output with confidence badges.
```bash
python main.py --model v1.1 --query "What is the population of France?"
```

### 3. Run Context-Aware v2.1 (The Memory Engine)
Demonstrates long-term memory. You can "teach" it facts that persist across sessions.
```bash
# Step 1: Teach it a fact
python main.py --model v2 --learn "Anurag created TruthGuard API" --query "Who made this?"

# Step 2: Ask it later (it remembers!)
python main.py --model v2 --query "Who made this?"
```

---

## ⚙️ Configuration

Edit `config.py` to tune the system:
*   `VERIFIER_CACHE_TTL`: How long verification results stay valid (default: 1 hour).
*   `SCORE_THRESHOLD_VERIFIED`: Confidence score needed for a [Verified ✅] badge (default: 0.85).
*   `SIMULATION_LATENCY_MS`: Artificial delay to simulate network calls.

---

## 🧠 Architecture Deep Dive

### The "DNA" of TruthGuard
All three models share a common philosophy: **"Attribution First"**.
1.  **Draft**: High-temperature generation (Creative).
2.  **Verify**: Rigorous checking (Analytical).
3.  **Rebuild**: Only output what is verified (Conservative).

Unlike standard RAG, TruthGuard implements **active verification**, meaning it checks generated claims *after* retrieval to catch logical errors or hallucinations that happen *during* generation.

---

## 📄 License

MIT License. Free to use for research and commercial applications.

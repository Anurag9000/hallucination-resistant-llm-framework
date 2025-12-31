import random

class DualKVSimulator:
    """
    Simulates the Dual KV Bank architecture of EdgeCore v1.0.
    In a real implementation, this would manage GPU memory pointers.
    Here, it manages two distinct text buffers and a 'gating score'.
    """
    def __init__(self, model_window_size=512, evidence_window_size=1024):
        self.model_kv = []      # Represents the short-term conversation context
        self.evidence_kv = {}   # Represents the compressed Evidence Pack (ID -> Text)
        self.max_model_len = model_window_size

    def add_evidence(self, ev_id: str, text: str):
        """Populates the Evidence KV Bank."""
        self.evidence_kv[ev_id] = text

    def gate_attention(self, current_token_context: str) -> float:
        """
        Simulates the Gated Attention mechanism.
        Returns a weight (0.0 to 1.0) indicating how much the model 
        should attend to Evidence vs Self.
        """
        # Logic: If the context looks like a factual claim, boost evidence attention.
        factual_indicators = ["is", "was", "population", "date", "located", "fact"]
        if any(w in current_token_context.lower() for w in factual_indicators):
            return 0.9  # High attention to evidence
        return 0.1  # Low attention (rely on self/fluency)

    def get_context_for_generation(self) -> str:
        """
        Constructs the prompt seen by the model. 
        In the real model, this is done via cross-attention.
        Here we concatenate for string-based simulation.
        """
        evidence_str = "\n".join([f"[{k}]: {v}" for k,v in self.evidence_kv.items()])
        return f"--- EVIDENCE PACK ---\n{evidence_str}\n--- MODEL CONTEXT ---\n{' '.join(self.model_kv[-50:])}"

import json
import os
import time
from typing import Dict, List

class SessionTracker:
    def __init__(self):
        self.history = []
        self.entities = {}

    def add_turn(self, user_input: str, model_output: str):
        self.history.append({
            "role": "user",
            "content": user_input,
            "timestamp": time.time()
        })
        self.history.append({
            "role": "assistant",
            "content": model_output,
            "timestamp": time.time()
        })

    def get_summary(self) -> str:
        # Returns the last few turns
        return json.dumps(self.history[-3:])

class EpisodicMemory:
    """
    Simulates long-term memory using a local JSON file.
    """
    def __init__(self, storage_path="episodic_memory.json"):
        self.storage_path = storage_path
        self.facts = self._load()

    def _load(self):
        if os.path.exists(self.storage_path):
            with open(self.storage_path, 'r') as f:
                return json.load(f)
        return []

    def save(self):
        with open(self.storage_path, 'w') as f:
            json.dump(self.facts, f)

    def add_fact(self, fact: str, confidence: float):
        self.facts.append({
            "fact": fact,
            "confidence": confidence,
            "timestamp": time.time()
        })
        self.save()

    def search(self, query: str) -> List[str]:
        # Simple keyword search
        return [f["fact"] for f in self.facts if any(w in f["fact"] for w in query.split())]

class ContradictionWatcher:
    def check_contradiction(self, claim: str, memory_facts: List[str]) -> bool:
        # Simulates checking if 'claim' contradicts any 'memory_facts'
        # In a real system, use NLI.
        # Here, naïve keyword negation check.
        for fact in memory_facts:
            # If facts are roughly same topic but negation differs
            if "not" in claim and "not" not in fact and len(set(claim.split()) & set(fact.split())) > 3:
                return True
        return False

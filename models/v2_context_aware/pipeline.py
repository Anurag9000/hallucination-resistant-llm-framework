from core.llm_interface import LLMInterface
from .context_engine.modules import SessionTracker, EpisodicMemory, ContradictionWatcher

class ContextAwarePipeline:
    def __init__(self, llm: LLMInterface):
        self.llm = llm
        self.session = SessionTracker()
        self.memory = EpisodicMemory()
        self.watcher = ContradictionWatcher()

    async def run(self, query: str) -> str:
        # 1. Grounding Gateway: Context Pack Lookup
        facts = self.memory.search(query)
        session_summary = self.session.get_summary()
        
        context_pack = f"--- CONTEXT PACK ---\nHistory: {session_summary}\nFacts: {facts}"
        
        # 2. Context-Aware Generation
        prompt = f"{context_pack}\n\nUser: {query}\nSystem: Answer consistent with the context."
        draft = await self.llm.generate_text(prompt)
        
        # 3. Contradiction Watcher (Post-Gen Check)
        if self.watcher.check_contradiction(draft, facts):
            return f"[Contradiction Detected 🛑] My previous memory says: {facts[0]}. I cannot say: {draft}"
        
        # 4. Update Session
        self.session.add_turn(query, draft)
        
        # 5. Output with Badges
        return f"{draft} [Context-Bound 🧠]"

    def learn_fact(self, fact: str):
        """Manually inject a fact for demo purposes"""
        self.memory.add_fact(fact, 1.0)

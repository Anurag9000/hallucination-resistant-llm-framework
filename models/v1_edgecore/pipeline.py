from core.llm_interface import LLMInterface
from .kv_manager import DualKVSimulator

class EdgeCorePipeline:
    def __init__(self, llm: LLMInterface):
        self.llm = llm
        self.kv = DualKVSimulator()

    async def run(self, query: str):
        # 1. Simulate Local Retrieval (Tiny Retriever)
        # In a real app, this searches a local vector DB.
        self.kv.add_evidence("E1", "Mars typically orbits the sun at 1.5 AU.")
        self.kv.add_evidence("E2", "Phobos and Deimos are the two moons of Mars.")
        
        # 2. Simulate Gated Decode
        # We manually construct a prompt that forces the LLM to use the "Evidence Pack"
        context = self.kv.get_context_for_generation()
        prompt = f"{context}\n\nUser: {query}\nSystem (EdgeCore): Answer using the Evidence Pack. Cite sources like [E1]."
        
        output = await self.llm.generate_text(prompt)
        return output

import asyncio
import argparse
import sys
import os
import json
import csv

# Assumes this script is run from the project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.mock_llm import MockLLM
from models.v2_context_aware.pipeline import ContextAwarePipeline
from experiments.utils import LLMEvaluator

async def run_memory_eval(episode: dict, llm, max_turns: int, evaluator: LLMEvaluator) -> dict:
    """Evaluates the v2.1 pipeline's memory over a simulated session."""
    pipeline = ContextAwarePipeline(llm)
    
    inject_fact = episode["fact_to_inject"]
    contradiction_query = episode["contradiction_query"]
    retrieval_query = episode["retrieval_query"]
    distractions = episode["distraction_turns"][:max_turns]
    
    # 1. Learn the initial fact
    print(f"Injecting Fact: '{inject_fact}'")
    pipeline.learn_fact(inject_fact)
    
    # 2. Simulate N turns of distracting conversation
    print(f"Running {len(distractions)} conversational turns...")
    for q in distractions:
        _ = await pipeline.run(q)
        
    session_turns = len(pipeline.session.history) // 2 
    print(f"Session history contains {session_turns} user-assistant pairs.")
    
    # 3. Test Retrieval 
    print(f"Testing Retrieval: '{retrieval_query}'")
    retrieval_output = await pipeline.run(retrieval_query)
    
    memory_retained = inject_fact in str(pipeline.memory.facts) 
    
    expected_keywords = episode.get("expected_retrieval_keywords", [])
    keyword_hit = any(kw.lower() in retrieval_output.lower() for kw in expected_keywords)
    
    # 4. Test Contradiction Watcher
    print(f"Testing Contradiction: '{contradiction_query}'")
    contradiction_output = await pipeline.run(contradiction_query)
    contradiction_caught = "[Contradiction Detected 🛑]" in contradiction_output
    
    faithfulness = await evaluator.score_faithfulness(retrieval_output, [inject_fact])
    
    # Cleanup dummy json for testing
    if os.path.exists("episodic_memory.json"):
        os.remove("episodic_memory.json")
        
    return {
        "id": episode["id"],
        "num_turns": len(distractions),
        "fact_injected": inject_fact,
        "memory_retained_in_store": memory_retained,
        "retrieval_keyword_hit": keyword_hit,
        "retrieval_faithfulness": round(faithfulness, 3),
        "contradiction_query": contradiction_query,
        "contradiction_caught": contradiction_caught,
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--use_heuristic", action="store_true", help="Force heuristic evaluation")
    parser.add_argument("--session_length", type=int, default=50, help="Number of intermediate turns")
    parser.add_argument("--provider", type=str, default="mock", choices=["mock", "ollama", "gemini"], help="LLM provider backend")
    parser.add_argument("--model_name", type=str, default="", help="Specific model tag")
    parser.add_argument("--output_dir", type=str, default="", help="Custom directory to save CSV results")
    args = parser.parse_args()
    
    # Load dataset
    data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "evidence_data", "eval_set.json")
    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found. Run generate_eval_data.py first.")
        sys.exit(1)
        
    with open(data_path, 'r') as f:
        full_dataset = json.load(f)
        
    episodes = full_dataset["episodic"]
    evaluator = LLMEvaluator(use_heuristic_only=args.use_heuristic)
    
    if args.provider == "ollama":
        from core.ollama_llm import OllamaLLM
        model_name = args.model_name or "llama3.2"
        llm = OllamaLLM(model_name=model_name)
    elif args.provider == "gemini":
        from core.gemini_llm import GeminiLLM
        model_name = args.model_name or "gemini-2.5-flash"
        llm = GeminiLLM(model_name=model_name)
    else:
        llm = MockLLM()
    
    print("--- 🧠 Running V2 Context-Aware Episodic Eval ---")
    results = []
    
    # For episodic memory we can test lengths 10, 30, 50 to plot a graph later
    test_lengths = [10, 30, 50]
    
    for episode in episodes:
        for length in test_lengths:
            if length <= args.session_length:
                print(f"\nEvaluating episode '{episode['id']}' with {length} turns...")
                res = asyncio.run(run_memory_eval(episode, llm, length, evaluator))
                results.append(res)
    
    print("\n📊 MEMORY EVALUATION RESULTS 📊")
    for r in results:
        print(f"Turns: {r['num_turns']} | Retained: {r['memory_retained_in_store']} | " 
              f"Retrieval Hit: {r['retrieval_keyword_hit']} | Contradiction Caught: {r['contradiction_caught']}")

    # Save to CSV
    if hasattr(args, 'output_dir') and args.output_dir:
        results_dir = args.output_dir
    else:
        results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
        
    os.makedirs(results_dir, exist_ok=True)
    csv_file = os.path.join(results_dir, "memory_persistence.csv")
    
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    
    print(f"\n📁 Results saved to {csv_file}")

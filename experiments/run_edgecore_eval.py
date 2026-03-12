import asyncio
import time
import argparse
import json
import csv
from typing import List, Dict

# Assumes this script is run from the project root
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.mock_llm import MockLLM
from models.v1_edgecore.pipeline import EdgeCorePipeline
from experiments.utils import LLMEvaluator

async def run_ablation(dataset: List[Dict], llm, use_gating: bool, evaluator: LLMEvaluator) -> List[Dict]:
    """Runs the v1 pipeline against a list of queries, optionally disabling the gating."""
    results = []
    
    print(f"Running Ablation on {len(dataset)} queries with gating={use_gating}...")
    
    for item in dataset:
        q = item["query"]
        evidence = item.get("evidence", [])
        
        pipeline = EdgeCorePipeline(llm)
        
        # We manually patch the gating mechanism for the baseline
        if not use_gating:
            # Force low attention to evidence (baseline behavior)
            original_gate = pipeline.kv.gate_attention
            pipeline.kv.gate_attention = lambda x: 0.1 
            
        start_time = time.time()
        output = await pipeline.run(q)
        latency = time.time() - start_time
        
        # Restore original if patched
        if not use_gating:
            pipeline.kv.gate_attention = original_gate
            
        # Use LLMEvaluator
        faithfulness_score = await evaluator.score_faithfulness(output, evidence)
        
        # Check if the expected keyword is present (secondary hard metric)
        expected_keywords = item.get("expected_answer_keywords", [])
        keyword_hit = any(kw.lower() in output.lower() for kw in expected_keywords) if expected_keywords else False
        
        results.append({
            "id": item["id"],
            "type": item["type"],
            "query": q,
            "latency_ms": round(latency * 1000, 2),
            "output": output,
            "faithfulness_score": round(faithfulness_score, 3),
            "keyword_hit": keyword_hit,
            "gating_active": use_gating
        })
        
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--use_heuristic", action="store_true", help="Force heuristic evaluation")
    parser.add_argument("--num_samples", type=int, default=0, help="Limit number of samples per type for quick testing")
    parser.add_argument("--provider", type=str, default="mock", choices=["mock", "ollama", "gemini"], help="LLM provider backend")
    parser.add_argument("--model_name", type=str, default="", help="Specific model tag")
    args = parser.parse_args()
    
    # Load dataset
    data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "evidence_data", "eval_set.json")
    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found. Run generate_eval_data.py first.")
        sys.exit(1)
        
    with open(data_path, 'r') as f:
        full_dataset = json.load(f)
        
    test_queries = full_dataset["factual"] + full_dataset["adversarial"]
    if args.num_samples > 0:
        test_queries = full_dataset["factual"][:args.num_samples] + full_dataset["adversarial"][:args.num_samples]
        
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
    
    print("\n--- 1. Testing Baseline (No Gating) ---")
    baseline_results = asyncio.run(run_ablation(test_queries, llm, use_gating=False, evaluator=evaluator))
    
    print("\n--- 2. Testing EdgeCore (With Gating) ---")
    edgecore_results = asyncio.run(run_ablation(test_queries, llm, use_gating=True, evaluator=evaluator))
    
    # Calculate metrics
    baseline_faithfulness = sum(r["faithfulness_score"] for r in baseline_results) / len(baseline_results) if baseline_results else 0
    edgecore_faithfulness = sum(r["faithfulness_score"] for r in edgecore_results) / len(edgecore_results) if edgecore_results else 0
    
    baseline_kw_hit = sum(1 for r in baseline_results if r["keyword_hit"]) / len(baseline_results) if baseline_results else 0
    edgecore_kw_hit = sum(1 for r in edgecore_results if r["keyword_hit"]) / len(edgecore_results) if edgecore_results else 0
    
    print("\n📊 RESULTS 📊")
    print(f"Baseline Faithfulness (No Gating): {baseline_faithfulness:.2%}")
    print(f"EdgeCore Faithfulness (With Gating): {edgecore_faithfulness:.2%}")
    print(f"Baseline Keyword Hit Rate: {baseline_kw_hit:.2%}")
    print(f"EdgeCore Keyword Hit Rate: {edgecore_kw_hit:.2%}")
    
    # Save to CSV
    results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
    os.makedirs(results_dir, exist_ok=True)
    csv_file = os.path.join(results_dir, "edgecore_ablation.csv")
    
    all_results = baseline_results + edgecore_results
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=all_results[0].keys())
        writer.writeheader()
        writer.writerows(all_results)
    
    print(f"\n📁 Results saved to {csv_file}")

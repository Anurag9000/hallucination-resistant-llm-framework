import asyncio
import time
import argparse
import sys
import os
import json
import csv
from typing import List, Dict

# Assumes this script is run from the project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.mock_llm import MockLLM
from core.verifier_engine import VerifierFactory
from core.cache import VerificationCache
from models.v1_finalthought.pipeline import FinalThoughtPipeline
from experiments.utils import LLMEvaluator

async def evaluate_pipeline(dataset: List[Dict], llm, evaluator: LLMEvaluator) -> List[Dict]:
    """Runs the Final Thought v1.1 pipeline and logs latency and cache hits."""
    # We use a short TTL cache to test eviction or persistence across runs
    cache = VerificationCache(ttl_seconds=3600)
    verifier_factory = VerifierFactory(llm, cache)
    pipeline = FinalThoughtPipeline(llm, verifier_factory)

    results = []
    
    print(f"Running v1.1 Pipeline Evaluation on {len(dataset)} queries...")
    for item in dataset:
        q = item["query"]
        evidence = item.get("evidence", [])
        
        start_time = time.time()
        output = await pipeline.run(q)
        latency = time.time() - start_time
        
        badges = evaluator.evaluate_badges(output)
        faithfulness = await evaluator.score_faithfulness(output, evidence)
        
        results.append({
            "id": item["id"],
            "query": q,
            "latency_ms": round(latency * 1000, 2),
            "output_length": len(output),
            "num_verified": badges["verified_count"],
            "num_likely": badges["likely_count"],
            "num_omitted": badges["omitted_count"],
            "badge_precision": round(badges["badge_precision"], 3),
            "faithfulness_score": round(faithfulness, 3),
            "cache_size_after": len(cache.cache)
        })
        
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--use_heuristic", action="store_true", help="Force heuristic evaluation")
    parser.add_argument("--num_samples", type=int, default=0, help="Number of samples to run")
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
        
    test_queries = full_dataset["factual"]
    if args.num_samples > 0:
        test_queries = test_queries[:args.num_samples]
        
    # Introduce duplicates to test cache optimization explicitly
    if len(test_queries) > 0:
        test_queries.append(test_queries[0])
        
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
    
    results = asyncio.run(evaluate_pipeline(test_queries, llm, evaluator))
    
    print("\n📊 PIPELINE EVALUATION RESULTS 📊")
    
    avg_latency = sum(r["latency_ms"] for r in results) / len(results)
    print(f"Average Pipeline Latency: {avg_latency:.2f} ms")
    
    avg_faithfulness = sum(r["faithfulness_score"] for r in results) / len(results)
    print(f"Average Faithfulness Score: {avg_faithfulness:.2%}")
    
    # Analyze Cache impact if duplicates exist
    if len(test_queries) > 1 and test_queries[-1]["id"] == test_queries[0]["id"]:
        first_run = results[0]
        second_run = results[-1]
        print("\n⚡ Cache Optimization Impact:")
        print(f"  First Run (Miss): {first_run['latency_ms']} ms")
        print(f"  Second Run (Hit): {second_run['latency_ms']} ms")
        if first_run['latency_ms'] > 0:
            speedup = (first_run['latency_ms'] - second_run['latency_ms']) / first_run['latency_ms']
            print(f"  Speedup: {speedup:.2%}")
        
    if hasattr(args, 'output_dir') and args.output_dir:
        results_dir = args.output_dir
    else:
        results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
        
    os.makedirs(results_dir, exist_ok=True)
    csv_file = os.path.join(results_dir, "pipeline_eval.csv")

    with open(csv_file, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    print(f"\n📁 Results saved to {csv_file}")

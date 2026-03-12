import os
import sys
import json
import csv
from pathlib import Path
from collections import defaultdict

def summarize_run(base_run_dir):
    print(f"\n{'='*60}")
    print(f"📈 EXPERIMENT SUMMARY REPORT")
    print(f"Directory: {base_run_dir}")
    print(f"{'='*60}\n")
    
    results = {
        "edgecore": [],
        "pipeline": [],
        "memory": []
    }

    base_path = Path(base_run_dir)
    if not base_path.exists():
        print(f"Error: Directory {base_run_dir} does not exist.")
        return

    for subdir_path in base_path.iterdir():
        if not subdir_path.is_dir():
            continue
            
        exp_name = subdir_path.name
        
        # Determine type
        if exp_name.startswith("edgecore"):
            exp_type = "edgecore"
            csv_name = "edgecore_ablation.csv"
        elif exp_name.startswith("pipeline"):
            exp_type = "pipeline"
            csv_name = "pipeline_eval.csv"
        elif exp_name.startswith("memory"):
            exp_type = "memory"
            csv_name = "memory_persistence.csv"
        else:
            continue
            
        csv_file = subdir_path / csv_name
        config_file = subdir_path / "config.json"
        
        if not csv_file.exists() or not config_file.exists():
            continue
            
        with open(config_file, 'r') as f:
            config = json.load(f)
            
        with open(csv_file, 'r') as f:
            reader = list(csv.DictReader(f))
            if not reader:
                continue
            
            # Aggregate metrics based on type
            if exp_type == "edgecore":
                # Split baseline vs edgecore
                baseline = [r for r in reader if r.get('gating_active') == 'False']
                edgecore = [r for r in reader if r.get('gating_active') == 'True']
                
                b_faith = sum(float(r['faithfulness_score']) for r in baseline) / len(baseline) if baseline else 0
                e_faith = sum(float(r['faithfulness_score']) for r in edgecore) / len(edgecore) if edgecore else 0
                
                results["edgecore"].append(f"{exp_name:<35} | Baseline Faithfulness: {b_faith:.2%} -> EdgeCore: {e_faith:.2%}")
                
            elif exp_type == "pipeline":
                avg_latency = sum(float(r['latency_ms']) for r in reader) / len(reader)
                avg_faith = sum(float(r['faithfulness_score']) for r in reader) / len(reader)
                
                results["pipeline"].append(f"{exp_name:<35} | Avg Faithfulness: {avg_faith:.2%} | Avg Latency: {avg_latency:.1f}ms")
                
            elif exp_type == "memory":
                retained_ratio = sum(1 for r in reader if r['memory_retained_in_store'] == 'True') / len(reader)
                avg_faith = sum(float(r.get('retrieval_faithfulness', 0)) for r in reader) / len(reader)
                
                results["memory"].append(f"{exp_name:<35} | Facts Retained: {retained_ratio:.0%} | Retrieval Faithfulness: {avg_faith:.2%}")

    # Display clear sorted outputs
    for exp_type, items in results.items():
        if items:
            print(f"--- {exp_type.upper()} EXPERIMENTS ---")
            for item in sorted(items):
                print(item)
            print()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python summarize_results.py <run_dir>")
        sys.exit(1)
        
    summarize_run(sys.argv[1])

"""
summarize_results.py — Cross-model leaderboard for the Hallucination-Resistant Framework.

Reads every sub-experiment folder created by run_all.sh, parses all CSVs,
and prints a clean unified comparison table across all 3 pipelines and all providers.

Usage:
    python3 experiments/summarize_results.py experiments/results/run_YYYYMMDD_HHMMSS
"""

import os
import sys
import json
import csv
from pathlib import Path
from collections import defaultdict


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _mean(values):
    return sum(values) / len(values) if values else 0.0


def _pct(v):
    return f"{v:6.1%}"


def _ms(v):
    return f"{v:8.1f} ms"


def _parse_bool(s):
    return str(s).strip().lower() in {"true", "1", "yes"}


# ──────────────────────────────────────────────────────────────────────────────
# CSV parsers — one per eval type
# ──────────────────────────────────────────────────────────────────────────────

def parse_edgecore(csv_path):
    """Returns dict with baseline and edgecore metrics."""
    rows = list(csv.DictReader(open(csv_path)))
    baseline = [r for r in rows if not _parse_bool(r.get("gating_active", False))]
    edgecore = [r for r in rows if _parse_bool(r.get("gating_active", False))]

    def metrics(subset):
        if not subset:
            return {}
        return {
            "faithfulness": _mean([float(r["faithfulness_score"]) for r in subset]),
            "keyword_hit":  _mean([1 if _parse_bool(r.get("keyword_hit")) else 0 for r in subset]),
            "latency_ms":   _mean([float(r["latency_ms"]) for r in subset]),
            "n":            len(subset),
        }

    return {"baseline": metrics(baseline), "edgecore": metrics(edgecore)}


def parse_pipeline(csv_path):
    """Returns pipeline metrics."""
    rows = list(csv.DictReader(open(csv_path)))
    if not rows:
        return {}
    return {
        "faithfulness": _mean([float(r["faithfulness_score"]) for r in rows]),
        "latency_ms":   _mean([float(r["latency_ms"]) for r in rows]),
        "n":            len(rows),
    }


def parse_memory(csv_path):
    """Returns memory-pipeline metrics."""
    rows = list(csv.DictReader(open(csv_path)))
    if not rows:
        return {}
    return {
        "retention_rate":          _mean([1 if _parse_bool(r.get("memory_retained_in_store")) else 0 for r in rows]),
        "retrieval_faithfulness":  _mean([float(r.get("retrieval_faithfulness", 0)) for r in rows]),
        "contradiction_catch_rate":_mean([1 if _parse_bool(r.get("contradiction_caught")) else 0 for r in rows]),
        "n": len(rows),
    }


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def summarize_run(base_run_dir: str):
    base = Path(base_run_dir)
    if not base.exists():
        print(f"Error: {base_run_dir} does not exist.")
        sys.exit(1)

    # Collects:  results[exp_type][exp_name] = parsed metrics dict
    results = defaultdict(dict)
    configs  = {}

    for subdir in sorted(base.iterdir()):
        if not subdir.is_dir():
            continue
        name = subdir.name                          # e.g. edgecore__mock
        cfg_file = subdir / "config.json"
        cfg = json.loads(cfg_file.read_text()) if cfg_file.exists() else {}
        configs[name] = cfg

        if name.startswith("edgecore"):
            csv_f = subdir / "edgecore_ablation.csv"
            if csv_f.exists():
                results["edgecore"][name] = parse_edgecore(csv_f)

        elif name.startswith("pipeline"):
            csv_f = subdir / "pipeline_eval.csv"
            if csv_f.exists():
                results["pipeline"][name] = parse_pipeline(csv_f)

        elif name.startswith("memory"):
            csv_f = subdir / "memory_persistence.csv"
            if csv_f.exists():
                results["memory"][name] = parse_memory(csv_f)

    # ── Print banner ──────────────────────────────────────────────
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║         CROSS-MODEL LEADERBOARD  —  TruthGuard AI           ║")
    print(f"║  Run: {Path(base_run_dir).name:<52} ║")
    print("╚══════════════════════════════════════════════════════════════╝")

    # ── 1. EdgeCore Ablation ──────────────────────────────────────
    print()
    print("▌ 1 / 3  v1 EdgeCore Ablation (Baseline vs Gated)")
    print(f"  {'Experiment':<42}  {'Baseline Faith':>14}  {'EdgeCore Faith':>14}  " +
          f"{'Δ Faith':>8}  {'KW Hit (EC)':>11}  {'Latency':>10}")
    print("  " + "─" * 110)
    for name, m in sorted(results["edgecore"].items()):
        b = m.get("baseline", {})
        e = m.get("edgecore", {})
        if not b or not e:
            continue
        delta = e["faithfulness"] - b["faithfulness"]
        sign = "+" if delta >= 0 else ""
        print(f"  {name:<42}  {_pct(b['faithfulness']):>14}  {_pct(e['faithfulness']):>14}  "
              f"{sign}{_pct(delta):>7}  {_pct(e['keyword_hit']):>11}  {_ms(e['latency_ms']):>10}")
    if not results["edgecore"]:
        print("  (no data)")

    # ── 2. FinalThought Pipeline ──────────────────────────────────
    print()
    print("▌ 2 / 3  v1.1 FinalThought Pipeline")
    print(f"  {'Experiment':<42}  {'Avg Faithfulness':>16}  {'Avg Latency':>12}")
    print("  " + "─" * 75)
    for name, m in sorted(results["pipeline"].items()):
        if not m:
            continue
        print(f"  {name:<42}  {_pct(m['faithfulness']):>16}  {_ms(m['latency_ms']):>12}")
    if not results["pipeline"]:
        print("  (no data)")

    # ── 3. Context-Aware Memory ───────────────────────────────────
    print()
    print("▌ 3 / 3  v2 Context-Aware Memory")
    print(f"  {'Experiment':<48}  {'Retention':>9}  {'Retrieval Faith':>15}  {'Contradiction Catch':>19}")
    print("  " + "─" * 97)
    for name, m in sorted(results["memory"].items()):
        if not m:
            continue
        print(f"  {name:<48}  {_pct(m['retention_rate']):>9}  "
              f"{_pct(m['retrieval_faithfulness']):>15}  {_pct(m['contradiction_catch_rate']):>19}")
    if not results["memory"]:
        print("  (no data)")

    # ── Summary count ─────────────────────────────────────────────
    total = sum(len(v) for v in results.values())
    print()
    print(f"  ✅  {total} experiment(s) recorded across {len(results)} pipeline types.")
    print(f"  📂  Full logs and CSVs: {base_run_dir}")
    print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 experiments/summarize_results.py <run_dir>")
        sys.exit(1)
    summarize_run(sys.argv[1])

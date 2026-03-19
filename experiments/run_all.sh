#!/usr/bin/env bash

# =================================================================
# Focused Sweep Runner — TruthGuard AI (Qwen 1.5B + v2 Memory Vault)
#
# Runs the two key experiments that proved 100% faithfulness:
#   1. v1 EdgeCore Ablation (Baseline vs Gated) — for comparison
#   2. v2 Context-Aware Memory Vault (Qwen 1.5B) — the 100% winner
#
# Low-Context Mode is enforced (num_ctx=2048) on all local models.
# =================================================================

set -e

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BASE_RUN_DIR="experiments/results/run_${TIMESTAMP}"
mkdir -p "$BASE_RUN_DIR"

echo "=========================================================="
echo "🚀  TruthGuard AI — Focused Qwen/v2 Sweep — $(date)"
echo "📂  Run Directory: $BASE_RUN_DIR"
echo "=========================================================="

# ------------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------------
PROVIDER="ollama"
MODEL="qwen2.5:1.5b"
NUM_SAMPLES=5
MEMORY_LENGTHS=(10 30 50)
CTX_ARGS="--num_ctx 2048"

# ------------------------------------------------------------------
# HELPER
# ------------------------------------------------------------------
run_experiment() {
    local eval_script=$1
    local extra_args=$2
    local exp_name=$3

    echo "----------------------------------------------------------"
    echo "▶️  Running: $exp_name"

    TARGET_DIR="${BASE_RUN_DIR}/${exp_name}"
    mkdir -p "$TARGET_DIR"

    # Save config for reproducibility
    cat > "${TARGET_DIR}/config.json" <<EOF
{
  "script": "$eval_script",
  "provider": "$PROVIDER",
  "model_name": "$MODEL",
  "num_samples": $NUM_SAMPLES,
  "num_ctx": 2048,
  "extra_args": "$extra_args",
  "timestamp": "$TIMESTAMP"
}
EOF

    PYTHON_BIN="python3"
    if [ -f "./venv/bin/python3" ]; then
        PYTHON_BIN="./venv/bin/python3"
    fi

    local cmd="${PYTHON_BIN} experiments/${eval_script} \
        --provider ${PROVIDER} \
        --model_name \"${MODEL}\" \
        ${CTX_ARGS} \
        --num_samples ${NUM_SAMPLES} \
        --output_dir \"${TARGET_DIR}\" \
        ${extra_args}"

    eval "$cmd 2>&1 | tee \"${TARGET_DIR}/log.txt\"" \
        || echo "⚠️  Warning: $exp_name reported an error — see log."

    echo "✅  Done: $exp_name"
}

# ------------------------------------------------------------------
# 1. v1 EdgeCore Ablation (Baseline Comparator)
# ------------------------------------------------------------------
echo ""
echo "═══════ 1 / 2 │ v1 EdgeCore Ablation (Baseline vs Gated) ═══════"
run_experiment "run_edgecore_eval.py" "" "edgecore__ollama__qwen2.5_1.5b"

# ------------------------------------------------------------------
# 2. v2 Context-Aware Memory Vault (The 100% Winner)
# ------------------------------------------------------------------
echo ""
echo "═══════ 2 / 2 │ v2 Context-Aware Memory Vault ═══════"
for len in "${MEMORY_LENGTHS[@]}"; do
    run_experiment "run_memory_eval.py" \
        "--session_length $len" \
        "memory__ollama__qwen2.5_1.5b__${len}turns"
done

# ------------------------------------------------------------------
# Aggregate and display leaderboard
# ------------------------------------------------------------------
echo ""
echo "=========================================================="
echo "🏁  Sweep complete! Generating leaderboard…"

PYTHON_BIN="python3"
if [ -f "./venv/bin/python3" ]; then
    PYTHON_BIN="./venv/bin/python3"
fi

${PYTHON_BIN} experiments/summarize_results.py "$BASE_RUN_DIR"
echo "=========================================================="

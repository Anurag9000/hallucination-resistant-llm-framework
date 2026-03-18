#!/usr/bin/env bash

# =================================================================
# Exhaustive Runner Script — Hallucination-Resistant LLM Framework
#
# Sweeps EVERY provider across ALL 3 model pipelines.
# Saves timestamped folders with config + logs + raw CSVs.
# Produces a unified cross-model leaderboard at the end.
# =================================================================

set -e

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BASE_RUN_DIR="experiments/results/run_${TIMESTAMP}"
mkdir -p "$BASE_RUN_DIR"

# Check for Gemini API Key to prevent 0% scores
if [ -z "$GEMINI_API_KEY" ]; then
    echo "⚠️  WARNING: GEMINI_API_KEY is not set. Gemini evaluations will fail and fall back to heuristic."
    echo "   If you want to use Gemini, run: export GEMINI_API_KEY='your_key'"
    echo "   Continuing with local/mock models only..."
    echo ""
fi

echo "=========================================================="
echo "🚀  Exhaustive Framework Sweep — $(date)"
echo "📂  Run Directory: $BASE_RUN_DIR"
echo "=========================================================="

# ------------------------------------------------------------------
# CONFIGURATION — edit these to control the sweep
# ------------------------------------------------------------------

# Providers to test. Remove "gemini" if you have no GEMINI_API_KEY.
# Remove "ollama" if Ollama daemon is not running.
PROVIDERS=("mock" "ollama" "gemini")

# Ollama model(s) to test
MODELS_OLLAMA=("llama3.2" "qwen2.5:1.5b")

# Gemini model(s) to test
MODELS_GEMINI=("gemini-2.5-flash")

# Samples per eval type (increase for full evaluation; use 2 for quick smoke-test)
NUM_SAMPLES=2

# Memory session lengths to sweep (number of turns before recall test)
MEMORY_LENGTHS=(10 30 50)

# ------------------------------------------------------------------
# HELPER
# ------------------------------------------------------------------
run_experiment() {
    local eval_script=$1
    local provider=$2
    local model_name=$3
    local extra_args=$4
    local exp_name=$5

    echo "----------------------------------------------------------"
    echo "▶️  Running: $exp_name"

    TARGET_DIR="${BASE_RUN_DIR}/${exp_name}"
    mkdir -p "$TARGET_DIR"

    # Save exact config so every run is fully reproducible
    cat > "${TARGET_DIR}/config.json" <<EOF
{
  "script": "$eval_script",
  "provider": "$provider",
  "model_name": "$model_name",
  "num_samples": $NUM_SAMPLES,
  "extra_args": "$extra_args",
  "timestamp": "$TIMESTAMP"
}
EOF

    # Detect virtual environment
    PYTHON_BIN="python3"
    if [ -f "./venv/bin/python3" ]; then
        PYTHON_BIN="./venv/bin/python3"
    fi

    # Set context limits to make the setup "make sense" (force reliance on Memory Vault)
    local ctx_args=""
    if [[ "$provider" == "ollama" ]]; then
        ctx_args="--num_ctx 2048"
    elif [[ "$provider" == "gemini" ]]; then
        ctx_args="--max_context 8192"
    fi

    local cmd="${PYTHON_BIN} experiments/${eval_script} \
        --provider ${provider} \
        --model_name \"${model_name}\" \
        ${ctx_args} \
        --num_samples ${NUM_SAMPLES} \
        --output_dir \"${TARGET_DIR}\" \
        ${extra_args}"

    # Run script, tee output to terminal AND log file
    eval "$cmd 2>&1 | tee \"${TARGET_DIR}/log.txt\"" \
        || echo "⚠️  Warning: $exp_name reported an error — see log."

    echo "✅  Done: $exp_name"
}

# ------------------------------------------------------------------
# 1. v1 EdgeCore Pipeline (baseline vs gated, ablation)
# ------------------------------------------------------------------
echo ""
echo "═══════ 1 / 3 │ v1 EdgeCore Ablation ═══════"
for provider in "${PROVIDERS[@]}"; do
    if   [ "$provider" == "ollama" ]; then
        for model in "${MODELS_OLLAMA[@]}"; do
            run_experiment "run_edgecore_eval.py" "$provider" "$model" "" \
                "edgecore__${provider}__${model//:/_}"
        done
    elif [ "$provider" == "gemini" ]; then
        for model in "${MODELS_GEMINI[@]}"; do
            run_experiment "run_edgecore_eval.py" "$provider" "$model" "" \
                "edgecore__${provider}__${model//./_}"
        done
    else
        run_experiment "run_edgecore_eval.py" "$provider" "" "" \
            "edgecore__${provider}"
    fi
done

# ------------------------------------------------------------------
# 2. v1.1 FinalThought Pipeline (latency + faithfulness + cache)
# ------------------------------------------------------------------
echo ""
echo "═══════ 2 / 3 │ v1.1 FinalThought Pipeline ═══════"
for provider in "${PROVIDERS[@]}"; do
    if   [ "$provider" == "ollama" ]; then
        for model in "${MODELS_OLLAMA[@]}"; do
            run_experiment "run_pipeline_eval.py" "$provider" "$model" "" \
                "pipeline__${provider}__${model//:/_}"
        done
    elif [ "$provider" == "gemini" ]; then
        for model in "${MODELS_GEMINI[@]}"; do
            run_experiment "run_pipeline_eval.py" "$provider" "$model" "" \
                "pipeline__${provider}__${model//./_}"
        done
    else
        run_experiment "run_pipeline_eval.py" "$provider" "" "" \
            "pipeline__${provider}"
    fi
done

# ------------------------------------------------------------------
# 3. v2 Context-Aware Memory (retention + faithfulness + turns sweep)
# ------------------------------------------------------------------
echo ""
echo "═══════ 3 / 3 │ v2 Context-Aware Memory ═══════"
for provider in "${PROVIDERS[@]}"; do
    for len in "${MEMORY_LENGTHS[@]}"; do
        if   [ "$provider" == "ollama" ]; then
            for model in "${MODELS_OLLAMA[@]}"; do
                run_experiment "run_memory_eval.py" "$provider" "$model" \
                    "--session_length $len" \
                    "memory__${provider}__${model//:/_}__${len}turns"
            done
        elif [ "$provider" == "gemini" ]; then
            for model in "${MODELS_GEMINI[@]}"; do
                run_experiment "run_memory_eval.py" "$provider" "$model" \
                    "--session_length $len" \
                    "memory__${provider}__${model//./_}__${len}turns"
            done
        else
            run_experiment "run_memory_eval.py" "$provider" "" \
                "--session_length $len" \
                "memory__${provider}__${len}turns"
        fi
    done
done

# ------------------------------------------------------------------
# 4. Aggregate, compare, and display unified leaderboard
# ------------------------------------------------------------------
echo ""
echo "=========================================================="
echo "🏁  All sweeps done! Generating cross-model leaderboard…"

# Re-detect for summary script
PYTHON_BIN="python3"
if [ -f "./venv/bin/python3" ]; then
    PYTHON_BIN="./venv/bin/python3"
fi

${PYTHON_BIN} experiments/summarize_results.py "$BASE_RUN_DIR"
echo "=========================================================="

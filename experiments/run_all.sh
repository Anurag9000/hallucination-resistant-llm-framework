#!/usr/bin/env bash

# Exhaustive Runner Script for TruthGuard AI Framework
# Sweeps across configurations, runs evaluations, and aggregates results.

set -e

# Base directory for this suite of experiments
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BASE_RUN_DIR="experiments/results/run_${TIMESTAMP}"
mkdir -p "$BASE_RUN_DIR"

echo "=========================================================="
echo "🚀 Starting Exhaustive Framework Sweep"
echo "📂 Run Directory: $BASE_RUN_DIR"
echo "=========================================================="

# Define the models and parameters to sweep
# For testing locally without Gemini keys, we rely primarily on 'mock' and 'ollama'
# But we sweep exhaustively based on what the user wants.
PROVIDERS=("mock" "ollama")
MODELS_OLLAMA=("llama3.2")
# Number of samples (keep at 1 or 2 for quick local testing/sweeps)
NUM_SAMPLES=2
# Memory session lengths to sweep
MEMORY_LENGTHS=(10 30)

run_experiment() {
    local eval_script=$1
    local provider=$2
    local model_name=$3
    local extra_args=$4
    local exp_name=$5

    echo "----------------------------------------------------------"
    echo "▶️ Running: $exp_name"
    
    # Create specific subfolder for this sweep
    TARGET_DIR="${BASE_RUN_DIR}/${exp_name}"
    mkdir -p "$TARGET_DIR"

    # Save Configuration
    echo "{ \"script\": \"$eval_script\", \"provider\": \"$provider\", \"model_name\": \"$model_name\", \"num_samples\": $NUM_SAMPLES, \"extra_args\": \"$extra_args\" }" > "${TARGET_DIR}/config.json"

    # Execute Python script
    cmd="python3 experiments/${eval_script} --provider ${provider} --model_name \"${model_name}\" --num_samples ${NUM_SAMPLES} --output_dir \"${TARGET_DIR}\" ${extra_args}"
    echo "Executing: $cmd"
    
    # Run and log output
    eval "$cmd > \"${TARGET_DIR}/log.txt\" 2>&1" || echo "⚠️ Warning: $exp_name encountered an error. Check logs."
    
    echo "✅ Finished: $exp_name"
}

# 1. Sweep EdgeCore Evaluation
for provider in "${PROVIDERS[@]}"; do
    if [ "$provider" == "ollama" ]; then
        for model in "${MODELS_OLLAMA[@]}"; do
             run_experiment "run_edgecore_eval.py" "$provider" "$model" "" "edgecore_${provider}_${model//:/_}"
        done
    else
        run_experiment "run_edgecore_eval.py" "$provider" "" "" "edgecore_${provider}"
    fi
done

# 2. Sweep FinalThought Pipeline Evaluation
for provider in "${PROVIDERS[@]}"; do
    if [ "$provider" == "ollama" ]; then
        for model in "${MODELS_OLLAMA[@]}"; do
             run_experiment "run_pipeline_eval.py" "$provider" "$model" "" "pipeline_${provider}_${model//:/_}"
        done
    else
        run_experiment "run_pipeline_eval.py" "$provider" "" "" "pipeline_${provider}"
    fi
done

# 3. Sweep Context-Aware Memory Evaluation across different session lengths
for provider in "${PROVIDERS[@]}"; do
    for len in "${MEMORY_LENGTHS[@]}"; do
        if [ "$provider" == "ollama" ]; then
            for model in "${MODELS_OLLAMA[@]}"; do
                 run_experiment "run_memory_eval.py" "$provider" "$model" "--session_length $len" "memory_${provider}_${model//:/_}_${len}turns"
            done
        else
            run_experiment "run_memory_eval.py" "$provider" "" "--session_length $len" "memory_${provider}_${len}turns"
        fi
    done
done

echo "=========================================================="
echo "🏁 All Config Sweeps Completed!"
echo "📊 Running Data Aggregation and Summary script..."
python3 experiments/summarize_results.py "$BASE_RUN_DIR"
echo "=========================================================="

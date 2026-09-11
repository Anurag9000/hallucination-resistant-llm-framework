#!/usr/bin/env bash
set -euo pipefail

# Historical sweep compatibility entrypoint.  The repository-owned scientific
# catalog now expands all providers/models/pipelines and the literal OPF_ADP runtime
# owns scheduling/resource pressure. Environment variables such as TRUTHGUARD_MODELS,
# TRUTHGUARD_NUM_SAMPLES and TRUTHGUARD_MEMORY_LENGTHS can customize the matrix.
exec python3 run_all_training.py "$@"

#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Opt-in candidate confirmed in ten alternating pairs on RTX 4090.
# The established benchmark_optimized.sh remains available as the control.
export EARLY_INPUT_RECYCLE="${EARLY_INPUT_RECYCLE:-1}"
export BULK_RESULTS="${BULK_RESULTS:-1}"
export DEFORM_ATTN_IMPL="${DEFORM_ATTN_IMPL:-triton}"
export DEFORM_VALUE_CACHE="${DEFORM_VALUE_CACHE:-0}"
export CUDA_DEVICE_MAX_CONNECTIONS="${CUDA_DEVICE_MAX_CONNECTIONS:-1}"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-backend:native}"
exec bash "$ROOT/benchmark_optimized.sh" "$@"

#!/usr/bin/env bash
# Keep collection and report import on the same Nsight version.
set -euo pipefail
PROFILE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROFILE_ROOT"
NSYS_BIN="${NSYS_BIN:-$HOME/.local/opt/nsight-systems-2024.2.3/target-linux-x64/nsys}"
PYTHON_BIN="${PYTHON_BIN:-/home/ubuntu/.cache/supership-venv/bin/python}"
PROFILE_PREFIX="${1:-output/profiles/ship_prof_$(date +%Y%m%d_%H%M%S)}"
if [[ ! -x "$NSYS_BIN" ]]; then
  printf 'Set NSYS_BIN to a CUDA 12.4 compatible Nsight Systems executable. Missing: %s\n' "$NSYS_BIN" >&2
  exit 1
fi
if [[ -e "$PROFILE_PREFIX.nsys-rep" || -e "$PROFILE_PREFIX.qdstrm" ]]; then
  printf 'Output already exists, choose a new prefix: %s\n' "$PROFILE_PREFIX" >&2
  exit 1
fi
mkdir -p "$(dirname "$PROFILE_PREFIX")"
"$NSYS_BIN" --version
RUNS=1 PYTHON_BIN="$PYTHON_BIN" OUTPUT_FILE="$PROFILE_PREFIX.predictions.json" "$NSYS_BIN" profile \
  --trace=cuda,nvtx,osrt \
  --sample=none \
  --cpuctxsw=none \
  --cuda-graph-trace=node \
  -o "$PROFILE_PREFIX" \
  bash benchmark_optimized.sh
"$NSYS_BIN" stats --report cuda_gpu_kern_sum,cuda_api_sum,osrt_sum "$PROFILE_PREFIX.nsys-rep"

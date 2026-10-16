#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

# ===== 常用参数：修改冒号后的默认值即可；终端环境变量可以临时覆盖 =====
export EVAL_SPLIT="${EVAL_SPLIT:-val}"        # all / val / reference
export BATCH_SIZE="${BATCH_SIZE:-8}"          # 每批图像数，例如 8、16、32
export DEVICE="${DEVICE:-cuda:0}"            # GPU 设备；也可填 cpu
export RUNS="${RUNS:-1}"                     # 独立运行次数，正式对比建议 3 次
export OUTPUT_DIR="${OUTPUT_DIR:-output}"    # 结果和日志目录，可按方案分别保存
export INIT_TIMEOUT="${INIT_TIMEOUT:-300}"   # 每轮初始化超时（秒）
export RUN_TIMEOUT="${RUN_TIMEOUT:-3600}"    # 每轮推理超时（秒）
PYTHON_BIN="${PYTHON_BIN:-$ROOT/.venv/bin/python}"
# ===== 参数区结束 =====

export PYTHON_BIN
export PYTHONUNBUFFERED=1
exec "$PYTHON_BIN" supership/evaluate.py "$@"

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
export BATCH_COPY="${BATCH_COPY:-0}"          # 1=整批回传检测结果，0=原逐框回传
export WARMUP="${WARMUP:-0}"                  # READY 前用随机图像预热次数
export PRECISION="${PRECISION:-fp32}"        # fp32 / fp16
export PREFETCH_FACTOR="${PREFETCH_FACTOR:-2}" # 每个读取进程预取批数
export PIN_MEMORY="${PIN_MEMORY:-0}"         # 1=锁页内存
export NON_BLOCKING="${NON_BLOCKING:-0}"     # 1=非阻塞数据传输
export BUFFERED_JSON="${BUFFERED_JSON:-0}"   # 1=先序列化到字符串再一次写入（增加内存）
export BACKEND="${BACKEND:-torch}"           # torch / cuda_graph / tensorrt
export CUDA_GRAPH="${CUDA_GRAPH:-0}"        # 1=捕获所选后端，可与 TensorRT 组合
# export ENGINE_PATH=output/deploy/model.fp16.engine  # TensorRT 引擎，与 batch 匹配
# export MODEL_WEIGHTS=output/compression/distilled.pth  # 剪枝/蒸馏模型
# export NUM_WORKERS=4                       # 取消注释可覆盖 YAML 的读取进程数
# export STAGE_PROFILE=output/profile/stages.json  # 分阶段诊断：插入 GPU 同步，会影响耗时
PYTHON_BIN="${PYTHON_BIN:-$ROOT/.venv/bin/python}"
# ===== 参数区结束 =====

export PYTHON_BIN
export PYTHONUNBUFFERED=1
exec "$PYTHON_BIN" supership/evaluate.py "$@"

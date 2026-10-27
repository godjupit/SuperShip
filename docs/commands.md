# 运行与评测

在项目根目录运行，先准备 Python 依赖、`data/SuperShip/` 和 `weights/baseline.pth`。可通过 `PYTHON_BIN` 指定解释器。

所有运行、测试和评测只能在调度器已分配的 GPU 计算节点执行。登录节点仅用于编辑、Git 和作业管理。现有分配可通过 `srun --jobid=<有效作业ID> --overlap --ntasks=1 --cpus-per-task=8 --pty bash` 进入；先确认没有其他计算任务占用目标GPU，固定使用已分配的8核。

```bash
bash run.sh --worker
RUNS=3 bash tools/benchmark/benchmark_optimized.sh
bash tools/benchmark/score_reference.sh
```

以上默认路径可能位于共享文件系统。在本集群复现 thread100-light 时，将输入、预测和完整 stdout/stderr 日志都放到计算节点本地 NVMe，全部运行与评分结束后再复制回共享目录。特别是 worker 结束前会刷新 stderr，直接重定向到 JuiceFS 会把日志写入延迟计入端到端时间。数据复制是明确的部署准备；每个 worker 仍须在 READY 后读取输入，所有输出 fsync 和进程退出仍在计时内。

下面在 GPU 计算节点、项目根目录执行；`PYTHON_BIN` 指向已安装依赖的解释器。每次使用新的本地目录，保持官方计时器和最近候选的全部配置：

```bash
set -euo pipefail
test -n "${SLURM_JOB_ID:-}"
nvidia-smi -L
export PYTHON_BIN="${PYTHON_BIN:?请指定项目Python解释器}"
mapfile -t PRESET < <("$PYTHON_BIN" -c 'import json; d=json.load(open("configs/presets/thread100-light.json")); print("\n".join(k+"="+v for k,v in d.items()))')
export "${PRESET[@]}"
LOCAL=$(mktemp -d /tmp/supership-reference-XXXXXXXX)
cp -a data/SuperShip/reference "$LOCAL/reference"
"$PYTHON_BIN" supership/benchmark_submission.py \
  --image-dir "$LOCAL/reference/images" \
  --meta-file "$LOCAL/reference/reference_images_meta.json" \
  --output-file "$LOCAL/prediction.json" --runs 3 --init-timeout 600 \
  -- bash run.sh --worker > "$LOCAL/timing.log" 2> "$LOCAL/runtime.log"
for i in 1 2 3; do
  "$PYTHON_BIN" supership/score_submission.py \
    --gt data/SuperShip/reference/annotations/instances_reference.json \
    --submission "$LOCAL/prediction.run$i.json" > "$LOCAL/score$i.log" 2>&1
done
mkdir -p output
cp -a "$LOCAL" "output/$(basename "$LOCAL")"
cat "$LOCAL/timing.log"
```

2026-10-27 在 g0067、RTX4090、8核下，上述全本地方式三轮为0.260419176 / 0.282751773 / 0.261382914秒，中位0.261382914秒；reference AP50均0.7809，预测字节一致。不要将单次核心处理时间当作官方端到端时间；同样不能将共享存储与本地存储结果混为一组。

主线默认使用 `configs/fastest.env`。历史分支选择匹配的 `configs/presets/` 参数；640 保守版本在 `exp/rtx4090-e2e` 中先执行：

```bash
source configs/presets/conservative640.env
```

计时覆盖 READY 后输入访问、全部输出写盘与进程退出。参考集、validation 和 hidden 的精度分别报告；公开参考集结果不代表隐藏集成绩。需要复测时使用新的输出路径。旧日志、预测、引擎及性能分析产物已按用户要求删除，须重新生成。

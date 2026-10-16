# SuperShip 常用命令

## 推荐：一条命令直接看时间、精度和基线比较

```bash
bash evaluate.sh
```

默认使用 `.venv/bin/python`、RTX 3090（`cuda:0`）、batch size 8，对验证集和公开参考集分别运行 3 次并评分。终端只显示各轮耗时、AP50、时间中位数和基线差值；完整日志与检测结果保存到 `output/`。重复运行会覆盖同名结果。

```bash
bash evaluate.sh val                # 只测验证集，与官方 AP50=0.916 比较
bash evaluate.sh reference          # 只测公开参考集
BATCH_SIZE=16 bash evaluate.sh      # 改 batch size
bash evaluate.sh --runs 3           # 快速跑一次
OUTPUT_DIR=output/batch16 BATCH_SIZE=16 bash evaluate.sh  # 分目录保存，方便比较
```

常用默认参数集中在 `evaluate.sh` 顶部的“常用参数”区：

| 参数 | 默认值 | 用途 |
| --- | --- | --- |
| `EVAL_SPLIT` | `all` | `all` 两个数据集、`val` 验证集、`reference` 参考集 |
| `BATCH_SIZE` | `8` | 每批图像数 |
| `DEVICE` | `cuda:0` | 推理设备 |
| `RUNS` | `3` | 每个数据集独立运行次数 |
| `OUTPUT_DIR` | `output` | 检测结果和日志目录 |
| `INIT_TIMEOUT` | `300` | 每轮初始化超时秒数 |
| `RUN_TIMEOUT` | `3600` | 每轮推理超时秒数 |
| `PYTHON_BIN` | 项目 `.venv/bin/python` | Python 解释器路径 |

例如把脚本中的 `${BATCH_SIZE:-8}` 改为 `${BATCH_SIZE:-16}`，默认批量就变为 16。终端环境变量优先于脚本默认值；位置参数和 `--runs`、`--output-dir`、`--init-timeout`、`--run-timeout` 又可覆盖相应的环境变量。

参考集与本地基线 AP50=0.7929 比较；此值不是官方公布的参考集精度。官方没有公布隐藏集的基线时间或精度，因此脚本不能判定正式比赛是否达标。

以下命令在项目根目录执行。验证集有 1,030 张图像；这里的“测试集”指公开参考集（200 张），正式隐藏测试集由组委会评测。

## 1. 设置运行环境

每次打开新终端先执行一次：

```bash
cd /root/ship/SuperShip
export PYTHON_BIN="$PWD/.venv/bin/python"
export PYTHONUNBUFFERED=1
export DEVICE=cuda:0
export BATCH_SIZE=16
mkdir -p output
set -o pipefail
```

调整批量大小，例如：`export BATCH_SIZE=16`。以下计时和评分命令均使用上述环境。

## 2. 验证集：运行、计时、输出精度

按比赛 worker 协议独立运行 3 次：

```bash
"$PYTHON_BIN" supership/benchmark_submission.py \
  --image-dir data/SuperShip/val/images \
  --meta-file data/SuperShip/val/annotations/instances_val.json \
  --output-file output/val_submission.json \
  --runs 3 \
  -- env PYTHON_BIN="$PYTHON_BIN" bash run.sh --worker \
  2> output/val_runtime.log | tee output/val_benchmark.log
```

计时成功后，对本次的 3 份结果分别评分，只显示主要精度：

```bash
for i in 1 2 3; do
  echo "==> 验证集第 $i 次"
  "$PYTHON_BIN" supership/score_submission.py \
    --gt data/SuperShip/val/annotations/instances_val.json \
    --submission "output/val_submission.run${i}.json" \
    2>&1 | tee "output/val_score.run${i}.log" \
    | grep -E 'mAP@|AP@0.50|AP@0.75'
  result_status=$?
  if [ "$result_status" -ne 0 ]; then
    echo "评分失败，请查看 output/val_score.run${i}.log"
    break
  fi
done
```

官方验证集参考 AP50 为 `0.916`；当前代码曾实测 `0.9170`。优先比较同一数据集上的 `AP@0.50`。

## 3. 公开参考测试集：运行、计时、保存检测输出

```bash
RUNS=3 bash benchmark_reference.sh \
  2> output/reference_runtime.log | tee output/reference_benchmark.log
```

检测输出保存为：

- `output/reference_submission.run1.json`
- `output/reference_submission.run2.json`
- `output/reference_submission.run3.json`

查看第一轮的结果数量和前 3 个检测框：

```bash
"$PYTHON_BIN" - <<'PY'
import json
from pathlib import Path

path = Path("output/reference_submission.run1.json")
results = json.loads(path.read_text())
print(f"检测框数量：{len(results)}")
print(json.dumps(results[:3], ensure_ascii=False, indent=2))
PY
```

如需同时看参考集精度：

```bash
for i in 1 2 3; do
  echo "==> 参考集第 $i 次"
  "$PYTHON_BIN" supership/score_submission.py \
    --gt data/SuperShip/reference/annotations/instances_reference.json \
    --submission "output/reference_submission.run${i}.json" \
    2>&1 | tee "output/reference_score.run${i}.log" \
    | grep -E 'mAP@|AP@0.50|AP@0.75'
  result_status=$?
  if [ "$result_status" -ne 0 ]; then
    echo "评分失败，请查看 output/reference_score.run${i}.log"
    break
  fi
done
```

## 4. 怎么读时间、精度和进度

计时终端显示类似：

```text
run 1/3: 4.473044 s, ...
run 2/3: 4.322453 s, ...
run 3/3: 4.523582 s, ...
{"runs_seconds":[4.473044,4.322453,4.523582],"median_seconds":4.473044}
```

- `run 1/3`：完成第 1 轮，共 3 轮；当前没有逐图像进度条。
- `median_seconds`：3 次端到端时间的中位数，单位为秒。
- 计时包含读取、解码、预处理、推理、后处理、写盘和退出，不包含模型加载、CUDA 初始化。
- 评分单独执行，不计入推理时间。`AP@0.50` 就是比赛关注的 AP50，`0.9170` 表示 91.70%，并非图片正确率。
- 验证集和参考集的分数分别比较，不能把参考集 AP50 直接与官方验证集的 `0.916` 比较。
- 重复运行同一组命令会覆盖对应的结果和日志；比较优化方案前请先备份。

模型警告和运行错误保存在 `output/val_runtime.log` 或 `output/reference_runtime.log`。计时未成功结束时，先检查日志，再执行评分，避免读取旧结果：

```bash
tail -n 30 output/val_runtime.log
tail -n 30 output/reference_runtime.log
```

另开终端查看 GPU 状态：

```bash
watch -n 1 nvidia-smi
```

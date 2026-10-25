# 推理后端与优化工作区快照

- 创建时间：20261016T131655Z（UTC）。
- 分支：`exp/inference-backends`；起点：`cd5fed1508d929547f2c4656aebf209ecacb4547`。
- 状态：dirty 工作区快照，未创建实验代码 commit，未推送；本次未运行新的性能实验。
- 完整代码状态由起点 commit + `source.patch` 确定，文件 SHA256 见 `source.json`。补丁包含原有未跟踪文件；不含本记录目录，也不包含被忽略的数据、权重和输出。

## 分支选择

当前 diff 同时包含推理参数开关、批量结果回传、锁页及异步传输、JSON 写盘、CUDA Graph/TensorRT 后端、ONNX 导出和 INT8 构建、剪枝蒸馏以及权重配置覆盖。先保存在统一的后端开发分支，以保持现有改动完整。没有把当前混合改动伪装成多个已验证的独立历史版本。后续独立路线从明确的版本创建分支，分别提交。

配置 YAML 仅新增空行，原样保留。默认后端仍是 torch，优化开关默认关闭。`config.yaml` 记录源码默认值，不能当作历史运行参数。

## 已有证据与限制

`metrics.json` 从现存计时/评分日志提取，`evidence/` 保存小型原始证据（日志后缀转为 `.log.txt` 以便纳入 Git）。历史实验无确定代码 SHA，不能声称使用本快照完成；存在参数文件的实验保留原参数，无参数文件的保留为空。

既有单轮实验中，`copy_pin_json` 为 9.535698731 秒、AP50=0.9170；`cuda_graph` 日志为 9.383898684 秒、AP50=0.9170。后者缺少完整参数记录，不能据此认定后端严格可比或稳定更快。剪枝和蒸馏结果也按现存日志保存。

原 `OPTIMIZATION_EXPERIMENTS.md` 末尾的“CUDA Graph、剪枝/蒸馏待实现”和“未安装 ONNX”已与当前源码、产物及环境不一致；保留原文作为历史记录，不将其视为当前状态。当前 TensorRT 未安装，不能声称 TensorRT 已测通过。ONNX 导出元数据、压缩参数和训练日志见归档。

当前环境见 `environment.json`，并非完整的历史环境证据。大型产物仍在原路径，位置与校验值见 `artifacts.json`；其他机器恢复时需另行复制这些产物。

## 恢复代码

在另一个检出的干净仓库中切换到 `cd5fed1508d929547f2c4656aebf209ecacb4547`，再运行：

```bash
git apply /absolute/path/to/this-record/source.patch
```

`source.patch` 的反向应用检查已通过，且归档的代码校验值与捕获状态一致。不要在已包含这些改动的当前目录再次应用。

## 后续复现命令示例（尚未执行）

以下来自既有最快 FP32 组合的参数记录，显式固定 torch 后端；输出目录在执行前必须改成新的唯一目录。示例不是历史原始命令的完整取证，也不是本次测量结果。

```bash
BACKEND=torch MODEL_CONFIG=configs/dfine/dfine_hgnetv2_s_supership.yml \
MODEL_WEIGHTS=weights/baseline.pth DEVICE=cuda:0 \
BATCH_COPY=1 WARMUP=3 PRECISION=fp32 PIN_MEMORY=1 NON_BLOCKING=1 \
BUFFERED_JSON=1 NUM_WORKERS=4 PREFETCH_FACTOR=2 BATCH_SIZE=8 \
RUNS=1 OUTPUT_DIR=output/experiments/UNIQUE_RUN_ID bash evaluate.sh val
```

本次检查仅覆盖 Python 语法、Shell 语法和补丁完整性；未重新验证推理正确性或性能，见 `checks.json`。

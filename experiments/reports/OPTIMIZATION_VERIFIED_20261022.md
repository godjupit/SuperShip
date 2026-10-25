# 优化方案与时间记录｜2026-10-22

最终保留提交：**0.476629654 秒**；同工具基线 **4.853070409 秒**，耗时减少 **90.18%**，加速 **10.18×**。服务器已接受最终三轮原始日志。

时间均为北京时间；设备为本机单张 RTX 4090，参考集为公开 v2 的 200 张图像。最终计时使用官方仓库 `thu-scc/SuperShip` 的 `42460fba744a1c8741252177723530976101f305` 版本：READY 后开始访问数据，包含解码、预处理、推理、后处理、fsync、退出及同组子进程等待，初始化不计时。正式评测设备为 RTX 3090，隐藏集结果未测。

## 最终三轮复测与提交

| 方案 | 三轮端到端耗时（秒） | 中位数（秒） | 参考集 AP50（每轮一致） | 实验起止时间 | 提交时间 |
| --- | --- | --- | --- | --- | --- |
| [main-baseline](../20261022-verified/20261022-official-main-baseline/metrics.json) | 4.853070 / 4.827949 / 5.618700 | 4.853070 | 0.7935 | 19:30:49–19:31:23 | 19:31:23，Accepted |
| [fast-opencv-score001](../20261022-verified/20261022-official-fast-opencv-score001/metrics.json) | 0.845095 / 0.910322 / 0.895794 | 0.895794 | 0.8025 | 19:31:24–19:31:46 | 19:31:46，Accepted |
| [fast-opencv-score005](../20261022-verified/20261022-official-fast-opencv-score005/metrics.json) | 0.562363 / 0.558237 / 0.567733 | 0.562363 | 0.7962 | 19:31:46–19:32:04 | 19:32:04，Accepted |
| [fast-opencv-half-score005](../20261022-verified/20261022-official-fast-opencv-half-score005/metrics.json) | 0.477736 / 0.476630 / 0.476559 | 0.476630 | 0.7808 | 19:32:05–19:32:22 | 19:32:23，Accepted |

## 方案与精度取舍

共同优化：用常驻线程并行解码和有界预取；复用锁页内存；GPU 使用 channels-last、FP16、CUDA Graph，并将归一化与模型后处理一起捕获；检测结果批量回传，以 NumPy 向量化坐标处理和 orjson 写盘。所有图像均在 READY 后解码、推理，预热仅使用合成图像。保留原 HGNetv2 + D-FINE/RT-DETRv4-S 基本模型和官方权重。

最快配置增加 `JPEG_REDUCTION=2`，在 JPEG 解码阶段缩小为一半尺寸，再用 OpenCV 缩放到 640×640；框坐标仍按原始尺寸还原。`SCORE_THRESHOLD=0.05` 减少无效低分输出和序列化开销。更保守配置使用完整 JPEG 解码，其余相同。

| 验证方案 | 验证集 AP50 | 单次端到端耗时（秒） | 检查时间 |
| --- | --- | --- | --- |
| [fast-fp32-vector](../20261022-verified/20261022-validation-fast-fp32-vector/metrics.json) | 0.9171 | 5.475333 | 19:29:43–19:29:58 |
| [fast-opencv-half](../20261022-verified/20261022-validation-fast-opencv-half/metrics.json) | 0.9109 | 3.429113 | 19:30:24–19:30:39 |
| [fast-opencv-half-score005](../20261022-verified/20261022-validation-fast-opencv-half-score005/metrics.json) | 0.9101 | 1.871662 | 19:30:40–19:30:48 |
| [fast-opencv-score001](../20261022-verified/20261022-validation-fast-opencv-score001/metrics.json) | 0.9172 | 4.088346 | 19:29:59–19:30:14 |
| [fast-opencv-score005](../20261022-verified/20261022-validation-fast-opencv-score005/metrics.json) | 0.9167 | 2.380080 | 19:30:15–19:30:24 |

验证集为完整 1,030 张图像，包含尾批处理；此处仅单次检查精度，不将验证集日志提交系统。基线 AP50=0.9171，本地 98% 参考线为 0.898758。最快方案 AP50=0.9101，保留约 99.24% 的基线精度。系统回执仅确认计时被接受；不表示隐藏集精度已审核。

## 筛选过的方向

以下为前期筛选结果，使用旧计时工具，与上表的最终复测分开比较。AP50 均为参考集三轮结果；三轮时间、完整参数、源码与环境见[筛选快照](../20261022-verified/screening.json)。

| 实验名（20261022-） | 三轮中位数（秒） | 参考集 AP50 | 筛选结论 |
| --- | --- | --- | --- |
| fast-cuda-fp16 | 1.918164 | 0.7935 | 完成检查并提交；较慢时恢复最快提交 |
| fast-cuda-fp16-b16 | 1.918214 | 0.7933 | 完成检查并提交；较慢时恢复最快提交 |
| fast-cuda-fp32 | 1.968371 | 0.7933 | 完成检查并提交；较慢时恢复最快提交 |
| fast-cuda-grouped-fp16 | 1.867984 | 0.7935 | 完成检查并提交；较慢时恢复最快提交 |
| fast-cuda-no-antialias | 1.867476 | 0.8024 | 完成检查并提交；较慢时恢复最快提交 |
| fast-fp16-b16 | 1.416532 | 0.7926 | 完成检查并提交；较慢时恢复最快提交 |
| fast-fp16-b32 | 1.416860 | 0.7926 | 完成检查并提交；较慢时恢复最快提交 |
| fast-fp16-deploy | 1.316620 | 0.7926 | 完成检查并提交；较慢时恢复最快提交 |
| fast-fp16-normal-exit | 2.118622 | 0.7926 | 完成检查并提交；较慢时恢复最快提交 |
| fast-fp16-opencv | 0.865479 | 0.8025 | 完成检查并提交；较慢时恢复最快提交 |
| fast-fp16-score001 | 1.366588 | 0.7926 | 完成检查并提交；较慢时恢复最快提交 |
| fast-fp16-vector | 1.367429 | 0.7926 | 完成检查并提交；较慢时恢复最快提交 |
| fast-fp16-w4 | 1.667300 | 0.7926 | 完成检查并提交；较慢时恢复最快提交 |
| fast-fp32 | 1.667770 | 0.7935 | 完成检查并提交；较慢时恢复最快提交 |
| fast-fp32-contiguous | 1.416726 | 0.7931 | 完成检查并提交；较慢时恢复最快提交 |
| fast-fp32-vector | 1.366626 | 0.7935 | 完成检查并提交；较慢时恢复最快提交 |
| fast-opencv-deploy | 0.865432 | 0.8027 | 完成检查并提交；较慢时恢复最快提交 |
| fast-opencv-fp32 | 0.915697 | 0.8026 | 完成检查并提交；较慢时恢复最快提交 |
| fast-opencv-half | 0.815272 | 0.7858 | 完成检查并提交；较慢时恢复最快提交 |
| fast-opencv-half-score005 | 0.514573 | 0.7808 | 完成检查并提交；较慢时恢复最快提交 |
| fast-opencv-score001 | 0.815510 | 0.8025 | 完成检查并提交；较慢时恢复最快提交 |
| fast-opencv-score005 | 0.570945 | 0.7962 | 完成检查并提交；较慢时恢复最快提交 |
| fast-opencv-score010 | 0.564683 | 0.7753 | 未提交：低于参考集基线的98% |
| fast-opencv-w12 | 0.865521 | 0.8025 | 完成检查并提交；较慢时恢复最快提交 |

提高阈值到 0.1 的参考集 AP50 为 0.7753，未通过筛选，不采用。仅改变 batch、线程数、FP16、部署融合或改用 nvJPEG，均未超过最终 CPU 解码组合。未因允许训练/剪枝而替换基本模型；本次没有新增训练。

## 复现与检查

优化代码位于 `exp/rtx4090-e2e` 分支；本次最终复测源码版本为 `6925b4e`，各实验保存了参数、官方工具版本、命令、日志 SHA256 和完整预测产物路径。权重 SHA256 为 `42a04535d33de94acc58ae3c66a9a2d161e975ee17adae6cae533770d1929c3e`，数据归档 SHA256 为 `4f70f1167ee51090e30f5f3c4915f821b2c960d307610902ad666ae92ea69b71`。

在优化分支工作目录中安装 `requirements.txt` 和 `requirements-fast.txt`，使用与 CUDA 驱动兼容的 PyTorch，然后运行：

```bash
PYTHON_BIN=/home/ubuntu/.cache/supership-venv/bin/python \
PIPELINE=fast PRECISION=fp16 BACKEND=cuda_graph \
BATCH_SIZE=8 NUM_WORKERS=8 PIPELINE_DEPTH=3 \
SCORE_THRESHOLD=0.05 IMAGE_DECODER=opencv JPEG_REDUCTION=2 \
VECTORIZED_RESULTS=1 CHANNELS_LAST=1 MODEL_DEPLOY=0 \
FAST_EXIT=1 TORCH_THREADS=1 RESIZE_ANTIALIAS=1 RUNS=3 \
bash benchmark_reference.sh
```

改为 `JPEG_REDUCTION=1` 可复现更保守方案。每轮输出仍须通过评分脚本。原始预测和日志保存在各 metrics.json 的 `artifact_directory`（本机忽略目录），逐轮 AP50 和服务器回执已纳入实验记录。最终检查：30 项测试通过、1 项跳过；`git diff --check` 通过。

后续可继续尝试原模型内部解码器剪枝加训练集蒸馏、TensorRT 针对当前硬件重新构建、GPU/CPU 流水线重叠；这些属于待验证方向，本次不宣称其有收益。

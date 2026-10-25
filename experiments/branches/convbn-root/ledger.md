# 优化实验日志

每次实验在本文件追加简要结果；完整参数、运行环境、命令、日志和分析保存在独立实验文件夹，并从本文件链接。

## 未做性能优化的基线

| 数据集 | 参数 | 端到端耗时 | AP50 | 官方参考 AP50 |
| --- | --- | --- | --- | --- |
| 验证集，1,030 张 | RTX 3090、FP32、640×640、batch=8、workers=4 | **17.452 秒（本次单次）** | **0.9170** | 0.916 |

此基线使用官方模型和权重，仅包含运行必需的 GPU 位置编码修复及无效框过滤，尚未应用性能优化。证据：`output/experiments/single_run/baseline/`；按本次要求每组只运行 1 次。

后续按日期追加记录，每条写清参数、耗时、AP50 和结论；单次测量用于筛选，不能排除运行波动。

## 2026-10-16｜参考集批量实验｜已完成

参数：RTX 3090、FP32、640×640、workers=4、参考集 200 张，每组 3 次；只调整 batch。

| batch | 三次耗时（秒） | 中位数（秒） | 各轮 AP50 |
| --- | --- | --- | --- |
| 8 | 4.374 / 4.574 / 4.573 | 4.573 | 0.7929 / 0.7929 / 0.7930 |
| 16 | 4.524 / 4.474 / 4.575 | 4.524 | 0.7927 / 0.7927 / 0.7927 |
| 32 | 4.974 / 4.925 / 4.925 | 4.925 | 0.7931 / 0.7931 / 0.7931 |

结论：batch=16 的小幅提升不足以排除运行波动，batch=32 本轮更慢，暂保留 batch=8。日志：`output/experiments/batch{8,16,32}/`。

## 2026-10-16｜验证集基线复测｜已完成

参数：RTX 3090、FP32、640×640、batch=8、workers=4、验证集 1,030 张，运行 1 次。

结果：端到端 **17.055 秒**，**AP50=0.9170**，比官方验证集参考 0.916 高 0.10 个百分点。精度基本一致；单次时间仅供参考，后续用 3 次中位数比较。日志：`output/val_benchmark.log`、`output/val_score.run1.log`。

## 2026-10-16｜优化验证｜每组仅运行 1 次

固定：验证集 1,030 张、RTX 3090、640×640，默认 FP32、batch=8、workers=4、预取=2；表中只列改动。

| 实验目录名 | 改动 | 耗时（秒） | AP50 |
| --- | --- | --- | --- |
| `baseline` | 同次基线 | 17.452 | 0.9170 |
| `batch_copy` | 仅批量回传 | 13.043 | 0.9170 |
| `warmup3` | 仅随机预热 3 次 | 17.054 | 0.9170 |
| `fp16` | 仅 FP16 | 17.607 | 0.9170 |
| `workers2` | 仅 workers=2 | 17.606 | 0.9170 |
| `workers8` | 仅 workers=8 | 17.699 | 0.9170 |
| `prefetch4` | 仅预取批数=4 | 17.547 | 0.9170 |
| `pin_async` | 锁页内存 + 非阻塞传输 | 15.801 | 0.9170 |
| `batch16` | 仅 batch=16 | 17.706 | 0.9170 |
| `batch32` | 仅 batch=32 | 17.605 | 0.9169 |
| `buffered_json` | 仅一次性 JSON 写盘 | 16.002 | 0.9170 |
| `combined` | 批量回传 + 预热3 + FP16 + 锁页/非阻塞 | 11.390 | 0.9170 |
| `copy_pin_json` | 批量回传 + 预热3 + 锁页/非阻塞 + JSON | 9.536 | 0.9170 |
| `combined_json` | 上一项 + FP16 | 9.770 | 0.9170 |

结论：本次最快为 FP32 组合 **9.536 秒**，比同次基线缩短 **45.4%**（约 **1.83×**），AP50=0.9170；308,879 个输出与基线逐项一致。单独增大 batch、读取进程或启用 FP16 未体现收益。

结果保存在 `output/experiments/single_run/<实验目录名>/`，包含 `parameters.json`、计时/评分日志和检测结果；代码差异保存在该父目录的 `code.patch` 与 `final_code.patch`。批量回传、JSON 单项结果也与基线逐项一致。

复现本次最快配置（所有优化开关默认仍关闭，可自行选择）：

```bash
BATCH_COPY=1 WARMUP=3 PRECISION=fp32 PIN_MEMORY=1 NON_BLOCKING=1 \
BUFFERED_JSON=1 NUM_WORKERS=4 PREFETCH_FACTOR=2 BATCH_SIZE=8 \
RUNS=1 OUTPUT_DIR=output/experiments/reproduce bash evaluate.sh val
```

## 2026-10-16｜部署与模型压缩｜每项单次验证

参数：验证集 1,030 张、batch=8，启用批量回传、锁页内存、非阻塞传输和一次性 JSON 写盘。

| 方法 | 耗时（秒） | AP50 | 结论 |
| --- | --- | --- | --- |
| CUDA Graph，FP32 | 9.384 | 0.9170 | 已支持完整批次和补齐尾批，初始化时用合成数据捕获。 |
| TensorRT FP16，builder优化级别1，workspace=2GiB | 11.958 | 0.9173 | 成功构建并评测，当前未比 PyTorch 组合方案更快。 |
| TensorRT FP16，独立执行流 | 12.484 | 0.9173 | 本次未体现加速；记录保留。 |
| TensorRT FP16 + CUDA Graph | 11.302 | 0.9173 | 组合已跑通，仍慢于当前 PyTorch 方案。 |
| INT8 Q/DQ，32张训练样本，42个骨干卷积 | 12.735 | 0.8926 | 精度下降，不采用，保留引擎与结果。 |
| 同一 INT8 引擎，独立执行流 | 11.105 | 0.8926 | 时间缩短但精度仍低，不采用。 |
| 解码器 3→2 层结构剪枝，预热3次 | 9.638 | 0.9112 | 参数量 10,420,385→9,125,753，精度下降。 |
| 剪枝 + 20 步监督蒸馏，预热3次 | 9.634 | 0.9106 | 训练和保存流程已验证，短训练未恢复精度。 |
| 剪枝 + 完整1轮蒸馏（1,203步），预热3次 | 9.737 | 0.9087 | 精度继续下降，保留该实验，不采用此训练配置。 |

训练仅使用训练集，batch=2、lr=1e-5、seed=42、KD权重=1；分类/L1/GIoU监督加上按预测集合匹配的教师蒸馏，冻结 BN 运行统计。短训练产物位于 `output/compression/`，完整1轮产物位于 `output/compression_epoch1/`；评测位于 `output/experiments/{cuda_graph,pruned_initial,distilled,distilled_epoch1}/`。低精度结果及权重全部保留，当前不替换原模型。

ONNX、TensorRT FP16、显式 INT8、CUDA Graph、结构剪枝和监督蒸馏均已实现并实测。当前本地最快且保持原精度的是 PyTorch CUDA Graph（9.384秒、AP50=0.9170）；均为单次测量，不代表稳定排名。默认仍保留原模型，优化按开关选择。

失败记录也保留：旧式 INT8 在优化级别1和0下均报内部图错误；显式校准首次因 ORT 缓存参数清空统计而失败，移除参数后成功；TensorRT + Graph 首次因引擎生命周期问题失败，修复后通过整批/尾批测试及评测。详细参数及结果见[部署与压缩实验索引](experiments/ADVANCED_RESULTS_20261016.md)，复现命令见 `COMMON_COMMANDS.md`。

## 性能分析分支

模型算子分析、流水线分阶段计时及其详细实验记录单独保存在 `exp/performance-analysis` 分支。当前分支仅保留推理优化和常规时间/精度评估。

## 2026-10-22｜20261022-torch-optimized｜已完成

RTX 4090，公开参考集 200 张，torch、fp32、batch=8、workers=4，独立运行三次。端到端中位耗时 **3.220965 秒**；各轮参考集 AP50=[0.7935, 0.7935, 0.7935]。隐藏集精度未测。参数、代码版本、环境与原始产物路径见[详细记录](experiments/20261022-torch-optimized/notes.md)。

## 2026-10-22｜20261022-cuda-graph｜已完成

RTX 4090，公开参考集 200 张，cuda_graph、fp32、batch=8、workers=4，独立运行三次。端到端中位耗时 **3.171570 秒**；各轮参考集 AP50=[0.7935, 0.7935, 0.7935]。隐藏集精度未测。参数、代码版本、环境与原始产物路径见[详细记录](experiments/20261022-cuda-graph/notes.md)。

### 本次分支对照与提交结果

同一台 RTX 4090、同一公开参考集：main 中位数 5.128391426 秒；inference-backends 普通组合 3.220965060 秒，CUDA Graph 3.171570187 秒；performance-analysis 的 CUDA Graph 3.221062850 秒。各轮 AP50 均为 0.7935，优化分支所有三轮输出均与基线第一轮逐项相同，覆盖 200 张图像、59,974 个检测。

已先提交主分支，再正式提交 inference-backends 的 CUDA Graph 完整三轮日志；服务器接受最终耗时 **3.171570187 秒**（比本次基线缩短约 38.2%）。分析分支未体现进一步收益；约 0.05 秒差异不足以说明分支本身有稳定性能差异。服务器仅解析计时，隐藏集精度未测。

## 2026-10-22｜20261022-fast-fp32

RTX 4090，参考集 200 张，三轮端到端中位数 **1.667770 秒**；各轮 AP50=[0.7935, 0.7935, 0.7935]；参数差异 `{}`。隐藏集精度未测。[详细记录](experiments/20261022-fast-fp32/notes.md)。

## 2026-10-22｜20261022-fast-fp32-vector

RTX 4090，参考集 200 张，三轮端到端中位数 **1.366626 秒**；各轮 AP50=[0.7935, 0.7935, 0.7935]；参数差异 `{"VECTORIZED_RESULTS": "1"}`。隐藏集精度未测。[详细记录](experiments/20261022-fast-fp32-vector/notes.md)。

## 2026-10-22｜20261022-fast-fp16-vector

RTX 4090，参考集 200 张，三轮端到端中位数 **1.367429 秒**；各轮 AP50=[0.7926, 0.7926, 0.7926]；参数差异 `{"VECTORIZED_RESULTS": "1", "PRECISION": "fp16"}`。隐藏集精度未测。[详细记录](experiments/20261022-fast-fp16-vector/notes.md)。

## 2026-10-22｜20261022-fast-fp16-b16

RTX 4090，参考集 200 张，三轮端到端中位数 **1.416532 秒**；各轮 AP50=[0.7926, 0.7926, 0.7926]；参数差异 `{"VECTORIZED_RESULTS": "1", "PRECISION": "fp16", "BATCH_SIZE": "16"}`。隐藏集精度未测。[详细记录](experiments/20261022-fast-fp16-b16/notes.md)。

## 2026-10-22｜20261022-fast-fp16-b32

RTX 4090，参考集 200 张，三轮端到端中位数 **1.416860 秒**；各轮 AP50=[0.7926, 0.7926, 0.7926]；参数差异 `{"VECTORIZED_RESULTS": "1", "PRECISION": "fp16", "BATCH_SIZE": "32"}`。隐藏集精度未测。[详细记录](experiments/20261022-fast-fp16-b32/notes.md)。

## 2026-10-22｜20261022-fast-fp16-w4

RTX 4090，参考集 200 张，三轮端到端中位数 **1.667300 秒**；各轮 AP50=[0.7926, 0.7926, 0.7926]；参数差异 `{"VECTORIZED_RESULTS": "1", "PRECISION": "fp16", "NUM_WORKERS": "4"}`。隐藏集精度未测。[详细记录](experiments/20261022-fast-fp16-w4/notes.md)。

## 2026-10-22｜20261022-fast-fp16-opencv

RTX 4090，参考集 200 张，三轮端到端中位数 **0.865479 秒**；各轮 AP50=[0.8025, 0.8025, 0.8025]；参数差异 `{"VECTORIZED_RESULTS": "1", "PRECISION": "fp16", "IMAGE_DECODER": "opencv"}`。隐藏集精度未测。[详细记录](experiments/20261022-fast-fp16-opencv/notes.md)。

## 2026-10-22｜20261022-fast-fp16-deploy

RTX 4090，参考集 200 张，三轮端到端中位数 **1.316620 秒**；各轮 AP50=[0.7926, 0.7926, 0.7926]；参数差异 `{"VECTORIZED_RESULTS": "1", "PRECISION": "fp16", "MODEL_DEPLOY": "1"}`。隐藏集精度未测。[详细记录](experiments/20261022-fast-fp16-deploy/notes.md)。

## 2026-10-22｜20261022-fast-fp16-score001

RTX 4090，参考集 200 张，三轮端到端中位数 **1.366588 秒**；各轮 AP50=[0.7926, 0.7926, 0.7926]；参数差异 `{"VECTORIZED_RESULTS": "1", "PRECISION": "fp16", "SCORE_THRESHOLD": "0.001"}`。隐藏集精度未测。[详细记录](experiments/20261022-fast-fp16-score001/notes.md)。

## 2026-10-22｜20261022-fast-fp32-contiguous

RTX 4090，参考集 200 张，三轮端到端中位数 **1.416726 秒**；各轮 AP50=[0.7931, 0.7931, 0.7931]；参数差异 `{"VECTORIZED_RESULTS": "1", "CHANNELS_LAST": "0"}`。隐藏集精度未测。[详细记录](experiments/20261022-fast-fp32-contiguous/notes.md)。

## 2026-10-22｜20261022-fast-fp16-normal-exit

RTX 4090，参考集 200 张，三轮端到端中位数 **2.118622 秒**；各轮 AP50=[0.7926, 0.7926, 0.7926]；参数差异 `{"VECTORIZED_RESULTS": "1", "PRECISION": "fp16", "FAST_EXIT": "0"}`。隐藏集精度未测。[详细记录](experiments/20261022-fast-fp16-normal-exit/notes.md)。

## 2026-10-22｜20261022-fast-cuda-fp32

RTX 4090，参考集 200 张，三轮端到端中位数 **1.968371 秒**；各轮 AP50=[0.7933, 0.7933, 0.7933]；参数差异 `{"VECTORIZED_RESULTS": "1", "IMAGE_DECODER": "cuda"}`。隐藏集精度未测。[详细记录](experiments/20261022-fast-cuda-fp32/notes.md)。

## 2026-10-22｜20261022-fast-cuda-fp16

RTX 4090，参考集 200 张，三轮端到端中位数 **1.918164 秒**；各轮 AP50=[0.7935, 0.7935, 0.7935]；参数差异 `{"VECTORIZED_RESULTS": "1", "PRECISION": "fp16", "IMAGE_DECODER": "cuda"}`。隐藏集精度未测。[详细记录](experiments/20261022-fast-cuda-fp16/notes.md)。

## 2026-10-22｜20261022-fast-cuda-fp16-b16

RTX 4090，参考集 200 张，三轮端到端中位数 **1.918214 秒**；各轮 AP50=[0.7933, 0.7933, 0.7933]；参数差异 `{"VECTORIZED_RESULTS": "1", "PRECISION": "fp16", "IMAGE_DECODER": "cuda", "BATCH_SIZE": "16"}`。隐藏集精度未测。[详细记录](experiments/20261022-fast-cuda-fp16-b16/notes.md)。

## 2026-10-22｜20261022-fast-opencv-fp32

RTX 4090，参考集 200 张，三轮端到端中位数 **0.915697 秒**；各轮 AP50=[0.8026, 0.8026, 0.8026]；参数差异 `{"VECTORIZED_RESULTS": "1", "IMAGE_DECODER": "opencv"}`。隐藏集精度未测。[详细记录](experiments/20261022-fast-opencv-fp32/notes.md)。

## 2026-10-22｜20261022-fast-opencv-score001

RTX 4090，参考集 200 张，三轮端到端中位数 **0.815510 秒**；各轮 AP50=[0.8025, 0.8025, 0.8025]；参数差异 `{"VECTORIZED_RESULTS": "1", "PRECISION": "fp16", "IMAGE_DECODER": "opencv", "SCORE_THRESHOLD": "0.001"}`。隐藏集精度未测。[详细记录](experiments/20261022-fast-opencv-score001/notes.md)。

## 2026-10-22｜20261022-fast-opencv-deploy

RTX 4090，参考集 200 张，三轮端到端中位数 **0.865432 秒**；各轮 AP50=[0.8027, 0.8027, 0.8027]；参数差异 `{"VECTORIZED_RESULTS": "1", "PRECISION": "fp16", "IMAGE_DECODER": "opencv", "MODEL_DEPLOY": "1"}`。隐藏集精度未测。[详细记录](experiments/20261022-fast-opencv-deploy/notes.md)。

## 2026-10-22｜20261022-fast-opencv-w12

RTX 4090，参考集 200 张，三轮端到端中位数 **0.865521 秒**；各轮 AP50=[0.8025, 0.8025, 0.8025]；参数差异 `{"VECTORIZED_RESULTS": "1", "PRECISION": "fp16", "IMAGE_DECODER": "opencv", "NUM_WORKERS": "12"}`。隐藏集精度未测。[详细记录](experiments/20261022-fast-opencv-w12/notes.md)。

## 2026-10-22｜20261022-fast-cuda-grouped-fp16

RTX 4090，参考集 200 张，三轮端到端中位数 **1.867984 秒**；各轮 AP50=[0.7935, 0.7935, 0.7935]；参数差异 `{"VECTORIZED_RESULTS": "1", "PRECISION": "fp16", "IMAGE_DECODER": "cuda"}`。隐藏集精度未测。[详细记录](experiments/20261022-fast-cuda-grouped-fp16/notes.md)。

## 2026-10-22｜20261022-fast-cuda-no-antialias

RTX 4090，参考集 200 张，三轮端到端中位数 **1.867476 秒**；各轮 AP50=[0.8024, 0.8024, 0.8024]；参数差异 `{"VECTORIZED_RESULTS": "1", "PRECISION": "fp16", "IMAGE_DECODER": "cuda", "RESIZE_ANTIALIAS": "0"}`。隐藏集精度未测。[详细记录](experiments/20261022-fast-cuda-no-antialias/notes.md)。

## 2026-10-22｜20261022-fast-opencv-score005

RTX 4090，参考集 200 张，三轮端到端中位数 **0.570945 秒**；各轮 AP50=[0.7962, 0.7962, 0.7962]；参数差异 `{"VECTORIZED_RESULTS": "1", "PRECISION": "fp16", "IMAGE_DECODER": "opencv", "SCORE_THRESHOLD": "0.05"}`。隐藏集精度未测。[详细记录](experiments/20261022-fast-opencv-score005/notes.md)。

## 2026-10-22｜20261022-fast-opencv-score010

RTX 4090，参考集 200 张，三轮端到端中位数 **0.564683 秒**；各轮 AP50=[0.7753, 0.7753, 0.7753]；参数差异 `{"VECTORIZED_RESULTS": "1", "PRECISION": "fp16", "IMAGE_DECODER": "opencv", "SCORE_THRESHOLD": "0.1"}`。隐藏集精度未测。[详细记录](experiments/20261022-fast-opencv-score010/notes.md)。

## 2026-10-22｜20261022-fast-opencv-half

RTX 4090，参考集 200 张，三轮端到端中位数 **0.815272 秒**；各轮 AP50=[0.7858, 0.7858, 0.7858]；参数差异 `{"VECTORIZED_RESULTS": "1", "PRECISION": "fp16", "IMAGE_DECODER": "opencv", "JPEG_REDUCTION": "2"}`。隐藏集精度未测。[详细记录](experiments/20261022-fast-opencv-half/notes.md)。

## 2026-10-22｜20261022-fast-opencv-half-score005

RTX 4090，参考集 200 张，三轮端到端中位数 **0.514573 秒**；各轮 AP50=[0.7808, 0.7808, 0.7808]；参数差异 `{"VECTORIZED_RESULTS": "1", "PRECISION": "fp16", "IMAGE_DECODER": "opencv", "JPEG_REDUCTION": "2", "SCORE_THRESHOLD": "0.05"}`。隐藏集精度未测。[详细记录](experiments/20261022-fast-opencv-half-score005/notes.md)。

## 2026-10-22｜独立验证集精度复核

公开验证集 1,030 张，各一次完整运行；基线 AP50=0.917，选中方案 `20261022-fast-opencv-half-score005` AP50=0.9101。达到同集基线98%；该单次验证时间不与200张排行榜时间混比，隐藏集精度未测。[详细记录](experiments/20261022-validation/notes.md)。

## 2026-10-22｜最终复测与优化时间记录

当前官方工具复测：单张 RTX 4090、公开参考集200张、完整三轮，基线4.853070秒；最快0.476630秒（验证集AP50=0.9101），保守方案0.562363秒（AP50=0.9167）。最终最快日志于北京时间19:32:23正式提交并获Accepted。测试30通过、1跳过，隐藏集未测。方案、逐轮时间、实验起止与回执见[完整记录](OPTIMIZATION_VERIFIED_20261022.md)。

## 2026-10-22｜最终官方复测和提交

当前官方工具完整三轮：主分支4.853070409秒，全量检测优化0.895794447秒，阈值0.05优化0.562363170秒，缩小JPEG解码+阈值0.05为 **0.476629654秒**；均正式提交并保存回执，最后保留0.476629654秒。最快方案公开验证集AP50=0.9101，基线0.9170；隐藏集精度未测。[完整优化方案与时间表](OPTIMIZATION_RESULTS_20261022.md)。

- 20261022-194940 [control](experiments/20261022-194940-further-control/notes.md): median 0.477079557 s, reference AP50=[0.7808, 0.7808, 0.7808]; submitted=True.

- 20261022-194940 [cvtcolor](experiments/20261022-194940-further-cvtcolor/notes.md): median 0.459317472 s, reference AP50=[0.7808, 0.7808, 0.7808]; submitted=True.

- 20261022-194940 [direct](experiments/20261022-194940-further-direct/notes.md): median 0.465033972 s, reference AP50=[0.7808, 0.7808, 0.7808]; submitted=True.

- 20261022-194940 [async](experiments/20261022-194940-further-async/notes.md): median 0.458977147 s, reference AP50=[0.7808, 0.7808, 0.7808]; submitted=True.

- 20261022-194940 [async-cvtcolor](experiments/20261022-194940-further-async-cvtcolor/notes.md): median 0.456020483 s, reference AP50=[0.7808, 0.7808, 0.7808]; submitted=True.

- 20261022-195126 [async-cvtcolor-b16](experiments/20261022-195126-further-async-cvtcolor-b16/notes.md): median 0.515991054 s, reference AP50=[0.781, 0.781, 0.781]; submitted=True.

- 20261022-195126 [async-cvtcolor-w4](experiments/20261022-195126-further-async-cvtcolor-w4/notes.md): median 0.478162180 s, reference AP50=[0.7808, 0.7808, 0.7808]; submitted=True.

- 20261022-195126 [async-cvtcolor-cudnn](experiments/20261022-195126-further-async-cvtcolor-cudnn/notes.md): median 0.447681871 s, reference AP50=[0.781, 0.7809, 0.781]; submitted=True.

- 20261022-195126 [decoder2](experiments/20261022-195126-further-decoder2/notes.md): median 0.426459931 s, reference AP50=[0.7763, 0.7763, 0.7763]; submitted=False.

- 20261022-195126 [decoder1](experiments/20261022-195126-further-decoder1/notes.md): median 0.403493509 s, reference AP50=[0.7764, 0.7764, 0.7764]; submitted=False.

- 20261022-195339 [decoder2-score004](experiments/20261022-195339-further-decoder2-score004/notes.md): median 0.417805221 s, reference AP50=[0.7786, 0.7784, 0.7782]; submitted=True.

- 20261022-195339 [decoder1-score004](experiments/20261022-195339-further-decoder1-score004/notes.md): median 0.405175354 s, reference AP50=[0.7789, 0.7789, 0.7789]; submitted=True.

- 20261022-195339 [decoder1-score003](experiments/20261022-195339-further-decoder1-score003/notes.md): median 0.435693499 s, reference AP50=[0.779, 0.779, 0.779]; submitted=True.

- 20261022-195339 [size576-half](experiments/20261022-195339-further-size576-half/notes.md): median 0.390968942 s, reference AP50=[0.7887, 0.7888, 0.7887]; submitted=True.

- 20261022-195339 [size576-full](experiments/20261022-195339-further-size576-full/notes.md): median 0.462455832 s, reference AP50=[0.7931, 0.7931, 0.793]; submitted=True.

- 20261022-195339 [size512-full](experiments/20261022-195339-further-size512-full/notes.md): median 0.446113230 s, reference AP50=[0.7873, 0.7873, 0.7874]; submitted=True.

- Validation [20261022-195339-further-size576-half](experiments/20261022-195339-further-size576-half/notes.md): AP50=0.9067, baseline=0.9170, precision pass=True.

- Validation [20261022-195339-further-decoder1-score004](experiments/20261022-195339-further-decoder1-score004/notes.md): AP50=0.8926, baseline=0.9170, precision pass=False.

- Validation [20261022-195126-further-async-cvtcolor-cudnn](experiments/20261022-195126-further-async-cvtcolor-cudnn/notes.md): AP50=0.91, baseline=0.9170, precision pass=True.

- 20261022-195623 [size512-half](experiments/20261022-195623-further-size512-half/notes.md): median 0.362355174 s, reference AP50=[0.7873, 0.787, 0.7873]; submitted=True.

- 20261022-195623 [size544-half](experiments/20261022-195623-further-size544-half/notes.md): median 0.380510271 s, reference AP50=[0.7816, 0.7819, 0.7819]; submitted=True.

- 20261022-195623 [size576-decoder2](experiments/20261022-195623-further-size576-decoder2/notes.md): median 0.390023948 s, reference AP50=[0.7735, 0.7736, 0.7735]; submitted=False.

- 20261022-195623 [size576-decoder1](experiments/20261022-195623-further-size576-decoder1/notes.md): median 0.392777066 s, reference AP50=[0.7635, 0.7631, 0.7631]; submitted=False.

- Validation [20261022-195623-further-size512-half](experiments/20261022-195623-further-size512-half/notes.md): AP50=0.896, baseline=0.9170, precision pass=False.

- Validation [20261022-195623-further-size544-half](experiments/20261022-195623-further-size544-half/notes.md): AP50=0.9054, baseline=0.9170, precision pass=True.

- Validation [20261022-195339-further-decoder2-score004](experiments/20261022-195339-further-decoder2-score004/notes.md): AP50=0.9039, baseline=0.9170, precision pass=True.

- 20261022-195852 [confirm-control](experiments/20261022-195852-further-confirm-control/notes.md): median 0.475669439 s, reference AP50=[0.7808, 0.7808, 0.7808]; submitted=True.

- 20261022-195852 [confirm-size544](experiments/20261022-195852-further-confirm-size544/notes.md): median 0.379818620 s, reference AP50=[0.7819, 0.7817, 0.7814]; submitted=True.

- Validation [20261022-195852-further-confirm-size544](experiments/20261022-195852-further-confirm-size544/notes.md): AP50=0.9054, baseline=0.9170, precision pass=True.

## 2026-10-23｜20261023-230700-convbn-root｜completed

负责人Codex /root；分支exp/convbn-root，父提交4971fb72cf67f6295da02bd25b9f204c766a95e3；GPU0 RTX4090，独占23:07–23:14，已释放。仅Conv-BN折叠，544其余配置不变，融合99对、剩余BN=0。首组三轮中位数未融合0.343989090秒、融合0.332367181秒（快3.38%）；复测未融合0.350231934秒、融合0.365588829秒（慢4.38%）。全部逐轮结果均保留，收益未稳定复现，不晋级默认最快候选；保留FUSE_CONV_BN可选开关。融合reference AP50最低0.7813；完整1030张validation AP50=0.9057，通过同组98%门槛0.89866；hidden AP50=null。56测试通过、1跳过；官方完整覆盖和尾批检查通过。未进行竞赛提交，原最快/保守候选及最近Accepted记录保持不变，官方隐藏集最优未知。[完整记录](experiments/20261023-230700-convbn-root/notes.md)。

用户追加10对交错复测已完成：GPU0于23:17–23:20独占，现已释放。未融合10次中位数0.3454462245秒，融合0.3289938185秒（缩短4.7627%），8/10对更快，仍有两对回退；范围分别0.340679127–0.376887739秒、0.324713411–0.368183548秒。所有20轮输出及reference精度检查通过，融合AP50最低0.7812，validation AP50沿用本次前阶段0.9057；hidden AP50=null。初步六轮及所有不利结果保留。最终结论：中位数有改善，存在波动，保留可选融合开关和原默认方案。完整逐轮记录见同实验paired10.json和notes.md。状态completed，更新时间北京时间23:20。

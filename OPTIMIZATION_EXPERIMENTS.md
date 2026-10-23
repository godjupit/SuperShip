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

负责人 Codex /root；优化分支 exp/convbn-root；父提交 `4971fb72cf67f6295da02bd25b9f204c766a95e3`；父实验 `20261022-195852-further-confirm-size544`。实现/检查及初步记录提交 `50ddc7319e3e2ac4185d5e16a96f22a1566456e4`；运行时提交 `84fd5fe09124a8b8ee28f7e6cc1d9a60f6e70165`。独立 worktree 已从/tmp迁移至 `/home/ubuntu/SuperShip-convbn-root`。GPU0 RTX4090独占北京时间23:07–23:14，已释放。仅融合Conv-BN，未启用整模型deploy，544其余配置不变。

融合99对、剩余BN=0；参考集200张均通过校验与逐轮评分，含完整验证集和尾批检查。首组三轮中位数未融合0.343989090秒、融合0.332367181秒（快3.38%）；复测未融合0.350231934秒、融合0.365588829秒（慢4.38%）。全部逐轮结果保留；加速未稳定复现，不晋级默认最快候选，保留FUSE_CONV_BN可选开关。融合reference AP50最低0.7813，高于同组门槛0.77763；完整1030张validation AP50=0.9057，高于同组门槛0.89866；hidden AP50=null。56项测试通过、1跳过，格式检查通过。本次未进行竞赛提交；原最快/保守候选及最近Accepted记录不变，官方隐藏集最优未知。完整命令、环境、数值检查、所有逐轮结果和校验和保存在exp/convbn-root分支 `experiments/20261023-230700-convbn-root/`。

用户追加10对复测已完成：GPU0 RTX4090于北京时间23:17–23:20独占，现已释放。每方案10次独立worker，AB/BA轮换先后顺序，每轮均完成官方计时、完整输出校验和评分。未融合中位数0.3454462245秒，融合0.3289938185秒（缩短4.7627%），8/10对更快；范围分别0.340679127–0.376887739秒、0.324713411–0.368183548秒。融合reference AP50最低0.7812，仍通过门槛；validation AP50沿用本次前阶段0.9057，hidden AP50=null。完整逐轮结果、配置及校验和保存在exp/convbn-root的同实验paired10.json。初始六轮及不利结果全部保留。最终结论：中位数有改善，但存在回退，保留FUSE_CONV_BN可选开关和原默认方案；未竞赛提交。状态completed，更新时间北京时间23:20。

追加10对的可复现记录提交：`c6d860d6b09e4566494ab2314f6482f1bb0a2a5d`；[完整逐轮记录](https://github.com/godjupit/SuperShip/blob/c6d860d6b09e4566494ab2314f6482f1bb0a2a5d/experiments/20261023-230700-convbn-root/notes.md)。


## 2026-10-22｜20261022-main｜已完成

RTX 4090，公开参考集 200 张，torch、fp32、batch=8、workers=4，独立运行三次。端到端中位耗时 **5.128391 秒**；各轮参考集 AP50=[0.7935, 0.7935, 0.7935]。隐藏集精度未测。参数、代码版本、环境与原始产物路径见[详细记录](experiments/20261022-main/notes.md)。

### 本次分支对照与提交结果

同一台 RTX 4090、同一公开参考集：main 中位数 5.128391426 秒；inference-backends 普通组合 3.220965060 秒，CUDA Graph 3.171570187 秒；performance-analysis 的 CUDA Graph 3.221062850 秒。各轮 AP50 均为 0.7935，优化分支所有三轮输出均与基线第一轮逐项相同，覆盖 200 张图像、59,974 个检测。

已先提交主分支，再正式提交 inference-backends 的 CUDA Graph 完整三轮日志；服务器接受最终耗时 **3.171570187 秒**（比本次基线缩短约 38.2%）。分析分支未体现进一步收益；约 0.05 秒差异不足以说明分支本身有稳定性能差异。服务器仅解析计时，隐藏集精度未测。


## 2026-10-23｜20261023-225558-branch-audit-root｜completed

负责人 Codex /root；工作分支 main；基于 `d12866deaa0172f90a0de55743399ac8aa0e68cf`；更新时间北京时间 22:55。范围为所有分支的历史结果、源码差异及优化优先级核对；本次不运行性能实验、不占用 GPU、不进行竞赛提交。已 fetch origin，全部五个本地分支均与对应远程引用一致。

| 分支及核对提交 | 历史参考集三轮中位数 | 结论 |
| --- | --- | --- |
| main `d12866d` | 5.128391 秒；更新计时工具复测 4.853070 秒 | 基线入口，汇总中的 0.476630 秒已被后续优化分支记录更新 |
| exp/inference-backends `43f44ed` | 3.171570 秒 | 较早的 CUDA Graph 组合，reference AP50=0.7935 |
| exp/performance-analysis `9ebd7e2` | 3.221063 秒 | 较早的分析路线，无证据优于 inference-backends |
| exp/rtx4090-e2e `4971fb7` | **0.379818620 秒** | 544 输入最快已通过参考集及完整验证集检查的候选；优先作为后续优化父版本 |
| exp/profile-fast544 `3e61b33` | 父版本复测 0.359185144 秒；分阶段诊断 0.342910136 秒 | 同一 544 配置的诊断工具；未提出新的提速假设，不将测量波动当作分支收益 |

上述数据均为 RTX 4090、公开参考集 200 张；不同日期、工具版本及诊断开销的结果不作同轮严格排名。RTX 3090 历史记录另组，不能混比。源码 SHA、逐轮结果、证据路径和后续优先级见[核对记录](experiments/20261023-225558-branch-audit-root/notes.md)。

- 本地最快有效候选：`20261022-195852-further-confirm-size544`，父版本 `4971fb72cf67f6295da02bd25b9f204c766a95e3`；reference AP50=0.7819/0.7817/0.7814，validation AP50=0.9054，hidden AP50=null。512 半尺寸解码虽测得 0.362355 秒，但 validation AP50=0.8960 低于同组门槛 0.89866，不晋级。
- 保守候选：保留完整 JPEG 解码的 640 方案 `20261022-official-fast-opencv-score005`，历史中位数 0.562363170 秒、validation AP50=0.9167；不覆盖其复现记录。
- 已核对的最近 Accepted 提交：544 确认实验，北京时间 2026-10-22 19:59:29，0.379818620 秒，timing parsed only；未在线核验账号当前状态。官方隐藏集最优：未知。
- 用户本次要求：后续先分析所有分支，再优先优化最快的有效方案。优化从上述 544 父版本建立独立分支/worktree；profile-fast544 仅提供诊断能力。cuDNN 自动选算法、FP16、channels-last、CUDA Graph、异步回传均已启用，不重复计作新优化。
- 优先检查 READY 后 GPU 图内 Conv-BN 融合覆盖及重复类型/布局转换，再根据具体卷积形状决定替换实现。现有全进程 Nsight stats 包含算法搜索、预热，不能直接当成稳态推理热点。每个新假设先登记、同协议复测三轮，并检查完整输入/尾批与精度后再晋级。


## 2026-10-23｜20261023-232613-submit-convbn｜completed

负责人Codex /root；用户明确授权正式提交一次，账号已按本机说明核对。运行分支exp/convbn-root，源码c6d860d6b09e4566494ab2314f6482f1bb0a2a5d，父实验20261023-230700-convbn-root；544融合配置不变。GPU0 RTX4090，23:26预检空闲，预约生成一次完整三轮原始日志并校验各轮精度后提交；不拼接10次交错日志。原始产物独立存于融合worktree的output/submissions/20261023-232613-submit-convbn；提交前核对日志SHA256，提交后保存脱敏回执。本次只提交该新日志一次，不自动重传旧成绩。

北京时间23:27:49已正式提交一次并获Submission Accepted，系统解析中位数 **0.340258450秒**；逐轮0.361170067/0.340258450/0.327337284秒，reference AP50=0.7816/0.7812/0.7820。日志SHA256 `7df2f1ffe686526ea3e95a99221ee82d36cb84c497214ea0afebc2d8695d23e5`，提交前后一致；提交原始三轮完整日志，未拼接或挑选10次交错结果。新三轮输出均通过官方校验和score_reference.sh评分；本次未重新测validation（同一融合实现此前AP50=0.9057），hidden AP50=null。GPU于23:28释放，状态completed。最近被接受提交更新为本次0.340258450秒，官方隐藏集最优仍未知；仅计时被接收，保守候选保留。用户仅授权本次提交，未重传旧日志。[脱敏回执及完整记录](experiments/20261023-232613-submit-convbn/notes.md)。

## 2026-10-23｜20261023-235500-main-fastest-merge｜completed

负责人Codex /root；用户要求将当前最快方案自动合入main。合并父分支exp/convbn-root（c6d860d6b09e4566494ab2314f6482f1bb0a2a5d），保留主分支已有文档、环境安装脚本及历史回执。将benchmark_optimized.sh默认FUSE_CONV_BN设置为1，采用已验证99对融合/544配置；仍可FUSE_CONV_BN=0复现未融合对照。合并后检查测试、独立三轮参考计时和评分，并重新检查完整验证集；不自动进行新的竞赛提交。正式GPU运行前再次检查独占情况并更新状态。

## 2026-10-23｜20261023-fast544-bottlenecks｜诊断完成

最快有效544/FP16/b8/CUDA Graph配置，RTX4090，真实200张参考输入；Nsight Systems排除初始化/合成预热，内核累计217.579ms，BN34.552ms（15.88%）、FP16转换23.478ms（10.79%）、Half拷贝18.087ms（8.31%）、concat14.265ms（6.56%）。Nsight Compute五类单调用取样：concat样本DRAM82.70%/L2吞吐88.81%，具有访存吞吐受限证据；BN/卷积样本未达吞吐饱和。首末GPU活动之间的时间线覆盖率98.51%，不等于SM利用率。Nsight输出参考AP50=0.7817，五次NCU取样运行各自评分0.7815–0.7827，均通过官方输出检查；本次完整验证集和隐藏集未测，无新正式端到端成绩或竞赛提交。旧NCU不兼容和首次模板过滤失败均保留原因。见[优化过程](优化过程.md)与[详细实验记录](experiments/20261023-fast544-bottlenecks/notes.md)。

合并后验证：GPU0 RTX4090，负责人Codex /root，2026-10-23 23:56预检无其他GPU进程，开始独占参考三轮及完整验证集一轮。有效参数及精确命令见experiments/20261023-235500-main-fastest-merge/；运行结束后释放并记录全部结果。

合并后验证完成：源码49f97ba（完整SHA见详细记录），56 passed/1 skipped；RTX4090参考集三轮0.330820520/0.324560194/0.346345743秒，中位0.330820520秒，AP50=0.7817/0.7823/0.7814；完整1030张验证集AP50=0.9057、单次1.243855975秒，均通过官方输出及精度检查。运行开始23:55，23:57检查GPU空闲并释放。main优化wrapper默认启用99对Conv-BN融合，FUSE_CONV_BN=0可恢复对照。原三轮Accepted 0.340258450秒和保守候选仍保留；本次无新竞赛提交，hidden AP50未测。Nsight内核表明确标注为未融合对照。[完整合并与验证记录](experiments/20261023-235500-main-fastest-merge/notes.md)。

## 2026-10-24｜20261024-000500-kernel-sweep｜planned

负责人Codex /root；exp/kernel-sweep-20261024，父main121df82。对融合544/FP16/b8/Graph分别检查类型转换、concat、布局拷贝和卷积替代。GPU0 RTX4090，00:04预检空闲，现独占；各方案独立目录、完整三轮与评分，失败保留。不将旧未融合profile当作当前热点。详细记录[实验目录](experiments/20261024-000500-kernel-sweep/notes.md)。

## 2026-10-24｜20261024-001212-kernel-control｜success

Codex /root, GPU0 RTX4090 exclusive, exp/kernel-sweep-20261024; [control](experiments/20261024-001212-kernel-control/notes.md).

control: runs=[0.322793661, 0.366654933, 0.33017573], median=0.33017573, reference AP50=[0.7818, 0.7816, 0.7817], validation AP50=0.9055, submitted=False. Error=None.

## 2026-10-24｜20261024-001241-kernel-weight-half｜success

Codex /root, GPU0 RTX4090 exclusive, exp/kernel-sweep-20261024; [weight-half](experiments/20261024-001241-kernel-weight-half/notes.md).

weight-half: runs=[0.319338027, 0.317976677, 0.331978987], median=0.319338027, reference AP50=[0.7816, 0.7817, 0.7811], validation AP50=0.9056, submitted=True. Error=None.

## 2026-10-24｜20261024-001310-kernel-affine-half｜success

Codex /root, GPU0 RTX4090 exclusive, exp/kernel-sweep-20261024; [affine-half](experiments/20261024-001310-kernel-affine-half/notes.md).

affine-half: runs=[0.35012063, 0.310748555, 0.341132634], median=0.341132634, reference AP50=[0.7813, 0.7811, 0.7815], validation AP50=0.9055, submitted=True. Error=None.

## 2026-10-24｜20261024-001340-kernel-concat-half｜success

Codex /root, GPU0 RTX4090 exclusive, exp/kernel-sweep-20261024; [concat-half](experiments/20261024-001340-kernel-concat-half/notes.md).

concat-half: runs=[0.337413893, 0.317121803, 0.342875711], median=0.337413893, reference AP50=[0.7814, 0.7817, 0.7816], validation AP50=0.9057, submitted=True. Error=None.

## 2026-10-24｜20261024-001413-kernel-encoder-layout｜success

Codex /root, GPU0 RTX4090 exclusive, exp/kernel-sweep-20261024; [encoder-layout](experiments/20261024-001413-kernel-encoder-layout/notes.md).

encoder-layout: runs=[0.354918758, 0.327095394, 0.332704269], median=0.332704269, reference AP50=[0.7815, 0.782, 0.7818], validation AP50=0.9056, submitted=True. Error=None.

## 2026-10-24｜20261024-001443-kernel-linear1x1｜success

Codex /root, GPU0 RTX4090 exclusive, exp/kernel-sweep-20261024; [linear1x1](experiments/20261024-001443-kernel-linear1x1/notes.md).

linear1x1: runs=[0.318179532, 0.318393595, 0.336021234], median=0.318393595, reference AP50=[0.7812, 0.7811, 0.7812], validation AP50=0.9058, submitted=True. Error=None.

## 2026-10-24｜20261024-001602-kernel-weights-linear｜success

Codex /root, GPU0 RTX4090 exclusive, exp/kernel-sweep-20261024; [weights-linear](experiments/20261024-001602-kernel-weights-linear/notes.md).

weights-linear: runs=[0.359631911, 0.311155924, 0.34447236], median=0.34447236, reference AP50=[0.7812, 0.7812, 0.7812], validation AP50=0.9058, submitted=True. Error=None.

## 2026-10-24｜20261024-001631-kernel-weights-affine｜success

Codex /root, GPU0 RTX4090 exclusive, exp/kernel-sweep-20261024; [weights-affine](experiments/20261024-001631-kernel-weights-affine/notes.md).

weights-affine: runs=[0.344889588, 0.32487112, 0.331088401], median=0.331088401, reference AP50=[0.7811, 0.7815, 0.7813], validation AP50=0.9054, submitted=True. Error=None.

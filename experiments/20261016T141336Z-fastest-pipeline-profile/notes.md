# 最快配置的完整流水线耗时诊断

2026-10-16；当前最好历史记录：FP32 CUDA Graph，9.384 秒、AP50=0.9170（单次）。本实验使用相同参数，完整验证集 1030 张，正常模式与诊断模式各一次。

正常模式：**9.731465 秒、AP50=0.9170**。诊断模式：**9.949605 秒、AP50=0.9170**。两次输出文件 SHA256 完全一致：True。

| 阶段 | 时间（秒） | 占诊断总时间 |
|---|---:|---:|
| 模型前向（含 Graph 输入复制/回放） | 3.459 | 34.76% |
| 读取与预处理等待 | 1.979 | 19.89% |
| CPU 检测结果整理 | 1.941 | 19.51% |
| JSON 序列化 | 0.746 | 7.49% |
| CPU → GPU 传输 | 0.224 | 2.25% |
| GPU → CPU 回传及转列表 | 0.163 | 1.64% |
| GPU 后处理 | 0.147 | 1.48% |
| 文件写入及 fsync | 0.052 | 0.53% |
| DataLoader 建立/收尾及输出准备 | 0.099 | 0.99% |
| 进程收尾与计时边界余量 | 1.140 | 11.46% |
| 合计 | 9.950 | 100.00% |

## 计时口径

- 正常模式按项目 benchmark 的 READY 后请求发送至进程退出计时，包含读取/预处理、前向、后处理、输出及退出；排除加载模型、CUDA 初始化、Graph 捕获和评分。
- 诊断模式在每个阶段结束时执行 CUDA synchronize 后读取 perf_counter，避免将异步前向错误归到回传时间。新增同步改变流水线重叠和调度，因此上表只能解释本次诊断，不能硬套到历史 9.384 秒或本次正常 9.731 秒上。
- 分阶段函数内合计 8.809240 秒；诊断外层 benchmark 为 9.949605 秒。差额 1.140365 秒为进程收尾与计时边界余量，包含结果/loader 对象销毁、报告写入、运行时退出及父进程等待检测等；未进一步拆分，不能全当成模型耗时。
- 读取等待包括 worker 启动、解码/resize/归一化未被预取隐藏的等待、拼批与进程间传递；4 个 worker 的 CPU 工作并行于推理，表中不是它们的累计 CPU 时间。要细分 worker 内部算子，需另做采样。
- 模型前向包含 CUDAGraphRuntime 的输入缓冲复制、尾批补齐及 graph 回放。没有在 graph 内插入模块同步，因此本次没有 backbone/attention 等内部占比；此前 eager 前向分析不能直接当作当前 graph 的占比。
- 不设置检测分数过滤，仍产生 308879 条结果；不复用其他实验 AP50。本次正常与诊断模式均独立评分，AP50=0.9170。

## 结论与下一步

模型前向约 34.8%，读取等待约 19.9%，CPU 结果整理加 JSON 约 27.0%。优先尝试批量坐标换算/四舍五入并减少 Python 字典构造；读取侧再试减少进程间传输及预处理开销；前向侧测试卷积/BN 融合后重新捕获 Graph。以上均为待测方向，不承诺收益，任何改变输出舍入/排序的方案都需逐项比较与重新评分。

## 复现

```bash
BACKEND=cuda_graph PRECISION=fp32 BATCH_SIZE=8 BATCH_COPY=1 WARMUP=0 PIN_MEMORY=1 NON_BLOCKING=1 BUFFERED_JSON=1 NUM_WORKERS=4 PREFETCH_FACTOR=2 RUNS=1 EVAL_SPLIT=val OUTPUT_DIR=output/experiments/20261016T141336Z-fastest-pipeline-profile/normal bash evaluate.sh
BACKEND=cuda_graph PRECISION=fp32 BATCH_SIZE=8 BATCH_COPY=1 WARMUP=0 PIN_MEMORY=1 NON_BLOCKING=1 BUFFERED_JSON=1 NUM_WORKERS=4 PREFETCH_FACTOR=2 RUNS=1 EVAL_SPLIT=val STAGE_PROFILE=experiments/20261016T141336Z-fastest-pipeline-profile/stages.json OUTPUT_DIR=output/experiments/20261016T141336Z-fastest-pipeline-profile/diagnostic bash evaluate.sh
```

复现时必须换新的实验目录与输出目录，避免覆盖本次结果。STAGE_PROFILE 仅用于诊断，日常测速不要设置。

代码基于 `2f1539d1147325ec4a4fd77a0e0c9e8eb022a1ce`，dirty=true；实验开始前保存完整 [source.patch](source.patch)，包括新建计时模块，校验值见 [config.json](config.json)。环境见 [environment.json](environment.json)；实际参数/权重及标注哈希见 [config.json](config.json)；原始诊断见 [stages.json](stages.json)，汇总见 [metrics.json](metrics.json)，完整控制台见 [normal.log](normal.log)、[diagnostic.log](diagnostic.log)。预测大文件位于 `output/experiments/20261016T141336Z-fastest-pipeline-profile`，不纳入 Git。

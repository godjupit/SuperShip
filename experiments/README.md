# 实验记录索引

代码位于 `exp/inference-backends` 分支；`baseline-pytorch` 指向优化前的 `cd5fed1`。推理与部署代码提交为 `8b5e90e`，性能剖析工具提交为 `dfcd19d`。历史记录中的基准 SHA、dirty 标记和补丁保留原样，表示实际运行时状态。

| 记录 | 类型 | 分支 | 状态 |
| --- | --- | --- | --- |
| [20261016T131655Z-inference-backends-snapshot](20261016T131655Z-inference-backends-snapshot/notes.md) | 当前代码完整快照与历史证据归档 | `exp/inference-backends` | dirty；完整补丁已保存；本次未新运行实验 |

历史汇总见仓库根目录 `OPTIMIZATION_EXPERIMENTS.md`；其部分待办已过时，以各记录的证据和限制为准。新运行使用独立目录，保存实际参数、代码版本、环境、命令和结果，不覆盖旧记录。

## 已执行的瓶颈实验


[本次部署与压缩实验结果](ADVANCED_RESULTS_20261016.md)（含低精度与失败记录）。

性能分析记录（算子分析、流水线耗时占比）位于 `exp/performance-analysis` 分支。

## 2026-10-22 追加优化实验导航

2026-10-22 本轮任务：在已有 RTX 4090 最快方案上继续检索、消融、独立验证和复测。负责人：当前 Codex 会话；工作分支 `exp/rtx4090-e2e`；起点 `585d759`；修改范围为 fast worker、其测试和基准默认参数；GPU 为单张 RTX 4090。实验期间依次运行，不并发计时。任务状态：completed（最终检查和提交状态见汇总末尾）。历史实验目录保持原名。

[本轮完整汇总](../OPTIMIZATION_FOLLOWUP_20261022.md)；[逐轮指标](../OPTIMIZATION_FOLLOWUP_20261022.csv)；[历史全局台账](../OPTIMIZATION_EXPERIMENTS.md)。

| 实验 | 状态 | 记录 |
| --- | --- | --- |
| 20261022-194940-further-async | success | [参数与结果](20261022-194940-further-async/notes.md) |
| 20261022-194940-further-async-cvtcolor | success | [参数与结果](20261022-194940-further-async-cvtcolor/notes.md) |
| 20261022-194940-further-control | success | [参数与结果](20261022-194940-further-control/notes.md) |
| 20261022-194940-further-cvtcolor | success | [参数与结果](20261022-194940-further-cvtcolor/notes.md) |
| 20261022-194940-further-direct | success | [参数与结果](20261022-194940-further-direct/notes.md) |
| 20261022-195126-further-async-cvtcolor-b16 | success | [参数与结果](20261022-195126-further-async-cvtcolor-b16/notes.md) |
| 20261022-195126-further-async-cvtcolor-cudnn | success | [参数与结果](20261022-195126-further-async-cvtcolor-cudnn/notes.md) |
| 20261022-195126-further-async-cvtcolor-w4 | success | [参数与结果](20261022-195126-further-async-cvtcolor-w4/notes.md) |
| 20261022-195126-further-decoder1 | success | [参数与结果](20261022-195126-further-decoder1/notes.md) |
| 20261022-195126-further-decoder2 | success | [参数与结果](20261022-195126-further-decoder2/notes.md) |
| 20261022-195339-further-decoder1-score003 | success | [参数与结果](20261022-195339-further-decoder1-score003/notes.md) |
| 20261022-195339-further-decoder1-score004 | success | [参数与结果](20261022-195339-further-decoder1-score004/notes.md) |
| 20261022-195339-further-decoder2-score004 | success | [参数与结果](20261022-195339-further-decoder2-score004/notes.md) |
| 20261022-195339-further-size512-full | success | [参数与结果](20261022-195339-further-size512-full/notes.md) |
| 20261022-195339-further-size576-full | success | [参数与结果](20261022-195339-further-size576-full/notes.md) |
| 20261022-195339-further-size576-half | success | [参数与结果](20261022-195339-further-size576-half/notes.md) |
| 20261022-195623-further-size512-half | success | [参数与结果](20261022-195623-further-size512-half/notes.md) |
| 20261022-195623-further-size544-half | success | [参数与结果](20261022-195623-further-size544-half/notes.md) |
| 20261022-195623-further-size576-decoder1 | success | [参数与结果](20261022-195623-further-size576-decoder1/notes.md) |
| 20261022-195623-further-size576-decoder2 | success | [参数与结果](20261022-195623-further-size576-decoder2/notes.md) |
| 20261022-195852-further-confirm-control | success | [参数与结果](20261022-195852-further-confirm-control/notes.md) |
| 20261022-195852-further-confirm-size544 | success | [参数与结果](20261022-195852-further-confirm-size544/notes.md) |

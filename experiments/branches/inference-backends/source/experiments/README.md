# 实验记录索引

代码位于 `exp/inference-backends` 分支；`baseline-pytorch` 指向优化前的 `cd5fed1`。推理与部署代码提交为 `8b5e90e`，性能剖析工具提交为 `dfcd19d`。历史记录中的基准 SHA、dirty 标记和补丁保留原样，表示实际运行时状态。

| 记录 | 类型 | 分支 | 状态 |
| --- | --- | --- | --- |
| [20261016T131655Z-inference-backends-snapshot](20261016T131655Z-inference-backends-snapshot/notes.md) | 当前代码完整快照与历史证据归档 | `exp/inference-backends` | dirty；完整补丁已保存；本次未新运行实验 |

历史汇总见仓库根目录 `OPTIMIZATION_EXPERIMENTS.md`；其部分待办已过时，以各记录的证据和限制为准。新运行使用独立目录，保存实际参数、代码版本、环境、命令和结果，不覆盖旧记录。

## 已执行的瓶颈实验


[本次部署与压缩实验结果](ADVANCED_RESULTS_20261016.md)（含低精度与失败记录）。

性能分析记录（算子分析、流水线耗时占比）位于 `exp/performance-analysis` 分支。

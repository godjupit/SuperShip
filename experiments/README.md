# 实验记录索引

代码位于 `exp/inference-backends` 分支；`baseline-pytorch` 指向优化前的 `cd5fed1`。推理与部署代码提交为 `8b5e90e`，性能剖析工具提交为 `dfcd19d`。历史记录中的基准 SHA、dirty 标记和补丁保留原样，表示实际运行时状态。

| 记录 | 类型 | 分支 | 状态 |
| --- | --- | --- | --- |
| [20261016T131655Z-inference-backends-snapshot](20261016T131655Z-inference-backends-snapshot/notes.md) | 当前代码完整快照与历史证据归档 | `exp/inference-backends` | dirty；完整补丁已保存；本次未新运行实验 |

历史汇总见仓库根目录 `OPTIMIZATION_EXPERIMENTS.md`；其部分待办已过时，以各记录的证据和限制为准。新运行使用独立目录，保存实际参数、代码版本、环境、命令和结果，不覆盖旧记录。

## 已执行的瓶颈实验

- [20261016-attention-profile-01](20261016-attention-profile-01/notes.md)：PyTorch FP32、batch=8、真实验证集 40 张，三轮 profiler；Self Attention 约 7.33%，卷积约 28.92%。

[本次部署与压缩实验结果](ADVANCED_RESULTS_20261016.md)（含低精度与失败记录）。

- [20261016T141336Z-fastest-pipeline-profile](20261016T141336Z-fastest-pipeline-profile/notes.md)：最快 CUDA Graph 配置的完整 val 流水线占比；正常 9.731s，AP50=0.9170。

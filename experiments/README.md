# 优化资料中心

从根目录[精简时间日志](../OPTIMIZATION_EXPERIMENTS.md)进入；本目录汇集所有分支的优化方案、数据索引、历史过程和结果。

```text
experiments/
├── results/       2026-10-25归档的129份历史记录索引
├── branches/      归档时9个分支：源码快照、SHA、原台账
├── reports/       原根目录的详细优化报告、CSV及旧热点分析
├── guides/        常用命令、环境配置和上游文档
├── data/          统一数据集/权重入口与数据说明
├── artifacts/     本机大产物，按分支分区，Git忽略
├── catalog/       文件来源、版本、路径迁移清单
└── <实验ID>/      完整过程、参数、命令、逐轮结果、校验值
```

- [结果索引](results/README.md)；[每个分支自己的资料](branches/README.md)；[数据与产物](data/README.md)。
- [按分支运行方案](guides/branch-runs.md)；[当前主线命令](guides/commands.md)；[开发环境](guides/development.md)；[最新瓶颈候选的原命令](guides/bottleneck-commands-original.md)。
- [历史汇总报告](reports/)保留原记录；同一实验不同分支的版本保存在各分支源码快照中，合并来源见[catalog/files.json](catalog/files.json)。
- 原始实验ID目录保持原位置，避免破坏脚本ROOT和历史路径。源码快照保留原文件字节；根AGENTS.md仍是唯一协作规则入口。
- artifacts只在本机存在，不随Git复制。公开数据和基线权重保留根data/、weights/统一位置，本目录通过相对链接访问，不重复占空间。
- 各worktree/output继续访问各自独立产物区；原分支已提交代码不变。目录整理与官方规范同步现已落到main；原有分支与固定SHA快照继续保留。

- [20261026-075543-continued-sweep](20261026-075543-continued-sweep/notes.md)：50配置、150轮参考集计时、8对复测；最新Accepted258.409792ms，完整源码和全部配置保留在`exp/continued-sweep-20261026`，固定运行源码SHA见记录。

当前main默认运行已验证最快的`thread100-light`，配置在[configs/fastest.env](../configs/fastest.env)。2026-10-26 09:28用户要求停止优化；GPU已释放，未证实更快的实验实现保留在各自分支。后续实验目录独立保存，不改写上方历史归档索引。

| 近期记录 | 状态与结论 |
| --- | --- |
| [最新候选性能诊断](20261026-083341-profile-thread100/notes.md) | completed；259.258ms复测，定位CPU供给、退出、GPU搬运 |
| [最快候选同步main](20261026-083914-main-fastest/notes.md) | completed；默认入口/计时脚本统一配置，三轮261.306ms |
| [解码等待顺序](20261026-084102-decode-latewait/notes.md) | completed；8对未确认收益，未晋级 |
| [CPU/退出/GPU/落盘四方向](20261026-085041-broad-directions/notes.md) | completed；55次完整运行，均未确认稳定收益 |
| [nvJPEG后端与批量解码](20261026-091334-nvjpeg-backends/notes.md) | abandoned，按用户指令停止；30轮初筛已完成，最佳498.191ms慢于同期OpenCV253–256ms |

以上均为本机RTX4090公开200张参考集结果；validation/hidden是否实测以各记录为准，不能作为官方隐藏成绩。历史原始产物、分支与worktree继续保留，main/output中的链接仅提供本机访问。

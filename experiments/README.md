# 优化资料中心

从根目录[精简时间日志](../OPTIMIZATION_EXPERIMENTS.md)进入；本目录汇集所有分支的优化方案、数据索引、历史过程和结果。

```text
experiments/
├── results/       全部129份实验记录的JSON/CSV索引
├── branches/      9个分支：源码快照、提交SHA、各自原台账
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

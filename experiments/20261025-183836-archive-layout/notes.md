# 目录整理与全分支资料归档

实验20261025-183836-archive-layout；负责人Codex /root；状态completed；工作分支exp/archive-layout-20261025；基于3b3ee83（固定主线）。本次只做目录、索引与脚本路径整理，不改变推理算法、不跑GPU、不提交竞赛。完成时间2026-10-25T18:53:09.866555。

## 结果

主目录保留官方run.sh、源码、配置、必要公开数据/权重和精简OPTIMIZATION_EXPERIMENTS.md。15个原根目录文件迁移至reports/guides、tools/benchmark和tools/dev；路径映射见../catalog/path-moves.json。全部优化过程汇集在experiments，保留原实验ID以兼容历史脚本。

9个分支的5486个已提交文件以固定SHA导出源码快照，逐字节对照Git原提交检查；根AGENTS.md仍是唯一协作规则入口，没有导出新的AGENTS。分支的实际代码和原实验目录未移动或修改，各自原台账也保留。canonical实验记录合并816个文件，新旧不同版本全部保存在相应分支快照，来源/选择SHA见../catalog/files.json。统一索引129份notes，结果表在../results/。

约945MB本机输出统一存放在experiments/artifacts/<branch>/。原9个worktree/output替换为指向本分支产物的链接，文件用同盘rename迁移，未重复复制或删除；原两份散落性能采样移至artifacts/main/legacy-profiles，迁移前后SHA256一致。公开data/SuperShip和weights保持原实际位置，experiments/data下提供相对入口，其他分支数据链接继续可用。大产物、本机合并备份、原始本机回执全部被Git忽略。

## 原有修改与主目录同步

main开始时已有未完成合并及3处冲突。整理前已把其Git index、MERGE_HEAD/MERGE_MSG、暂存/工作区diff和所有已改文件备份到本机artifacts/local-state/20261025-183836-archive-layout/，未复制.local或凭证。同步只涉及本任务目录/文档；核对Git index的全部暂存条目完全未变，12个其他运行时/官方修改文件字节未变。README仅更新迁移路径，冲突选择与标记保留；独立整理分支有清晰的新README，主目录可先看../guides/project-overview.md和根精简日志。

因main已有未解决合并，不能安全创建仅本任务的main提交。本次文件已实际同步到主文件夹，完整可审查提交推送到exp/archive-layout-20261025；未处理或纳入其他运行时代码冲突。迁移实际位置/原路径兼容链接和备份位置见本机artifacts/relocations.json，便于回退；未删除历史分支或worktree。

## 验证

9分支5486个源码文件逐字节与Git归档比对；816个canonical记录校验SHA256；59条核心导航链接有效。4个迁移后的计时/评分/验证脚本使用无GPU的Python捕获器检查cwd和参数，均定位项目根目录；shell语法及setup --help通过。原output链接、数据/权重链接和分支工作区状态核对通过。未对带原有冲突的main运行推理测试，也不宣称重新验证性能。

所有原数据、源码、参数、历史计时、不利结果和回执均保留；原本缺少/仅本机可用的产物仍按索引明确标注，不以移动路径冒充跨机可复现。

后续收尾：20261025-190006-main-git-finish已在main解决原上游合并并提交，目录整理也在主目录提交，不再处于“仅独立分支提交”的状态；上述备份与当时检查仍保留。

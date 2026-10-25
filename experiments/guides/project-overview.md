# SuperShip

遥感舰船检测推理优化项目。主目录保留运行入口和源码，优化资料统一归档在[experiments/](../README.md)。

- [精简优化日志](../../OPTIMIZATION_EXPERIMENTS.md)：时间、方案、关键结果和候选状态。
- [全部过程与结果](../README.md)：实验原记录、JSON/CSV索引、历史报告。
- [分支源码与原台账](../branches/README.md)：按提交SHA保存，原worktree继续独立使用。
- [运行与评测命令](../guides/commands.md)：评测脚本集中在tools/benchmark/。
- [数据与产物](../data/README.md)：公开数据、权重、每个分支的本机原始输出。
- [环境配置](../guides/development.md)：脚本集中在tools/dev/。
- [赛题说明](../../COMPETITION.md)、[数据说明](../../DATA_NOTICE.md)、[上游文档](../guides/upstream.md)。

```text
run.sh                   官方worker入口
engine/、supership/      主线运行源码
configs/、tests/         模型配置与检查
tools/benchmark/         参考计时、优化计时、评分、验证
tools/dev/               本机环境工具
data/、weights/          统一公开数据与权重
experiments/             全部优化资料；artifacts为本机大产物
OPTIMIZATION_EXPERIMENTS.md 精简时间日志
```

主线代码保持原版本，各方向的代码按分支保留。公开数据/权重入口和run.sh接口继续使用；基准计时仍覆盖READY后的全部输入处理、写盘与进程结束。

主线已合并官方`42460fba`规范与评分修复，并保留原优化开关；[合并后的完整说明](../guides/main-upstream-sync.md)。历史性能记录按原SHA保存，当前主线后续计时需重新建立基线。

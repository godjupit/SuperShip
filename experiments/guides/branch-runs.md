# 按分支使用优化方案

主目录使用已同步官方42460fba规范的main，并保留既有优化入口；各快照仍固定在各自历史SHA。各优化方向的原worktree继续独立使用，原output路径自动访问主目录experiments/artifacts/对应分支。源码快照用于固定版本查阅；每个快照的data、weights入口复用主目录。

| 方案 | 代码入口 |
| --- | --- |
| 主线Conv-BN融合 | tools/benchmark/benchmark_optimized.sh |
| 历史FP16权重/Linear/pack三项组合 | experiments/branches/kernel-sweep-20261024/source/benchmark_optimized.sh |
| 新瓶颈候选 | experiments/branches/bottleneck-opt-20261025/source/benchmark_bottleneck.sh |

从主目录运行已固定的候选源码，并把新结果保存到独立产物目录：

```bash
PYTHON_BIN=/home/ubuntu/.cache/supership-venv/bin/python \
OUTPUT_FILE="$PWD/experiments/artifacts/bottleneck-opt-20261025/manual-$(date +%Y%m%d-%H%M%S)/reference.json" \
bash experiments/branches/bottleneck-opt-20261025/source/benchmark_bottleneck.sh
```

复用旧精度与时间之前先核实配置、GPU/数据/协议以及SHA；历史约304ms与本轮316.5ms不能直接视为同轮收益。原机器路径的旧命令只作历史证据，工作目录和新输出路径按此说明选择。

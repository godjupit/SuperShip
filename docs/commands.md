# 运行与评测

在项目根目录运行，先准备 Python 依赖、`data/SuperShip/` 和 `weights/baseline.pth`。可通过 `PYTHON_BIN` 指定解释器。

```bash
bash run.sh --worker
RUNS=3 bash benchmark_optimized.sh
bash score_reference.sh
```

主线默认使用 `configs/fastest.env`。历史分支选择匹配的 `configs/presets/` 参数；640 保守版本在 `exp/rtx4090-e2e` 中先执行：

```bash
source configs/presets/conservative640.env
```

计时覆盖 READY 后输入访问、全部输出写盘与进程退出。参考集、validation 和 hidden 的精度分别报告；公开参考集结果不代表隐藏集成绩。需要复测时使用新的输出路径。旧日志、预测、引擎及性能分析产物已按用户要求删除，须重新生成。

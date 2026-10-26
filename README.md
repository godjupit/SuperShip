# SuperShip

遥感舰船检测推理优化项目。仓库保留运行源码、模型配置、精选版本和必要文档；旧实验结果、重复源码归档、日志和预测已清理。

- [版本与候选索引](OPTIMIZATION_EXPERIMENTS.md)
- [运行参数](configs/presets/README.md)
- [运行命令](docs/commands.md)
- [赛题说明](COMPETITION.md)、[数据说明](DATA_NOTICE.md)

`engine/`、`supership/` 是模型与推理代码，`configs/` 保存参数，`tests/` 保存检查，`tools/` 保存评测和开发工具。本机数据位于 `data/SuperShip/`，基线权重位于 `weights/baseline.pth`；新输出写入 Git 忽略的 `output/`。

主线默认运行已验证的 `thread100-light`，配置在 `configs/fastest.env`；环境变量可覆盖默认值，`PIPELINE=standard` 选择标准推理。历史分支保留各自实现和默认行为，复现时显式加载匹配参数。

```bash
bash run.sh --worker
```

清理使用普通提交与分支删除，未改写 Git 历史。历史提交仍可能包含旧实验文件；工作目录和保留分支的最新提交只保留精选参数及精简索引。

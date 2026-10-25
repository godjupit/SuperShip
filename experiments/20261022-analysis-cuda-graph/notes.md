# 20261022-analysis-cuda-graph

RTX 4090，200 张公开参考图像，官方协议独立运行三次。

命令：

```bash
PYTHON_BIN=/home/ubuntu/.cache/supership-venv/bin/python BACKEND=cuda_graph BATCH_COPY=1 WARMUP=3 PRECISION=fp32 PIN_MEMORY=1 NON_BLOCKING=1 BUFFERED_JSON=1 NUM_WORKERS=4 PREFETCH_FACTOR=2 BATCH_SIZE=8 RUNS=3 bash benchmark_reference.sh > output/submissions/20261022-analysis-cuda-graph/supership.out 2>&1
```

代码版本：`7ffd352b35acd06b2742a40d4bf7b8923debdc4a`。未修改推理代码。权重、数据标识和环境见本目录 JSON。原始日志与预测结果存放于 `/home/ubuntu/SuperShip-analysis/output/submissions/20261022-analysis-cuda-graph`，不提交大型产物。

三次耗时：[3.071232824, 3.22106285, 3.274563741] 秒；中位数：3.221062850 秒；参考集各轮 AP50：[0.7935, 0.7935, 0.7935]。隐藏集精度未测。

公开参考集的 203 个 SHA256SUMS 条目已逐一验证。AP50 只用于本地比较；服务器仅解析日志计时，不代表隐藏集精度审核。

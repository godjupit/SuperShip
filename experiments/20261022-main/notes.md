# 20261022-main

RTX 4090，200 张公开参考图像，官方协议独立运行三次。

命令：

```bash
PYTHON_BIN=/home/ubuntu/.cache/supership-venv/bin/python RUNS=3 bash benchmark_reference.sh > output/submissions/20261022-main/supership.out 2>&1
```

代码版本：`5adf03b8652bc1eaa7b201f45cf97a9cad1c6f5f`。未修改推理代码。权重、数据标识和环境见本目录 JSON。原始日志与预测结果存放于 `/home/ubuntu/SuperShip-main 2/output/submissions/20261022-main`，不提交大型产物。

三次耗时：[6.079042092, 5.128391426, 5.125821636] 秒；中位数：5.128391426 秒；参考集各轮 AP50：[0.7935, 0.7935, 0.7935]。隐藏集精度未测。

公开参考集的 203 个 SHA256SUMS 条目已逐一验证。AP50 只用于本地比较；服务器仅解析日志计时，不代表隐藏集精度审核。

正式提交回执：

```text
Submission Time (Asia/Shanghai): 2026-10-22 19:10:20
Server Message: Submission Accepted; Performance: 5.128391426 s; OK: median runtime = 5.128391426 s (timing JSON); timing parsed only.
```

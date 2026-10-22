# RTX 4090 分阶段诊断

200 张公开参考图像，CUDA Graph FP32，batch=8；一次同步诊断，非正式三轮日志。GPU 前向 0.377 秒，读取等待 1.164 秒；函数内部 2.092 秒，端到端 3.122 秒，差额约 1.03 秒包括进程退出与计时轮询。阶段同步会改变重叠，仅用于定位瓶颈。未重测 AP50。完整命令、版本、权重摘要见 config.json，阶段明细见 stages.json；原始日志位于 output/submissions/20261022-stage-profile/。

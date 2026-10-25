# distilled_epoch1

运行前已保存完整 dirty 补丁，未提交用户改动。

命令：`bash evaluate.sh val --runs 1 --output-dir output/experiments/distilled_epoch1`

参数：`{"MODEL_WEIGHTS": "output/compression_epoch1/distilled.pth", "BACKEND": "torch", "PRECISION": "fp32", "BATCH_SIZE": "8", "BATCH_COPY": "1", "WARMUP": "3", "PIN_MEMORY": "1", "NON_BLOCKING": "1", "BUFFERED_JSON": "1", "NUM_WORKERS": "4", "PREFETCH_FACTOR": "2", "RUNS": "1"}`

训练命令：`.venv/bin/python supership/compress.py --steps -1 --epochs 1 --output-dir output/compression_epoch1`

完成 1,203 步；训练参数见 `output/compression_epoch1/parameters.json`，逐步损失见 `training.jsonl`。本次 AP50=0.9087，低于未训练剪枝模型 0.9112，此配置不采用；权重保留。

# 20261022-fast-fp16-score001

源码版本：`038904fbbf31763907706b64dc1f98bc2e39e896`。全部参数及环境见本目录 JSON。

```bash
PYTHON_BIN=/home/ubuntu/.cache/supership-venv/bin/python PIPELINE=fast PRECISION=fp16 BACKEND=cuda_graph BATCH_SIZE=8 NUM_WORKERS=8 RUNS=3 PIPELINE_DEPTH=3 SCORE_THRESHOLD=0.001 IMAGE_DECODER=pil VECTORIZED_RESULTS=1 CHANNELS_LAST=1 MODEL_DEPLOY=0 FAST_EXIT=1 TORCH_THREADS=1 bash benchmark_reference.sh > output/submissions/20261022-fast-fp16-score001/supership.out 2>&1
```

原始日志、三轮完整预测及逐轮精度评分保存在 `/home/ubuntu/SuperShip-optimize/output/submissions/20261022-fast-fp16-score001`（本机忽略目录）。计时使用官方脚本，图像和元数据在 READY 后才访问；初始化只使用合成输入。每轮处理全部 200 张参考图像。隐藏集精度未测。

结果：

```json
{
  "status": "success",
  "runs_seconds": [
    1.366587599,
    1.366599145,
    1.266127631
  ],
  "median_seconds": 1.366587599,
  "reference_ap50_per_run": [
    0.7926,
    0.7926,
    0.7926
  ],
  "detections_per_run": [
    59977,
    59977,
    59977
  ],
  "images_with_detections_per_run": [
    200,
    200,
    200
  ],
  "hidden_ap50": null,
  "timing_scope": "official complete worker protocol: input access to output fsync and process exit; excludes initialization",
  "raw_log_path": "/home/ubuntu/SuperShip-optimize/output/submissions/20261022-fast-fp16-score001/supership.out",
  "raw_log_sha256": "8b38c0a1b18f0346b3346bed4fa5fa586a71dda7c7f3651eded5049b0813797f",
  "artifact_directory": "/home/ubuntu/SuperShip-optimize/output/submissions/20261022-fast-fp16-score001",
  "reduction_vs_previous_submission_percent": 56.9113240942443,
  "ap50_reference_baseline": 0.7935,
  "submitted": false
}
```

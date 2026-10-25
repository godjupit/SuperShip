# 20261022-fast-fp32-contiguous

源码版本：`038904fbbf31763907706b64dc1f98bc2e39e896`。全部参数及环境见本目录 JSON。

```bash
PYTHON_BIN=/home/ubuntu/.cache/supership-venv/bin/python PIPELINE=fast PRECISION=fp32 BACKEND=cuda_graph BATCH_SIZE=8 NUM_WORKERS=8 RUNS=3 PIPELINE_DEPTH=3 SCORE_THRESHOLD=0 IMAGE_DECODER=pil VECTORIZED_RESULTS=1 CHANNELS_LAST=0 MODEL_DEPLOY=0 FAST_EXIT=1 TORCH_THREADS=1 bash benchmark_reference.sh > output/submissions/20261022-fast-fp32-contiguous/supership.out 2>&1
```

原始日志、三轮完整预测及逐轮精度评分保存在 `/home/ubuntu/SuperShip-optimize/output/submissions/20261022-fast-fp32-contiguous`（本机忽略目录）。计时使用官方脚本，图像和元数据在 READY 后才访问；初始化只使用合成输入。每轮处理全部 200 张参考图像。隐藏集精度未测。

结果：

```json
{
  "status": "success",
  "runs_seconds": [
    1.417083007,
    1.2664223,
    1.416726365
  ],
  "median_seconds": 1.416726365,
  "reference_ap50_per_run": [
    0.7931,
    0.7931,
    0.7931
  ],
  "detections_per_run": [
    59974,
    59974,
    59974
  ],
  "images_with_detections_per_run": [
    200,
    200,
    200
  ],
  "hidden_ap50": null,
  "timing_scope": "official complete worker protocol: input access to output fsync and process exit; excludes initialization",
  "raw_log_path": "/home/ubuntu/SuperShip-optimize/output/submissions/20261022-fast-fp32-contiguous/supership.out",
  "raw_log_sha256": "c9eff6ff7662504f58fe0bdd315c0a10d53bd68225f3630c54964c4a2a7fb095",
  "artifact_directory": "/home/ubuntu/SuperShip-optimize/output/submissions/20261022-fast-fp32-contiguous",
  "reduction_vs_previous_submission_percent": 55.33044260514737,
  "ap50_reference_baseline": 0.7935,
  "submitted": false
}
```

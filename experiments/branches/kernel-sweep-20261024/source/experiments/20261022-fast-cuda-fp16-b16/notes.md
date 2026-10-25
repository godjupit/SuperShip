# 20261022-fast-cuda-fp16-b16

源码版本：`6e37ca3cf25f996840a3f2c112816d1fd44469d8`。全部参数及环境见本目录 JSON。

```bash
PYTHON_BIN=/home/ubuntu/.cache/supership-venv/bin/python PIPELINE=fast PRECISION=fp16 BACKEND=cuda_graph BATCH_SIZE=16 NUM_WORKERS=8 RUNS=3 PIPELINE_DEPTH=3 SCORE_THRESHOLD=0 IMAGE_DECODER=cuda VECTORIZED_RESULTS=1 CHANNELS_LAST=1 MODEL_DEPLOY=0 FAST_EXIT=1 TORCH_THREADS=1 bash benchmark_reference.sh > output/submissions/20261022-fast-cuda-fp16-b16/supership.out 2>&1
```

原始日志、三轮完整预测及逐轮精度评分保存在 `/home/ubuntu/SuperShip-optimize/output/submissions/20261022-fast-cuda-fp16-b16`（本机忽略目录）。计时使用官方脚本，图像和元数据在 READY 后才访问；初始化只使用合成输入。每轮处理全部 200 张参考图像。隐藏集精度未测。

结果：

```json
{
  "status": "success",
  "runs_seconds": [
    1.918214319,
    1.968451797,
    1.867474605
  ],
  "median_seconds": 1.918214319,
  "reference_ap50_per_run": [
    0.7933,
    0.7933,
    0.7933
  ],
  "detections_per_run": [
    59978,
    59978,
    59978
  ],
  "images_with_detections_per_run": [
    200,
    200,
    200
  ],
  "hidden_ap50": null,
  "timing_scope": "official complete worker protocol: input access to output fsync and process exit; excludes initialization",
  "raw_log_path": "/home/ubuntu/SuperShip-optimize/output/submissions/20261022-fast-cuda-fp16-b16/supership.out",
  "raw_log_sha256": "487fc513366863c61724667f86ecdd70b16b3405caeb81b4f0076263b2d85bfd",
  "artifact_directory": "/home/ubuntu/SuperShip-optimize/output/submissions/20261022-fast-cuda-fp16-b16",
  "reduction_vs_previous_submission_percent": 39.51846543196176,
  "ap50_reference_baseline": 0.7935,
  "submitted": false
}
```

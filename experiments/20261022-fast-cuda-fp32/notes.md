# 20261022-fast-cuda-fp32

源码版本：`6e37ca3cf25f996840a3f2c112816d1fd44469d8`。全部参数及环境见本目录 JSON。

```bash
PYTHON_BIN=/home/ubuntu/.cache/supership-venv/bin/python PIPELINE=fast PRECISION=fp32 BACKEND=cuda_graph BATCH_SIZE=8 NUM_WORKERS=8 RUNS=3 PIPELINE_DEPTH=3 SCORE_THRESHOLD=0 IMAGE_DECODER=cuda VECTORIZED_RESULTS=1 CHANNELS_LAST=1 MODEL_DEPLOY=0 FAST_EXIT=1 TORCH_THREADS=1 bash benchmark_reference.sh > output/submissions/20261022-fast-cuda-fp32/supership.out 2>&1
```

原始日志、三轮完整预测及逐轮精度评分保存在 `/home/ubuntu/SuperShip-optimize/output/submissions/20261022-fast-cuda-fp32`（本机忽略目录）。计时使用官方脚本，图像和元数据在 READY 后才访问；初始化只使用合成输入。每轮处理全部 200 张参考图像。隐藏集精度未测。

结果：

```json
{
  "status": "success",
  "runs_seconds": [
    1.968371382,
    2.018703976,
    1.967773344
  ],
  "median_seconds": 1.968371382,
  "reference_ap50_per_run": [
    0.7933,
    0.7933,
    0.7933
  ],
  "detections_per_run": [
    59979,
    59979,
    59979
  ],
  "images_with_detections_per_run": [
    200,
    200,
    200
  ],
  "hidden_ap50": null,
  "timing_scope": "official complete worker protocol: input access to output fsync and process exit; excludes initialization",
  "raw_log_path": "/home/ubuntu/SuperShip-optimize/output/submissions/20261022-fast-cuda-fp32/supership.out",
  "raw_log_sha256": "5a03798ce967aa70569dbace689dc527d3c8fde7724582cdd39602c62459b793",
  "artifact_directory": "/home/ubuntu/SuperShip-optimize/output/submissions/20261022-fast-cuda-fp32",
  "reduction_vs_previous_submission_percent": 37.93700703619333,
  "ap50_reference_baseline": 0.7935,
  "submitted": false
}
```

# 20261022-fast-opencv-half-score005

源码版本：`05cb42251126a2bcf298ae0557c80db708fb4e90`。全部参数及环境见本目录 JSON。

```bash
PYTHON_BIN=/home/ubuntu/.cache/supership-venv/bin/python PIPELINE=fast PRECISION=fp16 BACKEND=cuda_graph BATCH_SIZE=8 NUM_WORKERS=8 RUNS=3 PIPELINE_DEPTH=3 SCORE_THRESHOLD=0.05 IMAGE_DECODER=opencv VECTORIZED_RESULTS=1 CHANNELS_LAST=1 MODEL_DEPLOY=0 FAST_EXIT=1 TORCH_THREADS=1 JPEG_REDUCTION=2 RESIZE_ANTIALIAS=1 bash benchmark_reference.sh > output/submissions/20261022-fast-opencv-half-score005/supership.out 2>&1
```

原始日志、三轮完整预测及逐轮精度评分保存在 `/home/ubuntu/SuperShip-optimize/output/submissions/20261022-fast-opencv-half-score005`（本机忽略目录）。计时使用官方脚本，图像和元数据在 READY 后才访问；初始化只使用合成输入。每轮处理全部 200 张参考图像。隐藏集精度未测。

结果：

```json
{
  "status": "success",
  "runs_seconds": [
    0.514560429,
    0.514572551,
    0.514668438
  ],
  "median_seconds": 0.514572551,
  "reference_ap50_per_run": [
    0.7808,
    0.7808,
    0.7808
  ],
  "detections_per_run": [
    5425,
    5425,
    5425
  ],
  "images_with_detections_per_run": [
    200,
    200,
    200
  ],
  "hidden_ap50": null,
  "timing_scope": "official complete worker protocol: input access to output fsync and process exit; excludes initialization",
  "raw_log_path": "/home/ubuntu/SuperShip-optimize/output/submissions/20261022-fast-opencv-half-score005/supership.out",
  "raw_log_sha256": "dd95e1aa65a7cb3a516d77019feb336f67427b8b71c447a28c4230bc8837cbef",
  "artifact_directory": "/home/ubuntu/SuperShip-optimize/output/submissions/20261022-fast-opencv-half-score005",
  "reduction_vs_previous_submission_percent": 83.77546386615722,
  "ap50_reference_baseline": 0.7935,
  "submitted": false
}
```

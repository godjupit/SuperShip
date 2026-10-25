# 20261022-fast-cuda-no-antialias

源码版本：`05cb42251126a2bcf298ae0557c80db708fb4e90`。全部参数及环境见本目录 JSON。

```bash
PYTHON_BIN=/home/ubuntu/.cache/supership-venv/bin/python PIPELINE=fast PRECISION=fp16 BACKEND=cuda_graph BATCH_SIZE=8 NUM_WORKERS=8 RUNS=3 PIPELINE_DEPTH=3 SCORE_THRESHOLD=0 IMAGE_DECODER=cuda VECTORIZED_RESULTS=1 CHANNELS_LAST=1 MODEL_DEPLOY=0 FAST_EXIT=1 TORCH_THREADS=1 JPEG_REDUCTION=1 RESIZE_ANTIALIAS=0 bash benchmark_reference.sh > output/submissions/20261022-fast-cuda-no-antialias/supership.out 2>&1
```

原始日志、三轮完整预测及逐轮精度评分保存在 `/home/ubuntu/SuperShip-optimize/output/submissions/20261022-fast-cuda-no-antialias`（本机忽略目录）。计时使用官方脚本，图像和元数据在 READY 后才访问；初始化只使用合成输入。每轮处理全部 200 张参考图像。隐藏集精度未测。

结果：

```json
{
  "status": "success",
  "runs_seconds": [
    1.867321036,
    1.867476396,
    1.91779523
  ],
  "median_seconds": 1.867476396,
  "reference_ap50_per_run": [
    0.8024,
    0.8024,
    0.8024
  ],
  "detections_per_run": [
    59981,
    59981,
    59981
  ],
  "images_with_detections_per_run": [
    200,
    200,
    200
  ],
  "hidden_ap50": null,
  "timing_scope": "official complete worker protocol: input access to output fsync and process exit; excludes initialization",
  "raw_log_path": "/home/ubuntu/SuperShip-optimize/output/submissions/20261022-fast-cuda-no-antialias/supership.out",
  "raw_log_sha256": "4ee5edf7525a45ee215598f582732c2e7904c4ff465c3b058d457b00797ac24a",
  "artifact_directory": "/home/ubuntu/SuperShip-optimize/output/submissions/20261022-fast-cuda-no-antialias",
  "reduction_vs_previous_submission_percent": 41.11823841532408,
  "ap50_reference_baseline": 0.7935,
  "submitted": false
}
```

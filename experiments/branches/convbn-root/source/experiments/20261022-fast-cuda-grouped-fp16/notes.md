# 20261022-fast-cuda-grouped-fp16

源码版本：`05cb42251126a2bcf298ae0557c80db708fb4e90`。全部参数及环境见本目录 JSON。

```bash
PYTHON_BIN=/home/ubuntu/.cache/supership-venv/bin/python PIPELINE=fast PRECISION=fp16 BACKEND=cuda_graph BATCH_SIZE=8 NUM_WORKERS=8 RUNS=3 PIPELINE_DEPTH=3 SCORE_THRESHOLD=0 IMAGE_DECODER=cuda VECTORIZED_RESULTS=1 CHANNELS_LAST=1 MODEL_DEPLOY=0 FAST_EXIT=1 TORCH_THREADS=1 JPEG_REDUCTION=1 RESIZE_ANTIALIAS=1 bash benchmark_reference.sh > output/submissions/20261022-fast-cuda-grouped-fp16/supership.out 2>&1
```

原始日志、三轮完整预测及逐轮精度评分保存在 `/home/ubuntu/SuperShip-optimize/output/submissions/20261022-fast-cuda-grouped-fp16`（本机忽略目录）。计时使用官方脚本，图像和元数据在 READY 后才访问；初始化只使用合成输入。每轮处理全部 200 张参考图像。隐藏集精度未测。

结果：

```json
{
  "status": "success",
  "runs_seconds": [
    1.867983835,
    1.968426698,
    1.86754831
  ],
  "median_seconds": 1.867983835,
  "reference_ap50_per_run": [
    0.7935,
    0.7935,
    0.7935
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
  "raw_log_path": "/home/ubuntu/SuperShip-optimize/output/submissions/20261022-fast-cuda-grouped-fp16/supership.out",
  "raw_log_sha256": "7208b4cf8a33b34e97da98a831e93c5e44ceb8ca5d3e8e9424414fd2ec6712eb",
  "artifact_directory": "/home/ubuntu/SuperShip-optimize/output/submissions/20261022-fast-cuda-grouped-fp16",
  "reduction_vs_previous_submission_percent": 41.10223880093498,
  "ap50_reference_baseline": 0.7935,
  "submitted": false
}
```

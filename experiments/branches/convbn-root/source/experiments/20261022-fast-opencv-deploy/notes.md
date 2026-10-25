# 20261022-fast-opencv-deploy

源码版本：`6e37ca3cf25f996840a3f2c112816d1fd44469d8`。全部参数及环境见本目录 JSON。

```bash
PYTHON_BIN=/home/ubuntu/.cache/supership-venv/bin/python PIPELINE=fast PRECISION=fp16 BACKEND=cuda_graph BATCH_SIZE=8 NUM_WORKERS=8 RUNS=3 PIPELINE_DEPTH=3 SCORE_THRESHOLD=0 IMAGE_DECODER=opencv VECTORIZED_RESULTS=1 CHANNELS_LAST=1 MODEL_DEPLOY=1 FAST_EXIT=1 TORCH_THREADS=1 bash benchmark_reference.sh > output/submissions/20261022-fast-opencv-deploy/supership.out 2>&1
```

原始日志、三轮完整预测及逐轮精度评分保存在 `/home/ubuntu/SuperShip-optimize/output/submissions/20261022-fast-opencv-deploy`（本机忽略目录）。计时使用官方脚本，图像和元数据在 READY 后才访问；初始化只使用合成输入。每轮处理全部 200 张参考图像。隐藏集精度未测。

结果：

```json
{
  "status": "success",
  "runs_seconds": [
    0.81545275,
    0.865501785,
    0.865431769
  ],
  "median_seconds": 0.865431769,
  "reference_ap50_per_run": [
    0.8027,
    0.8027,
    0.8027
  ],
  "detections_per_run": [
    59985,
    59985,
    59985
  ],
  "images_with_detections_per_run": [
    200,
    200,
    200
  ],
  "hidden_ap50": null,
  "timing_scope": "official complete worker protocol: input access to output fsync and process exit; excludes initialization",
  "raw_log_path": "/home/ubuntu/SuperShip-optimize/output/submissions/20261022-fast-opencv-deploy/supership.out",
  "raw_log_sha256": "c472a0165387d4a4181b9da219659e4e5057d8bc1c9de8fa887941aae7a3d4f2",
  "artifact_directory": "/home/ubuntu/SuperShip-optimize/output/submissions/20261022-fast-opencv-deploy",
  "reduction_vs_previous_submission_percent": 72.71282935665961,
  "ap50_reference_baseline": 0.7935,
  "submitted": false
}
```

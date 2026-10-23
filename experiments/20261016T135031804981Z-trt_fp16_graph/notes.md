# trt_fp16_graph

运行前已保存完整 dirty 补丁，未提交用户改动。

命令：`bash evaluate.sh val --runs 1 --output-dir output/experiments/trt_fp16_graph`

参数：`{"ENGINE_PATH": "output/deploy/model.fp16.engine", "MODEL_WEIGHTS": "weights/baseline.pth", "BACKEND": "tensorrt", "CUDA_GRAPH": "1", "PRECISION": "fp32", "BATCH_SIZE": "8", "BATCH_COPY": "1", "WARMUP": "0", "PIN_MEMORY": "1", "NON_BLOCKING": "1", "BUFFERED_JSON": "1", "NUM_WORKERS": "4", "PREFETCH_FACTOR": "2", "RUNS": "1"}`

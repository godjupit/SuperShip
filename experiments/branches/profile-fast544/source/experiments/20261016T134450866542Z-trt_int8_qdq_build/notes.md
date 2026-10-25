# trt_int8_qdq_build

运行前已保存完整 dirty 补丁，未提交用户改动。

命令：`.venv/bin/python supership/deploy.py build --precision int8 --int8-mode qdq --calib-samples 32 --optimization-level 1 --output output/deploy/model.int8-qdq.engine`

参数：`{"PRECISION": "int8"}`

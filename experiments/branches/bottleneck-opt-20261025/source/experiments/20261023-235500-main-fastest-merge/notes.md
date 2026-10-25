# 当前最快融合方案合入main

状态completed；用户授权自动合入。父main `5231b92fabf4a7efd125b046719510b4f4fc8e3c`；融合分支 `c6d860d6b09e4566494ab2314f6482f1bb0a2a5d`。融合合并提交 `0ada0c4`，诊断文档合并提交 `acdc948`，本次运行源码完整提交 **`49f97bae8211a578d81b87a9218220bdb9a6ce84`**。参数见config.json，精确命令见commands.json，校验值和依赖见metrics.json。

## 合并内容与保留项

- 合入99对Conv-BN融合、544输入、FP16、channels-last、CUDA Graph、OpenCV半尺寸解码、8读取线程、预取深度3、异步结果回传。benchmark_optimized.sh默认FUSE_CONV_BN=1；可显式设0复现未融合对照。
- 保留main的AGENTS.md、DEV_SETUP.md、setup_dev.sh、历史成绩、全部不利结果与脱敏回执。两个现有未跟踪文件ship_prof.nsys-rep和ship_prof.sqlite未修改、未提交。运行时tracked源码clean，只有这两个无关报告未跟踪，完整记录dirty范围，未将整个工作区称为clean。
- 合入Nsight诊断工具和优化过程文档；其热点测量来自未融合544对照，已明确不能作为当前BN=0融合方案的热点排名。
- 保留保守候选；本次使用现有已验证融合参数，不引入新模型假设。

## 合并后实际验证

GPU0 RTX4090、驱动550.142，本次独占开始于2026-10-23 23:55（正式进程起止见metrics.json），23:57结束后核对空闲。Python3.12.8、PyTorch2.6.0+cu124、OpenCV4.11.0；无额外性能环境覆盖，config.json保存实际参数。官方权重weights/baseline.pth与公开reference/val数据SHA256见metrics.json，隐藏集未访问。

三轮参考集：**0.330820520 / 0.324560194 / 0.346345743秒**，中位数 **0.330820520秒**；逐轮reference AP50为 **0.7817 / 0.7823 / 0.7814**。每轮均处理200张且通过官方输出校验，检测数6297/6303/6303。完整验证集1030张、40353检测，输出校验通过，AP50=**0.9057**，单次端到端1.243855975秒。参考门槛0.77763，验证门槛0.89866，分别通过；hidden AP50未测。

使用未修改的官方benchmark_submission.py与submission.py，计时从READY后开始，包含输入访问、所有输出落盘/fsync及进程组结束，初始化排除。三轮独立完整日志，没有挑选/拼接；与历史三轮0.340258450秒属于不同运行，不将波动差异宣称为新代码收益。

检查：56 passed, 1 skipped（可选TensorRT引擎缺失）；shell语法、Python编译、Git空白检查通过。合并后推理源码与exp/convbn-root的supership/和tests/逐文件相同；仅优化wrapper默认选择融合。没有改评分器或官方计时器。

## 复现与产物

```bash
PYTHON_BIN=/home/ubuntu/.cache/supership-venv/bin/python bash benchmark_optimized.sh
# 未融合对照：
PYTHON_BIN=/home/ubuntu/.cache/supership-venv/bin/python FUSE_CONV_BN=0 bash benchmark_optimized.sh
```

本次使用commands.json中的官方直接命令及config.json环境，输出独立保存，避免覆盖默认文件。大日志和预测位于 `/home/ubuntu/SuperShip-main 2/output/20261023-235500-main-fastest-merge/`，仅本机可用；全部SHA256在metrics.json，离机需重跑。参考三轮与验证一轮都重新评分，未复用历史AP50。

本次只做Git合并、验证、提交和推送，未再次提交竞赛成绩。最近服务器Accepted仍为此前融合方案0.340258450秒；回执保留在experiments/20261023-232613-submit-convbn/，官方隐藏集最优未知。

# Nsight CUDA 12.4兼容修复

实验 `20261023-224506-nsys-cuda124`，负责人Codex /root，分支exp/profile-fast544，状态completed。父实验20261023-223213-profile-fast544；父提交`c189fe62e4428a07f34eda61e3cb59ddefc2f7ed`。补丁source.patch SHA256 `8151c78191b0d2a938bf1cacf0ca529bc3f0d06a1889923891c17ac01771674c`；最终Git提交保存完整版本。

用户运行旧版Nsight 2022.4.2.1采集后遇到`Unknown runtime API function index: 440`和随后StringStorage错误，尽管推理完成，报告解析不完整。结合当前PyTorch CUDA12.4与旧工具版本，判断为工具/API兼容问题；换用2024.2.3.38后完整采集、导入及stats均成功，退出码0。CPU context switch不支持是独立警告，命令显式使用`--cpuctxsw=none`关闭该采集项。

从[NVIDIA官方redistribution清单](https://developer.download.nvidia.com/compute/cuda/redist/redistrib_12.5.0.json)定位2024.2.3.38归档，下载自[官方地址](https://developer.download.nvidia.com/compute/cuda/redist/nsight_systems/linux-x86_64/nsight_systems-linux-x86_64-2024.2.3.38-archive.tar.xz)，已核对SHA256 `36b457ec34572699c7ddba94aec659a02d4ec78fe19bec7750918fd7e9b79119`。解压到`/home/ubuntu/.local/opt/nsight_systems-linux-x86_64-2024.2.3.38-archive`，建立`/home/ubuntu/.local/opt/nsight-systems-2024.2.3`软链接指向归档内`nsight-systems/2024.2.3`。归档顶层bin/nsys是未替换版本变量的CUDA打包模板，直接执行会报`#VERSION_RSPLIT#`，未使用它；实际二进制是`target-linux-x64/nsys`。系统默认/usr/local/cuda/bin/nsys仍为旧版，未修改系统CUDA、驱动或PATH。CLI独立运行方式参见[NVIDIA安装说明](https://docs.nvidia.com/nsight-systems/InstallationGuide/index.html)。

GPU0 RTX4090，驱动550.142，开始预检与结束均无其他GPU进程。设备预约从2026-10-23 22:45登记至22:48结束（北京时间）。CPU、Python、数据/权重版本同父实验；实际参数保存在config.json，校验和可从父实验metrics.json核对。本次仅增加工具脚本和benchmark_reference.sh的OUTPUT_FILE可选覆盖项，不更改模型、计时器、校验器或最快参数。

## 复现

```bash
cd /home/ubuntu/SuperShip-profile-fast544
bash tools/profile_nsys_fast544.sh
```

脚本自动选新版Nsight，设置RUNS=1、Python虚拟环境、CUDA Graph node tracing，完成profile并对同一报告运行stats。默认时间戳前缀保存在output/profiles/，预测使用对应独立文件，避免覆盖固定reference_submission.json。可传新前缀作为第一个参数；重名报告拒绝覆盖。也可用NSYS_BIN和PYTHON_BIN选择其他安装路径。

本次精确命令：

```bash
bash tools/profile_nsys_fast544.sh /home/ubuntu/SuperShip-profile-fast544/output/20261023-224506-nsys-cuda124/ship_prof
```

等效核心命令：

```bash
RUNS=1 PYTHON_BIN=/home/ubuntu/.cache/supership-venv/bin/python \
OUTPUT_FILE=output/profiles/new_prefix.predictions.json \
/home/ubuntu/.local/opt/nsight-systems-2024.2.3/target-linux-x64/nsys profile \
  --trace=cuda,nvtx,osrt --sample=none --cpuctxsw=none --cuda-graph-trace=node \
  -o output/profiles/new_prefix bash benchmark_optimized.sh
/home/ubuntu/.local/opt/nsight-systems-2024.2.3/target-linux-x64/nsys stats \
  --report cuda_gpu_kern_sum,cuda_api_sum,osrt_sum output/profiles/new_prefix.nsys-rep
```

## 结果和限制

一轮带profiler诊断耗时0.545753089秒，处理200张图像、6303个检测，未修改官方校验器通过；reference AP50=0.7818，高于参考基线0.7935的98%门槛0.77763。validation AP50=null，hidden AP50=null。只验证工具链，不是三轮正式性能比较，不晋级候选，也未提交竞赛成绩。旧版失败报告仍保留在用户原output/profiles目录。

report约5.7MiB、sqlite约15MiB；profile-stats.log包含CUDA kernel、CUDA API和OSRT统计，无TargetProfilingFailed及importer错误。原始产物在 `/home/ubuntu/SuperShip-profile-fast544/output/20261023-224506-nsys-cuda124`，仅本机可用，不随Git上传；SHA256见metrics.json。该报告采集整个进程树，包含初始化、cuDNN算法搜索、合成预热和实际推理；默认stats为整个采集区间的合计，不能直接解释为READY后的推理算子占比。

检查：本机实际执行profile和stats成功，官方输出校验与评分成功，bash -n及git diff --check通过。此次只修改工具脚本和输出路径选项，没有重跑模型测试套件；此前父实验48通过、1跳过不充作本次新测试结果。

# 最快544方案：NVIDIA性能工具与五类瓶颈

本次为诊断实验，不更改模型、精度、运行参数或正式成绩。分析文档：[优化过程.md](../../优化过程.md)。

源码提交：`f06e04e0240712460e8c56f49c99c0768ca836c1`，运行脚本已提交；Nsight Systems开始时工作区clean。随后未跟踪的分析文档/汇总脚本不参与模型执行，tracked推理代码无改动。`config.json`为实际环境覆盖，`metrics.json`保存依赖、数据、权重校验值；未设置其他性能开关。GPU0 RTX4090、驱动550.142，开始预检无其他GPU进程。

## 采样范围

`tools/reference/profile_fastest_range.py`在初始化及合成预热后开始采样，实际调用相同worker的Runtime.run处理200张公开参考图像。开始后读取元数据/图像，写盘fsync及GPU同步后停止采样。该程序直接调用worker，未经过竞赛READY握手，未提供正式端到端成绩。CUDA Graph包含GPU归一化、模型和GPU后处理；未单测模型前向。本次完整验证集和隐藏集AP50未测。历史正式成绩及验证集结果单独引用，不能充当本次新实测。

## 完整命令

工作目录 `/home/ubuntu/SuperShip-optimize`，路径均相对该目录。目录已使用，重跑时必须选择新目录及新预测文件名。原始大报告/预测只保存在本机 `output/profiles/20261023-fast544-bottlenecks/`；Git保留汇总和SHA256。

```bash
/home/ubuntu/.local/opt/nsight-systems-2024.2.3/target-linux-x64/nsys profile \
  --trace=cuda,nvtx,osrt --sample=none --cpuctxsw=none --cuda-graph-trace=node \
  --capture-range=cudaProfilerApi --capture-range-end=stop \
  -o output/profiles/20261023-fast544-bottlenecks/inference \
  /home/ubuntu/.cache/supership-venv/bin/python tools/reference/profile_fastest_range.py \
  --config experiments/20261022-195852-further-confirm-size544/config.json \
  --output output/profiles/20261023-fast544-bottlenecks/nsys-predictions.json
/home/ubuntu/.local/opt/nsight-systems-2024.2.3/target-linux-x64/nsys export \
  --type sqlite --output output/profiles/20261023-fast544-bottlenecks/inference.sqlite \
  output/profiles/20261023-fast544-bottlenecks/inference.nsys-rep
python3 tools/reference/summarize_nsys.py \
  output/profiles/20261023-fast544-bottlenecks/inference.sqlite \
  output/profiles/20261023-fast544-bottlenecks/recomputed-summary.json
/home/ubuntu/.cache/supership-venv/bin/python supership/score_submission.py \
  --gt data/SuperShip/reference/annotations/instances_reference.json \
  --submission output/profiles/20261023-fast544-bottlenecks/nsys-predictions.json
```

Nsight汇总按完整demangledName分组，时间为sum(end-start)，占比除以全部kernel累计时间。Memcpy单列。GPU覆盖率采用kernel与Memcpy区间的并集，窗口从首个到最后GPU活动，排除首批供给及最后输出；不代表SM忙碌率。CPU API耗时包含等待且可与GPU重叠，不可相加。

## Nsight Compute工具与失败记录

旧版ncu2022.3.0.0在初始化阶段报 `CUDA error: API call is not supported in the installed CUDA driver`，退出1，没有采集内核；另有section未加载警告。旧版未生成有效硬件指标。原命令为：

```bash
ncu --profile-from-start off --set basic \
  --kernel-name 'regex:.*(bn_fw_inf|float16_copy|CatArrayBatchedCopy|xmma_fprop).*' \
  --launch-count 8 --export output/profiles/20261023-fast544-bottlenecks/hotspots \
  /home/ubuntu/.cache/supership-venv/bin/python tools/reference/profile_fastest_range.py \
  --config experiments/20261022-195852-further-confirm-size544/config.json \
  --output output/profiles/20261023-fast544-bottlenecks/ncu-predictions.json
```

兼容版来自[NVIDIA CUDA12.5官方redistribution清单](https://developer.download.nvidia.com/compute/cuda/redist/redistrib_12.5.0.json)，归档2024.2.0.16，CLI报告2024.2.0.0，SHA256已验证，见metrics.json。仅解压至 `/tmp/fast544-ncu-2024.2`，没有替换系统CUDA/驱动。下载归档为 `/tmp/fast544-ncu-2024.2.tar.xz`，临时目录被清理后需重新下载。官方归档URL：`https://developer.download.nvidia.com/compute/cuda/redist/nsight_compute/linux-x86_64/nsight_compute-linux-x86_64-2024.2.0.16-archive.tar.xz`。

驱动现有配置 `RmProfilingAdminOnly=1`，使用 `sudo -n ncu ...` 读取计数器；没有修改驱动权限配置。五个类别分别取第一个匹配调用（BN、FP16转换、concat、卷积、Half拷贝），`--profile-from-start off --set basic --section MemoryWorkloadAnalysis --launch-count 1`，CUDA Graph保持开启。BN正则为 `regex:.*bn_fw_inf.*`；其余精确命令见ncu-commands.json。输出前缀分别为ncu-bn/ncu-cast-demangled/ncu-concat/ncu-conv/ncu-copy，预测与报告路径独立。单个调用会被kernel replay多次采样，缓存/时钟/序列化改变，不用NCU duration替换Nsight时间线排名。

## 历史分阶段数据来源

`prior-profile/`为分支exp/profile-fast544提交c189fe62的原始小型记录副本，保留参数、三轮结果、环境、源码补丁、内核摘要和原始产物校验值。该原诊断使用父提交4971fb7加保存的patch。未在本次重跑分阶段诊断，其数值均明确为历史测量。大trace仍只在 `/home/ubuntu/SuperShip-profile-fast544/output/20261023-223213-profile-fast544/`；副本notes中的工具命令属于该源分支，不表示当前分支包含其诊断脚本。


## 最终结果与检查

Nsight Systems成功完成200张输入、6300检测，官方validate_output通过，参考AP50=0.7817。Nsight Compute五个类别各完成200张，均validate_output通过，检测数和逐次精度见ncu-summary.json。所有有效ncu报告成功导入。耗时最高BN累计34.552ms（15.88%）；concat样本DRAM82.70%、L2吞吐88.81%，确认该样本访存吞吐受限；BN和卷积样本未达计算或带宽饱和。详细解释见根文档。

新增失败记录：第一次FP16过滤使用默认function名称基准，模板内部float16_copy未匹配，ncu退出0但提示No kernels were profiled，未生成报告，随后的import退出1。改用--kernel-name-base demangled和独立cast-demangled前缀后成功；未把退出0当成采样成功。其余过滤也使用demangled。BN使用function即可匹配；完整五条命令在ncu-commands.json。

五条NCU命令和五组硬件样本已保存。具体样本调用不是逐形状完整覆盖，没有测整个模型的FLOPs、TFLOP/s、roofline或warp stall；没有声称找到全局唯一瓶颈。

检查：两个新增脚本py_compile通过；Nsight汇总独立重算的全部数值字段一致；六份有效预测通过官方输出检查并分别评分；Git diff --check通过。没有修改模型实现，未运行新的全套模型测试。未提出新优化候选，未提交竞赛成绩。

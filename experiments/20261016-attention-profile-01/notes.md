# 当前推理路径的性能瓶颈实验

已运行，后端为 PyTorch Eager；没有 TensorRT engine、TensorRT Python 包或 trtexec，因此本次没有采集 TensorRT profile。

## 主要结果

Self Attention 合计占 GPU kernel 时间 **7.33%**，三轮为 7.26%, 7.36%, 7.37%。Cross Attention 合计 **7.93%**。当前路径没有观察到 Self Attention 占 50% 的现象。

不带 profiler 和 hooks 的前向计时为 28.276, 28.347, 28.245 ms/批，中位数 **28.276 ms/批**。每批 8 张，FP32，640×640；RTX 3090，PyTorch 2.5.1+cu124，CUDA 12.4。

## 算子排名（三轮平均）

| 算子 | GPU ms/批 | GPU kernel 时间占比 |
| --- | ---: | ---: |
| `aten::cudnn_convolution` | 8.115 | 28.92% |
| `aten::cudnn_batch_norm` | 3.044 | 10.85% |
| `aten::addmm` | 2.958 | 10.54% |
| `aten::cat` | 2.296 | 8.18% |
| `aten::add` | 1.856 | 6.61% |
| `aten::mul` | 1.786 | 6.36% |
| `aten::copy_` | 1.545 | 5.50% |
| `aten::clamp_min` | 1.176 | 4.19% |
| `aten::silu_` | 0.928 | 3.31% |
| `aten::bmm` | 0.813 | 2.90% |

这些算子类别与下面的 attention 模块分类是两种视角，不能相加。`addmm`、`bmm` 不全属于 Self Attention；本次通过模块范围进行归属。

## 模块归属（互斥分类）

| 模块 | GPU kernel 时间占比 |
| --- | ---: |
| `backbone` | 35.95% |
| `encoder` | 34.30% |
| `decoder` | 14.49% |
| `decoder.decoder.layers.2.cross_attn` | 2.65% |
| `decoder.decoder.layers.0.cross_attn` | 2.65% |
| `decoder.decoder.layers.1.cross_attn` | 2.64% |
| `encoder.encoder.0.layers.0.self_attn` | 2.49% |
| `decoder.decoder.layers.2.self_attn` | 1.62% |
| `decoder.decoder.layers.0.self_attn` | 1.61% |
| `decoder.decoder.layers.1.self_attn` | 1.61% |

这里 backbone、encoder、decoder 的行表示未被更深 attention 范围归属的部分；例如 encoder 行不包含单列的 encoder Self Attention。所有行相加为 100%，避免父子范围重复计时。GPU kernel 时间不等于包含 CPU 调度间隙的前向延迟。

## 实验方法与范围

从验证集按固定间隔取 40 张真实图片，组成 5 批；图片清单和 annotation/weight SHA256 见 `parameters.json`。使用与当前入口相同的 `build_runtime` / `model_forward`，未调用 `deploy()`，未修改现有模型或生产推理路径。

输入预先放在 GPU：预热 5 次；不带 profiler 测 3 轮，每轮 20 次前向；随后采集 3 轮，每轮 5 批。使用 torch.profiler 的 CPU/CUDA 活动，forward hooks 为三个主模块、四处 self_attn、三处 cross_attn 加 record_function 范围。对 CPU 侧算子关联的 exclusive device 时间按最近模块祖先归属，避免嵌套和 CUDA kernel 双重计数。

仅诊断当前模型前向：不包含解码、CPU 预处理、H2D、后处理、D2H 或 JSON 写盘，也没有重新测 AP50，不能当作比赛端到端成绩。profiler 有采集开销，排名用于定位候选瓶颈；精确优化收益需独立计时与评分。

## 优先实验建议

1. 优先测试部署时的卷积/BatchNorm 融合，查看现有 `model.deploy()` 路径对该模型的实际覆盖；本次未启用，不能声称已经消除了全部 BatchNorm。
2. 再测试 TensorRT FP16 或 PyTorch 编译后的算子融合，重新采集 profile；融合后瓶颈占比可能变化。
3. Self Attention 优化可作为后续路线，但当前占比约 7.3%，仅优化它对整个前向的潜在收益有限，不能套用其他模型的 50% 结论。

## 复现

工作区：`exp/inference-backends`；基准 commit：`cd5fed1508d929547f2c4656aebf209ecacb4547`，dirty 状态由 `source.patch` 和 `source.json` 保存。不要在当前工作区重复应用补丁。其他干净检出切换到基准 SHA 后应用补丁，另行准备被忽略的数据与权重即可恢复运行代码。

本次完整命令（在仓库根目录执行）：

```bash
.venv/bin/python supership/profile_inference.py --output-dir output/experiments/profile-attention-20261016-01
```

重新运行必须更换输出目录，脚本拒绝覆盖已有目录。运行参数和测量环境见 `parameters.json`；大 trace 仍在 `output/experiments/profile-attention-20261016-01/trace.json`，路径和 SHA256 见 `metrics.json`。`operators.csv` 与 `exclusive_modules.csv` 可直接排序，原始 `operator_table.txt` 含嵌套 scope 与 kernel 行，只作原始调试证据，不应逐行相加。

未来安装兼容的 TensorRT/trtexec 后，可另起实验使用官方命令思路：构建 engine 时启用 `--profilingVerbosity=detailed`，运行时使用 `--dumpProfile --exportProfile=<唯一目录>/profile.json --separateProfileRun`。这些 TensorRT 命令本次未执行。

方法参考：[PyTorch Profiler](https://docs.pytorch.org/tutorials/recipes/recipes/profiler_recipe.html)、[TensorRT per-layer profiling](https://docs.nvidia.com/deeplearning/tensorrt/10.x.x/performance/benchmarking.html)。

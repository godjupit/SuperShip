# 最新三项组合：性能与瓶颈实测

实验 `20261025-174717-profile-current`；负责人 Codex /root；状态 **completed**；北京时间 2026-10-25 17:47–17:56 使用 GPU0 RTX4090，结束核实无GPU进程并释放。独立分支 `exp/profile-current-20261025`，worktree `/home/ubuntu/SuperShip-profile-current-20261025`。父源码 **d0db0d31148319923efe9eb05fb2ad3f19afa4fd**；父实验 `20261024-002139-kernel-paired10`。

本次只做诊断，不修改推理算法、不合入main、不提交竞赛，不自动恢复或重传旧成绩。旧kernel worktree四个未跟踪结果及main原有两个profile文件均未修改。

## 配置与可复现性

544输入、FP16、batch8、8读取线程、prefetch3、OpenCV半尺寸JPEG解码、channels-last、CUDA Graph、异步回传、score0.05、99对Conv-BN融合；新增组合保持 `KERNEL_WEIGHT_HALF=1 KERNEL_LINEAR1X1=1 FEATURE_CAT=triton_half`。完整实际覆盖见config.json，未发现额外性能环境覆盖。AMD EPYC7402，CPU亲和0–9，PyTorch2.6.0+cu124、CUDA12.4、cuDNN90100、Triton3.2.0、OpenCV4.11.0、Nsight Systems2024.2.3.38，驱动550.142；见environment.json。

首轮运行源码 **639ea9ae23f16ed7154bb33b6d4921023b2c604b**；后续复测运行源码见followup-metrics.json。后续提交只增加本次诊断脚本/证据文件；supership/、engine/、run.sh、官方计时器与输出校验器始终与d0db0d3一致，没有未提交推理补丁。诊断脚本均先提交再运行；执行中只有生成的证据文件未跟踪。operator-command.json、boundary-command.json、exit-observed-command.json保存额外命令与源码，commands.json及followup-commands.json保存其余实际调用。原始产物位于output/同名实验目录，仅本机可用；Git保存摘要、配置、命令、数据/权重/工具与产物SHA256。图像文件逐项哈希的排序清单摘要见dataset-checksums.json。

正式测试使用原样官方benchmark_submission.py：READY后才能访问输入，计时包括全部输出写盘/fsync和进程组结束；每轮独立worker。Nsight仅捕获真实输入Runtime.run，初始化/合成预热排除。完整验证集1030张含6张尾批，未测隐藏集。

## 正式性能与精度：全部逐轮保留

| 组 | 三轮秒数 | 中位数秒 | reference AP50 |
| --- | --- | --- | --- |
| 首组三轮 | 0.508567777 / 0.370512208 / 0.389600918 | **0.389600918** | 0.7818 / 0.7816 / 0.7812 |
| 因变慢与低覆盖率追加复测 | 0.373464633 / 0.339070775 / 0.346047775 | **0.346047775** | 0.7811 / 0.7812 / 0.7816 |

首轮0.5086秒保留；可能包含首次输入访问的冷缓存/系统波动，但未控制页缓存，不能确定归因。复测原因是首组相对历史变慢且Nsight GPU活动覆盖率降低；不挑最快单轮，不用复测覆盖首组。两组三轮都通过官方输出校验与评分。历史306.99ms与本次不同日期，不把差异当作新代码收益或确定回退。

完整验证集AP50 **0.9058**，单次端到端 **1.510722788秒**；1030张、40353检测，含尾批。参考同组基线0.7935、98%门槛0.77763，本次正式最低0.7812，保留98.450%、裕量0.00357。验证同组基线0.9170、门槛0.89866，保留98.779%、裕量0.00714。hidden AP50=null。每次Nsight、分阶段及边界诊断也单独校验和评分；详见metrics.json、followup-metrics.json与boundary-metrics.json，未用诊断耗时替换正式分数。

## 当前瓶颈：三类证据

### 1. 输入供给与CPU结果处理使GPU出现空档

两次Nsight内核累计 **170.796 / 166.174 ms**；GPU活动并集 **180.996 / 176.391 ms**，首末活动跨度 **243.626 / 228.850 ms**；覆盖率 **74.29% / 77.08%**。这只是时间线覆盖率，不是SM利用率；与历史内核172.945ms接近，但本次空档更明显。H2D约10ms，D2H约0.09ms，PCIe结果回传不是当前主要耗时。

三次主线程逐行诊断，核心Runtime.run为 **250.69 / 272.51 / 278.92 ms**：

| 阶段 | 三次累计时间ms |
| --- | --- |
| 等待每批图像线程Future.result（包括list构造与主机调度） | **166.64 / 179.60 / 183.33** |
| 结果collect，含最后一批 | 27.30 / 35.40 / 37.15 |
| 等待GPU输出event，含尾部 | **26.21 / 18.01 / 24.15** |
| JSON序列化 | **2.87 / 4.61 / 2.89** |
| fsync | **6.34 / 7.74 / 6.70** |

这些主线程区间由同一run帧的互斥逐行时间累计，合计与run墙钟相符；加载线程总工作量并行重叠。输入等待与GPU执行也重叠，不能把约180ms等待全当作可消除空闲，更不能与GPU内核时间相加。结合两次时间线约52–63ms的无GPU活动间隔与较短event等待，优先检查CPU供给、环形槽调度及主线程结果格式化，而不是继续盲增线程。

### 2. 写盘之后到进程退出，另有约105ms

边界worker保持同一Runtime.run，在请求收到、run返回、紧邻os._exit前打印时间戳。第一组三轮核心run约251–253ms，官方诊断总时间357–402ms。为排除请求发送开销，第二组三轮观察父进程原始send_request/record_exit的时间戳，函数原逻辑及官方文件均未修改：

| 轮次 | Runtime.run ms | 退出前到父进程观察到结束 ms | 请求发送到收到 ms |
| --- | ---: | ---: | ---: |
| 1 | 260.745 | 104.055 | 0.150 |
| 2 | 248.584 | 109.678 | 0.183 |
| 3 | 249.159 | 105.120 | 0.172 |

结果文件已经关闭/fsync，全部线程已join、GPU已同步。约104–110ms位于最后退出调用附近到父进程wait返回之间；**还不能细分为CUDA上下文/驱动资源回收还是系统调度**。这段必须计入完整协议，下一步应单独追踪退出过程。此时间戳诊断不替代上方正式两组成绩。

### 3. GPU内部重点是decoder cross-attention的数据搬运与中间张量

第一份真实Graph时间线的主要内核族如下，占比的分母为170.796ms内核累计，不是端到端：

| 内核族 | 累计ms | 内核占比 |
| --- | ---: | ---: |
| Half直接拷贝 | **12.946** | **7.58%** |
| FP16转换 | **10.651** | **6.24%** |
| 一类CUTLASS GEMM | **9.516** | **5.57%** |
| FP32 add | **9.055** | **5.30%** |
| Triton特征pack | **8.960** | **5.25%** |
| FP32 mul | **8.715** | **5.10%** |
| 一类原生concat | **7.804** | **4.57%** |

按显式名称分组，copy/cast约31.14ms、concat/pack约18.48ms，合计约49.62ms；GEMM/卷积族约53.34ms，其余67.84ms，不据此宣称带宽或算力饱和。

额外用同形状真实首批做eager PyTorch operator归属诊断，**仅定位调用位置**，不替代Graph的计时排名。最大几组copy_/clone落在三层 `decoder.decoder.layers.{0,1,2}.cross_attn`，例如[8,8,32,4624]/[64,32,68,68]；每层均有value重排、FP16与FP32转换、grid_sample和采样结果concat。对应engine/rtv4/utils.py的deformable_attention_core_func_v2：109行sampling-grid重排、114行value reshape、118行grid_sample、140–142行权重重排及concat→mul→sum。每层约210μs copy_和约103μs concat为带hook单批诊断值，父子操作含重复计时，不能相加或乘批数当作正式收益。原始trace只存output，operator-summary.json保存模块、形状及证据。

## 结论与下一步

先处理CPU供给/结果收集造成的GPU空档，并查清约105ms退出区间；GPU优化优先围绕三层deformable cross-attention减少reshape实体拷贝、类型往返以及concat/mul/sum中间读写。它们比继续做泛化的卷积替换更有具体证据。当前没有新NCU硬件计数器，不能把访存操作耗时等同于显存带宽饱和，也不能确认算力或launch已经饱和。

本地最快候选仍为此前已验证的三项组合，保守640高精度候选保留；本次不晋级新候选、不更新Accepted成绩。最近Accepted沿用原实验回执，未在线核验账号；官方隐藏集最优仍未知，4090结果不能作为3090正式成绩。

## 失败、检查与复现

初次cProfile在多线程运行中产生累计时间超过run墙钟、调用次数异常，**统计未被用于瓶颈结论**。原始三份JSON迁移保留在output/cprofile-rejected-stages{1,2,3}.json，脚本stages.py和当时Git源码保留。改用主线程Runtime.run逐行墙钟区间，并核对区间之和，详见line1/2/3.json。

没有推理算法修改。检查包括全部正式与诊断输出逐次官方校验/评分、完整1030图验证与尾批、诊断脚本编译以及git diff --check。运行后为诊断脚本补充已有输出拒绝覆盖保护；该保护不影响已记录测量或推理代码。

复现：在本分支准备同校验和数据/权重，复制本实验脚本与config.json到**新的唯一实验目录**，将TRITON_CACHE_DIR指向该新实验output目录；`run.py`自动按新目录名生成输出，执行三轮官方计时、验证和Nsight。`followup.py`可复现追加三轮及逐行诊断；`operators.py`与worker_boundary/observe_exit调用参考相邻commands文件。所有GPU任务串行独占；不可直接重跑本实验日志路径。原始日志/预测与完整profile不在Git中，离机需要重跑。

## 并发现场与Git收尾

实验结果已提交并推送独立分支。17:58收尾时main在本会话操作之外出现未解决合并冲突（README.md、engine/rtv4/hybrid_encoder.py、supership/generate_submission.py）及其他暂存变更；未修改、暂存或提交这些内容。main的OPTIMIZATION_EXPERIMENTS.md仅更新本次预约为completed并追加结果链接，因现有冲突无法单独正常提交，保留该本地更新。本实验所有源码/计时工具/规则均以独立worktree固定d0db0d3为准，未使用main并发修改中的文件；本分支推理源码与该固定版本一致。未把main的冲突变更当成本实验结果，也未对新规则或新代码作排名承诺。

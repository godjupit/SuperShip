# nvJPEG后端与批量解码：停止后的交接记录

实验 `20261026-091334-nvjpeg-backends`；负责人Codex/root；工作分支 `exp/nvjpeg-backends-20261026`。状态 **abandoned（用户要求先停止优化并整理提交，2026-10-26 09:28CST）**。已完成初筛，后续优化与深入profiling停止。进程审计未发现残留的本轮driver/worker，GPU0 RTX4090空闲；登记占用09:15–09:28CST，09:28确认释放。

main父版本 `f7b03b8f9e153b409431d49f40390763e4c2312a` 已承载最快已验证thread100-light，实验从该main隔离。所有推理实现与30轮初筛源码完整SHA `386a11a7a0156932f885faae3dcb5fafb775086a`；其后只有记录整理，没有未提交推理补丁。**最快nvJPEG配置498.190613ms，慢于同期OpenCV基线253.022944–256.347169ms，不晋级main。** 原最快、保守方案及Accepted258.409792ms不变。无竞赛提交。

## 后端与环境核实

实际环境是RTX4090、driver550.142、PyTorch2.6.0+cu124；系统CUDA目录指向11.8。探测两套实际安装库：

| 库 | nvjpegGetProperty版本 | DEFAULT/HYBRID/GPU_HYBRID | HARDWARE/HARDWARE_DEVICE |
| --- | --- | --- | --- |
| 系统libnvjpeg.so |11.9.0|创建及合成8/64批baseline/progressive解码成功|创建返回7（ARCH_MISMATCH）|
| torchvision携带libnvjpeg.so.12 |12.3.1|创建及合成8/64批baseline/progressive解码成功|创建返回7（ARCH_MISMATCH）|

非硬件handle查询hardware-info返回engine=0、cores=0。设备输入GPU_HYBRID_DEVICE后端也能创建，但未进行其解码/计时；不能将创建成功当作完整验证。完整返回码和库SHA见capability.json。**本机未安装nvJPEG12.8**，用户提供的12.8文档用作API/后端行为参考，而不是声称使用该版本。

参考[NVIDIA nvJPEG12.8官方文档](https://docs.nvidia.com/cuda/archive/12.8.0/nvjpeg/index.html)：软件GPU_HYBRID批量路径有batch>50及bitstream格式限制，缩放因子API仅硬件后端支持。因此保持模型batch8/输入544，独立比较解码batch8/64/128；软件路径完整解码RGB，再GPU缩放，未请求不支持的硬件半尺寸解码。实际GPU Huffman核与混合调度仍需Nsight确认；当前只有显式后端选择、格式/API支持和完整耗时证据，不把枚举值当作已观测到的GPU执行证明。

## 输入与实现

输入审计使用独立READY/request握手，收到READY后父进程才发送路径。200图像全部1024×1024、BaselineDCT（编码192）、三通道、4:2:0、EXIF方向unknown0；三个软件后端批量支持查询均返回status0/support-code0。详细每图信息本机input-audit.json，握手及实际命令见audit-command.json。初始化/预热只用合成数据，不访问评测路径或其派生内容。

实现使用ctypes直接调用nvjpegDecodeBatched，显式选择后端及批量；读取线程只取压缩字节。GPU解码输出HWC RGB，通过单次Triton双线性kernel缩放到544，避免历史torchvision实现的stack和通用resize中间张量。每个producer状态/缓冲区独立，压缩字节保留到解码完成；GPU事件约束复用，record_stream保护跨流张量生命周期，模型batch8和原CUDA Graph不变。串行/双缓冲生产者并行分别测量。所有线程join、GPU同步、native句柄销毁、JSON/fsync/关闭及正常退出都在计时内。默认CUDA_DEVICE_MAX_CONNECTIONS=1沿用基线，尚未调优。

非JPEG、四通道或需EXIF旋转的输入有显式OpenCV回退；本轮30份参考输出中的原生worker均报告200张native、0张回退。合成测试单独覆盖PNG回退、灰度/渐进式、不同尺寸、尾批和空输入。64解码批次的最后8张不足GPU_HYBRID文档阈值；128配置的128+72批次均超过50。不能将native=200解释成全部由GPU Huffman处理。

## 三轮结果

全部逐轮时间见[results.md](results.md)，不挑最快轮，不删除慢方案。关键中位数：

| 方案 | ms | reference AP50 |
| --- | ---: | ---: |
| OpenCV基线开头/末尾 |256.347169 /253.022944|0.7809|
| 历史torchvision路径在当前544模型上重测 |1203.153741|0.7795|
| HYBRID batch8并行 |1552.098385|0.7794|
| GPU_HYBRID batch8并行 |1525.347198|0.7794|
| HYBRID batch64并行 |1320.891127|0.7794|
| GPU_HYBRID batch64串行 |647.256890|0.7796|
| GPU_HYBRID batch64并行 |610.316333|0.7796|
| GPU_HYBRID batch128并行 |498.190613|0.7795|
| GPU_HYBRID batch64并行、系统11.9库 |610.318534|0.7796|

大批量与显式GPU_HYBRID明显优于小批量/CPU Huffman配置，串行/并行的顺序初筛也有差别，但最优仍约为OpenCV同期末尾控制的1.97倍耗时。没有足够依据晋级，也没有执行配对确认或组合调优。并行带来多少纯GPU重叠、解码/推理争用、CPU调度及native清理各占多少，尚未采样确定；不能仅凭这些完整时间定量归因。所有结果保留，供以后在用户恢复授权后评估。

## 检查与未完成事项

30次完整worker均覆盖全部200输入，合法输出且逐轮AP50通过0.77763门槛（实际reference基线0.7935×98%）。最低0.7794，比值0.982231、绝对裕量0.00177；像素/输出与OpenCV不同，未沿用旧AP50。validation AP50=null，hidden AP50=null，官方隐藏集最优未知。本轮无1030验证、无32GiB硬限制测试，无新官方回执。

9项针对性测试通过（5.38s）：原生后端、灰度/渐进式、64→2→64状态重初始化、损坏输入、GPU缩放与双线性参考误差≤1、跨流/异形尾批/回退/空输入。最初6失败/3通过源自测试假设错误：PIL的RGB整数127表示红色(127,0,0)，以及fake模型无encoder却要求非640几何重建；修正fixture后全部通过，没有为满足错误fixture修改解码算法。原测试源码/失败摘要保存在本机output，初测完整控制台trace未导出，明确标记缺失；修正后的完整日志保留。

整理期间仅核对已有结果/哈希、Python编译和gitdiff，不再启动性能或GPU实验。官方工具、元数据、权重及200图像与父manifest的SHA一致；30个预测逐个重核SHA。checksums.json保留实际源码/库和本机原始文件校验值。

停止时未完成：Nsight确认GPU Huffman核与解码/推理重叠；CPU/GPU/句柄销毁/OS退出分阶段归因；连接数/资源生命周期调优；候选配对确认；更大验证和内存硬限制检查。以上均未继续执行，不得将计划写为已完成。

## 复现与归档

原始预测、完整日志、输入审计和测试日志 **仅本机**：`/tmp/SuperShip-nvjpeg-backends-20261026/output/20261026-091334-nvjpeg-backends/`，main/output同ID链接到此。Git仅存必要源码、测试、能力探测、命令、结果摘要和哈希；不提交二进制库/预测/凭证。库需由相应环境提供，哈希见capability.json。

在独立worktree检出推理源码386a11a7a0156932f885faae3dcb5fafb775086a（该提交尚无screen.json），提供匹配的data/SuperShip、weights/baseline.pth、依赖，再执行：

```bash
/home/ubuntu/.cache/supership-venv/bin/python -m pytest -q tests/test_nvjpeg.py
/home/ubuntu/.cache/supership-venv/bin/python experiments/20261026-091334-nvjpeg-backends/run.py
```

run.py拒绝已有case/结果，避免覆盖；每个command.json保存完整配置、源码SHA、真实命令；外部机器须调整Python/库路径并准备匹配公开资产。probe.py只用合成图，audit.py单独通过READY请求审计，审计产物不可作为正式计时输出。main中只归档结果；完整实验代码保留在exp/nvjpeg-backends-20261026。原历史分支、worktree、实验和保守实现全部保留。

归档位置：main仅包含结果/能力/命令/校验摘要；完整实验实现、测试和驱动已提交推送至exp/nvjpeg-backends-20261026（收尾提交590435b）。未将更慢的解码路径合入main。

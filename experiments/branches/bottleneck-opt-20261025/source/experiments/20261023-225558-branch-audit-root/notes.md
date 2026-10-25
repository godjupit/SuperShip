# 全分支核对与后续父版本选择

实验 ID `20261023-225558-branch-audit-root`；状态 completed；负责人 Codex /root；北京时间 2026-10-23 22:55。本次是只读源码及历史证据分析，新增本记录和台账，不运行性能实验，不修改推理实现，不进行竞赛提交。

## 分支快照

`git fetch origin` 成功后核对，五个本地分支均与同名远程分支一致：

| 分支 | 完整 SHA |
| --- | --- |
| main | d12866deaa0172f90a0de55743399ac8aa0e68cf |
| exp/inference-backends | 43f44ed6561999c187aaab384169d0148da2f4fc |
| exp/performance-analysis | 9ebd7e25fe921f64a7da19b969d91e5320332f46 |
| exp/rtx4090-e2e | 4971fb72cf67f6295da02bd25b9f204c766a95e3 |
| exp/profile-fast544 | 3e61b3358c53a6b67b7acddb60951203b7c3ac7c |

已有 worktree 均保持原分支，未切换、修改或删除。main 的用户未跟踪文件 ship_prof.nsys-rep、ship_prof.sqlite 保留，不纳入提交。GPU 沙箱外预检显示 GPU0 RTX 4090 空闲，无进程；本次没有预约或使用 GPU 计算。

## 比较依据

旧组 RTX 4090、参考集 200 张：main 为 6.079042092/5.128391426/5.125821636 秒；inference-backends CUDA Graph 为 3.171570187/3.071756931/3.224105999 秒；performance-analysis CUDA Graph 为 3.071232824/3.221062850/3.274563741 秒。三个方案 reference AP50 均为0.7935，hidden AP50 均未测。原始证据分别为各分支 experiments/20261022-main、experiments/20261022-cuda-graph、experiments/20261022-analysis-cuda-graph 下的 metrics.json。分析分支相对后端分支主要增加算子及分阶段诊断，无稳定提速证据。

更新官方工具组：main 为 4.853070409 秒；640 半尺寸 JPEG 方案为 0.476629654 秒。逐轮结果、配置及工具版本见主分支 OPTIMIZATION_VERIFIED_20261022.md 及其链接。工具切换前后不直接按比例计算收益。

rtx4090-e2e 后续确认实验 `20261022-195852-further-confirm-size544`：

- 三轮 0.375216336/0.381344812/0.379818620 秒，中位数 0.379818620 秒。
- reference AP50=0.7819/0.7817/0.7814，基线0.7935，98%门槛0.77763；最小比值98.475%，最小裕量0.00377。
- 完整1,030张 validation AP50=0.9054；同组基线0.9170，98%门槛0.89866；比值98.735%，裕量0.00674。hidden AP50=null。
- 历史源码为 `585d759e3e2563733ef6dc18d2ff638333ee41be` 加保存补丁，补丁SHA256 `d09dbce0142096f0331d05793dc4bba03c7aa48014d39fc91f818ce4187e516f`；不能仅用历史基提交声称复现。后续已提交父版本为 `4971fb72cf67f6295da02bd25b9f204c766a95e3`。
- 官方工具提交 `42460fba744a1c8741252177723530976101f305`；READY到进程组退出，含全部输出和fsync。计时器SHA256 `0befe3aadd1860460d53e5ea2b141d3310edcf5391f9ab4c3a7727244e7d7c02`；校验器SHA256 `79f47d58cd11ae9ba5b2ac1d9613d053c41bda3d1fb457ede78453d3c15a4e7f`。
- 权重SHA256 `42a04535d33de94acc58ae3c66a9a2d161e975ee17adae6cae533770d1929c3e`；参考集manifest SHA256 `911e966a23ddadad2464723b2a3c3b992084ca62fe7fdefab51a8ffcf5db4a53`。
- Python3.12.8、torch2.6.0+cu124、OpenCV4.11.0。历史原始产物在 `/home/ubuntu/SuperShip-optimize/output/submissions/20261022-195852-further-confirm-size544`，本机路径不代表离机可访问。
- 已核对的历史Accepted回执时间2026-10-22 19:59:29，仅解析计时；本次不访问竞赛账号，不声称其仍为账号当前提交。

更快的512半尺寸JPEG候选虽有0.362355174秒，但validation AP50=0.8960未达0.89866，不选作优化父方案。保留640完整JPEG解码的保守方案，validation AP50=0.9167。

profile-fast544 相比 rtx4090-e2e 的 fast_worker 差异主要是可选事件、主机计时和报告。其 `20261023-223213-profile-fast544` 中父版本重测0.373381679/0.343036264/0.359185144秒；诊断0.342910136/0.345510094/0.342561504秒。记录明确不晋级候选；不能把不同运行的cuDNN选择、时钟、缓存和负载变化归为代码收益。诊断的validation/hidden AP50均为null，不移用父方案验证值充作本次测量。

## 后续工作约束与优先级

优先从 `4971fb72cf67f6295da02bd25b9f204c766a95e3` 创建独立优化分支及worktree，保持544输入、三层解码器、FP16、batch8、workers8、prefetch3、JPEG_REDUCTION=2、SCORE_THRESHOLD=0.05、channels-last、CUDA Graph、cvtcolor锁页写入、异步回传和cuDNN benchmark。完整覆盖项以该提交的确认实验config.json及benchmark_optimized.sh为准。

复现历史父方案，在该版本worktree运行：

```bash
PYTHON_BIN=/home/ubuntu/.cache/supership-venv/bin/python RUNS=3 bash benchmark_optimized.sh
```

需先检查GPU独占和输出路径，避免覆盖历史产物；新实验使用独立输出目录并记录实际命令。

优先分析READY后的GPU图：诊断记录显示GPU图约206ms、worker内部约239ms，BatchNorm及转换/拷贝值得检查。先核实可融合Conv-BN的实际覆盖，再独立评估重复转换/布局操作；历史MODEL_DEPLOY试验没有稳定收益，不将重新开开关当作已知提速。仅在定位具体卷积形状及瓶颈后考虑专用实现。JSON和输出回传占比较小，优先级较低。

全进程Nsight统计含初始化、算法搜索和合成预热。用户贴出的implicit/precomputed卷积占比尚未证明来自READY后的实际推理，应先按时间区间切分再确定优化对象。每个实际实验必须先登记、保留失败结果，完整检查输入与尾批，独立计时至少三轮并逐轮评分；有精度影响须复核完整验证集。RTX4090成绩不作为RTX3090正式成绩，官方隐藏集最优保持未知。

核对命令：git status --short、git branch -avv、git worktree list、git fetch origin、git for-each-ref；对各完整SHA执行git show读取台账和metrics，git diff比较supership/及入口脚本。仅文档变化，检查git diff --check及指标计算，不重跑模型测试或性能计时。

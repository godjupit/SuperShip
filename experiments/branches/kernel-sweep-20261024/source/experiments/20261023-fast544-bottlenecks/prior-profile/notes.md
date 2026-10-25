# 最快544方案：实际输入性能诊断

- 实验 ID：`20261023-223213-profile-fast544`；负责人 Codex /root；状态 completed。
- 分支 `exp/profile-fast544`，隔离目录 `/home/ubuntu/SuperShip-profile-fast544`（运行时位于/tmp，结束后用git worktree move持久保存）。
- 父提交 `4971fb72cf67f6295da02bd25b9f204c766a95e3`；父实验 `20261022-195852-further-confirm-size544`。
- 基线直接运行父提交所在 `/home/ubuntu/SuperShip-optimize` 的未修改 worker；诊断源码完整差异在 `source.patch`，SHA256 `665720c527e63d5d846cbb48761272bc6931b50fba84bc881d33d5532d575c1c`。第一版诊断补丁另存 source-initial.patch。最终提交包含诊断代码。
- GPU 0 RTX 4090，启动检查无其他 GPU 进程；本次独占记录为北京时间 2026-10-23 22:32–22:38，结束后释放。CPU AMD EPYC 7402，10个可见逻辑核；依赖版本见 environment.json。
- 200张公开参考集、544输入、batch=8、workers=8、prefetch=3、FP16、完整三层解码器、OpenCV半尺寸JPEG解码、cvtColor写锁页缓冲、CUDA Graph、异步回传。全部覆盖项见 config.json。
- 权重、元数据、官方计时/校验源码 SHA256 见 metrics.json；沿用此前公开数据版本。未访问隐藏数据，未运行验证集，未进行竞赛提交。

## 原始计时与正确性

| 运行 | 三轮端到端时间（秒） | 中位数 | 各轮reference AP50 |
|---|---|---|---|
| 父提交未修改基线 | 0.373381679 / 0.343036264 / 0.359185144 | 0.359185144 | 0.7815 / 0.7813 / 0.7817 |
| 最终分阶段诊断 | 0.342910136 / 0.345510094 / 0.342561504 | 0.342910136 | 0.7815 / 0.7817 / 0.7817 |

全部运行均通过未修改的官方输出校验，worker确认处理200张。基线三轮检测数为6308/6303/6304，诊断6302/6306/6300。不同进程 cuDNN 搜索可能选择不同算法并产生数值变化，故逐轮评分，未要求跨进程预测逐字节相同。三轮 AP50 均超过参考集基线0.7935的98%门槛0.77763。validation AP50=null，hidden AP50=null。

历史最快的0.379818620秒也是相同配置。本次没有新的优化假设，较历史快不能解释为代码收益；初始化选择算法、缓存、GPU时钟及系统负载都会造成差异。首组探索完整记录为0.446876341/0.380266406/0.344539908，中位数0.380266406；初版诊断0.343015168/0.343435423/0.364509495，中位数0.343435423；均保留，不挑选最快一轮。原始计时覆盖 READY 后输入访问、fsync、进程及进程组退出。

## 流水线瓶颈

以下是最终诊断三轮的各项中位数。GPU采用CUDA Event，不增加每批强制同步；主线程/读取线程用perf_counter。不同项存在重叠，不能加成端到端时间。

| 项目 | 时间（毫秒） | 含义 |
|---|---:|---|
| worker内部处理 | 239.42 | 元数据开始至输出fsync，不含报告写入及退出 |
| GPU Graph | 206.14 | 25批，含GPU预处理、模型前向、GPU后处理；每批8.25ms |
| H2D输入传输区间 | 9.86 | 图像与尺寸上传及相关排队；CUDA Event区间可能含主机发射间隙 |
| D2H结果传输 | 0.15 | 25批异步回传，说明结果传输带宽不是主要瓶颈 |
| 主线程等待输入 | 49.26 | 等待预取读取完成；包含首批启动及后续等待 |
| 主线程等待输出 | 144.29 | 等待较早批次GPU/回传完成；是等待时间，不能再与GPU时间相加 |
| CPU结果筛选/组装 | 21.50 | NumPy过滤、坐标转换、字典组装 |
| JSON序列化 | 2.90 | orjson.dumps |
| 写盘和fsync | 7.79 | 含目录/文件操作，受存储状态影响 |
| 读取线程累计 | 1305.74 | 8线程各任务墙钟时间之和，不是端到端1.3秒 |
| 其中imread/解码累计 | 1093.32 | 文件读取与JPEG解码合计，未拆分磁盘和解码 |
| 其中resize/RGB累计 | 205.83 | CPU缩放与颜色转换 |

GPU Graph时间约为worker内部墙钟的86%，表明当前首先需要研究GPU图内计算/内存操作。读取是次要但仍可见的限制；JSON和输出拷贝较小。诊断端到端约343ms与内部约239ms之间还存在约104ms，覆盖请求、诊断报告写入、退出及驱动清理等未细分开销；不能把全部差值直接归因为CUDA析构。

## CUDA算子分析

另用真实200张输入跑一次torch.profiler，保持相同CUDA Graph配置。捕获29,400条CUDA活动，CUDA活动时间合计218.39ms；profiler及trace导出使端到端达到2.462208255秒，此数只用于诊断，不能作为性能成绩。分类采用互斥kernel名称规则，并非模型模块归因。特别是attention的GEMM、softmax等分散在多个分类，不能将没有attention命名kernel解释成attention零耗时。

| CUDA活动类别 | 合计毫秒 | CUDA活动占比 |
|---|---:|---:|
| BatchNorm | 32.78 | 15.01% |
| 其他copy/cast | 28.69 | 13.14% |
| GEMM | 24.90 | 11.40% |
| 可识别卷积kernel | 23.86 | 10.93% |
| FP16转换kernel | 22.94 | 10.50% |
| concat | 16.51 | 7.56% |
| Memcpy | 9.74 | 4.46% |
| 其余kernel | 58.96 | 27.00% |

完整kernel名称、次数和时间在 kernels.json，分类结果在 kernel-groups.json。以上占比不是端到端占比；无法据此把某类耗时直接当作可获得收益。

建议下一步独立验证：

1. 检查可安全融合的Conv-BN对子；现有配置MODEL_DEPLOY=0，历史deploy路线未稳定获益，因此先验证实际融合覆盖和数值，而不能假设开启deploy就会更快。
2. 研究FP16/autocast边界和布局，减少重复转换、拷贝及concat中间张量；保留需要FP32的数值敏感操作，改动后重新检查参考与完整验证集。
3. 保持当前8读取线程为对照，针对首批和稳态等待分别试预取策略；历史减到4线程和增大batch均未体现收益，不重复当作已知加速。
4. 用单独诊断边界进一步拆分约104ms的内部计时外开销，保持READY、fsync、进程结束全部计入正式时间。

本次只提供诊断能力，不晋级新的候选，不改写历史最快/保守候选推荐。官方隐藏集最优仍未知。

## 可复现命令

在本分支worktree根目录，数据路径为data/SuperShip，权重weights/baseline.pth；Python环境路径见config.json。新机器需自行准备依赖和相同校验和的公开数据/权重，本机软链接不能代替产物分发。

```bash
python3 tools/profile_fast544.py --config experiments/20261023-223213-profile-fast544/config.json --output-dir output/20261023-223213-profile-fast544/reproduce-baseline --mode baseline
python3 tools/profile_fast544.py --config experiments/20261023-223213-profile-fast544/config.json --output-dir output/20261023-223213-profile-fast544/reproduce-stages --mode stages
python3 tools/profile_fast544.py --config experiments/20261023-223213-profile-fast544/config.json --output-dir output/20261023-223213-profile-fast544/reproduce-trace --mode trace
```

脚本禁止复用已存在输出目录，默认baseline/stages各三轮、trace一轮，全部通过官方输出检查并逐轮评分。阶段报告在predictions.runN.json.profile.json；trace在predictions.json.trace.json，可由兼容Chrome trace的时间线查看器打开。重跑trace需要足够磁盘空间。

原始父提交基线精确命令/目录/环境在output/20261023-223213-profile-fast544/clean-baseline-command.json；trace精确命令在trace-command.json；最终诊断命令在stages-final/command.json。最初探索与初版诊断使用同一config及官方benchmark_submission.py命令，分别输出baseline.json和diagnostic.json，后者FAST_PROFILE=1。全部产物SHA256见artifacts-sha256.json。

原始预测、完整日志及大trace仅保存在本机 `/home/ubuntu/SuperShip-profile-fast544/output/20261023-223213-profile-fast544`，不随Git推送；Git保存必要参数、逐轮指标、源码补丁、校验和及算子摘要。原运行命令及日志保留执行时/tmp路径，产物已随worktree持久迁移至上述目录；复现不依赖这些原始预测，但离机无法直接查阅大trace。

## 检查

`/home/ubuntu/.cache/supership-venv/bin/python -m pytest -q tests`：48 passed, 1 skipped（可选TensorRT引擎缺失）。扩展现有GPU尾批/环形复用测试，确认开启诊断时输出与无诊断路径一致、11张输入覆盖完整、6批事件记录正确。Python编译及git diff --check通过。未修改官方计时器/校验器，未进行竞赛提交。

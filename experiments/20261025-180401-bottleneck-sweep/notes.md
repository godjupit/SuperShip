# 瓶颈驱动优化：完整实验与推荐

实验 **20261025-180401-bottleneck-sweep**；负责人 Codex /root；状态 **completed**。分支 `exp/bottleneck-opt-20261025`，独立worktree `/home/ubuntu/SuperShip-bottleneck-opt-20261025`；父源码 **f2c4d275295a40b0845f82373a3f9f48178cf0fa**，父实验20261025-174717-profile-current、20261024-002139-kernel-paired10。GPU0 RTX4090于北京时间18:04空闲预检后预约，18:23核实空闲并释放。未终止其他进程，不在main的冲突工作区切换或修改推理代码。

## 结论与提交决定

**保留新组合为本轮比较组的推荐候选：提前回收输入槽 + 批量结果格式化 + Triton融合deformable attention + CUDA单连接。** 10对AB/BA交错对照，原三项组合中位数 **371.446ms**，新候选 **328.958ms**，缩短 **11.438%**，**8/10更快**；逐对差值中位 **38.962ms**，bootstrap 95%区间 **[2.178,48.910]ms**。有两次回退，不能承诺每轮更快，也不能用首个偏慢对照398.593ms夸大收益。

新入口 `benchmark_bottleneck.sh` 的一次全新完整三轮 **310.915874 / 316.507633 / 325.236048ms**，中位 **316.507633ms**。reference AP50 **0.7812/0.7812/0.7810**；完整1030张validation AP50 **0.9056**、单次 **1.048466823秒**，40347检测、尾批6张，官方校验通过。hidden AP50=null。

本轮精度门槛沿用同数据的实际基线：reference 0.7935，98%为0.77763；final最低0.7810，保留98.425%、裕量0.00337。validation实际基线0.9170，98%为0.89866；0.9056保留98.757%、裕量0.00694。20轮交错AP50最低0.7809，也通过参考门槛。不同轮次FP16/cuDNN/top-k差异保留，不把0.0002精度差称为提升。

**本次不正式提交竞赛日志**：新完整三轮316.508ms仍慢于用户此前约304ms和本机历史Accepted 302.713346ms记录。虽然同轮对照有改善，不能因此覆盖历史更短成绩；没有重传旧日志、没有拼接交错单轮或挑最快一轮。Git实验、代码与入口正常提交推送。服务器当前账号状态未在线核验；官方隐藏集最优仍未知，历史Accepted只代表timing parsed。

## 版本、比较组和环境

main此时存在外部合并冲突及未完成官方文档/评分更新，本实验不混入。以父分支固定COMPETITION、原样benchmark_submission.py/submission.py和本机同一组公开数据建立本轮比较组；重新测原最快三项组合，不直接继承历史302.7ms排名。权重/元数据/工具SHA256位于每个子实验metrics.json；本轮结束对全部200+1030张图像逐文件哈希，并确认与上轮诊断manifest完全一致，见dataset-checksums.json。

RTX4090单卡，AMD EPYC7402、CPU亲和0–9；Python3.12.8、PyTorch2.6.0+cu124、CUDA12.4、cuDNN90100、OpenCV4.11.0、Triton3.2.0、驱动550.142、Nsight Systems2024.2.3.38，详见environment.json。每次官方计时READY后才读图和元数据，覆盖全部输出写盘/fsync、GPU/线程完成和进程组退出；不更改计时器，不跳过图像。所有GPU任务串行独占，未在正式计时中运行GPU测试或硬件计数采样。

推理实现首次提交 **3607dff**；共享value替代提交 **246bb8c**，默认关闭；各子实验metrics.json记录执行时**完整源码SHA**，config.json/commands.json先提交后运行。后续仅新增入口、测试/诊断脚本和证据，不在测量中修改推理代码，无未提交推理补丁。最终wrapper执行源码 **5c0f88ef1a3937c6bbc5766710fa0b6fad182fa2**；10对源码 **30aef67dbba06befd2ddf6f8cfb8854d0c1912cd**。原始大日志/预测/profile在output/各同名实验目录，仅本机可用；Git保存全部参数、逐轮结果、命令、源SHA、校验值和必要摘要。artifacts-sha256.json保存全部原始产物索引，离机需准备数据并重跑。

## 独立假设与全部逐轮结果

固定原三项组合：544、FP16、channels-last、CUDA Graph、batch8、8读取线程、prefetch3、OpenCV半尺寸JPEG、score0.05、99对Conv-BN融合、FP16 Conv/Linear权重、1x1转Linear、Triton特征pack。表中每项只改变对应开关，组合明确列父项；正式输出每轮逐次评分，全部成功方案都重测完整验证集。

| 方案 | 三轮ms | 中位ms | reference AP50逐轮 | validation AP50 | 检查 |
| --- | --- | ---: | --- | ---: | --- |
| [control](../20261025-180701-bottleneck-control/notes.md) | 398.593 / 409.309 / 372.064 | 398.593 | 0.7816 / 0.7817 / 0.7816 | 0.9057 | 通过 |
| [recycle](../20261025-180732-bottleneck-recycle/notes.md) | 367.743 / 364.364 / 386.839 | 367.743 | 0.7813 / 0.7817 / 0.7812 | 0.9058 | 通过 |
| [bulk](../20261025-180800-bottleneck-bulk/notes.md) | 355.593 / 370.316 / 358.422 | 358.422 | 0.7812 / 0.7811 / 0.7816 | 0.9058 | 通过 |
| [fused](../20261025-180829-bottleneck-fused/notes.md) | 342.835 / 362.735 / 353.019 | 353.019 | 0.7812 / 0.7812 / 0.7812 | 0.9058 | 通过 |
| [cpu](../20261025-181042-bottleneck-cpu/notes.md) | 347.945 / 338.800 / 390.631 | 347.945 | 0.7813 / 0.7812 / 0.7816 | 0.9058 | 通过 |
| [fused-bulk](../20261025-181111-bottleneck-fused-bulk/notes.md) | 390.763 / 345.809 / 346.950 | 346.950 | 0.7811 / 0.7812 / 0.7812 | 0.9058 | 通过 |
| [combined](../20261025-181140-bottleneck-combined/notes.md) | 350.489 / 335.182 / 324.410 | 335.182 | 0.7817 / 0.7812 / 0.7812 | 0.9057 | 通过 |
| [cached](../20261025-181208-bottleneck-cached/notes.md) | 363.691 / 359.916 / 362.986 | 362.986 | 0.7812 / 0.7812 / 0.7817 | 0.9058 | 通过 |
| [control](../20261025-181236-bottleneck-control/notes.md) | 381.732 / 354.793 / 358.883 | 358.883 | 0.7813 / 0.7812 / 0.7812 | 0.9058 | 通过 |
| [connections1](../20261025-181339-bottleneck-connections1/notes.md) | 348.533 / 334.954 / 365.032 | 348.533 | 0.7817 / 0.7812 / 0.7816 | 0.9056 | 通过 |
| [async-alloc](../20261025-181407-bottleneck-async-alloc/notes.md) | 未进入计时 | null | null | null | 失败 |
| [combined-c1](../20261025-181507-bottleneck-combined-c1/notes.md) | 311.278 / 323.396 / 320.160 | 320.160 | 0.7817 / 0.7816 / 0.7812 | 0.9058 | 通过 |

- `recycle`：H2D完成event保护输入槽，即可开始下一轮CPU解码，不再等待对应GPU推理和D2H都结束。独立输入/输出的所有权边界，保持原输出槽event保护。
- `bulk`：输出event完成后复制到CPU快照，最后统一NumPy筛选、框转换、舍入和JSON对象构造，减少主循环中Python/NumPy操作；完整输入/查询顺序和原舍入语义保持。快照内存随输出量线性增长，4300x300x6个float32约31MB，不缓存评测答案或省略图像。
- `fused`：Triton直接读取原始非连续value布局，融合三尺度双线性grid sampling、权重乘法和归约；FP32计算/输出，零padding，align_corners=False，禁止训练路径。减少每层value克隆、类型转换和采样结果concat的中间写回。
- `cpu`=recycle+bulk；`fused-bulk`=fused+bulk；`combined`=recycle+bulk+fused；`combined-c1`再加连接数1。后两者各父实验及配置相邻保存。
- `cached`：三层共用value只做一次连续FP32布局准备，仍使用原生采样。精度正确，但本轮无明确端到端收益，默认关闭。
- `connections1`：独立连接数实验收益小且有波动，不单独声称稳定加速；纳入组合后的10对验证确认整体候选。
- `async-alloc`：cudaMallocAsync在READY前Graph捕获报Triton pointer不可访问，随后有captured allocation释放错误；未进入有效计时，完整错误日志和配置保留。不把失败记作性能分数，最终保持native分配器。

首组原方案398.593ms与后置358.883ms差异明显。单项结果只作筛选，**正式收益结论仅来自10对交错**，不以依次运行的首组对照解释每项贡献。

## 交错确认、最终入口与热点证据

完整20轮时间、AP50、AB/BA顺序、数据/预测/日志校验值见[10对实验](../20261025-181604-bottleneck-paired10/notes.md)和metrics.json。每个worker独立初始化、同一计时工具；bootstrap只量化本机样本波动，不代替3090或隐藏集验证。最终[wrapper三轮及验证](../20261025-182026-bottleneck-final/notes.md)独立于交错日志，未拼接为提交成绩。

同一会话、同版Nsight、相同200张真实输入、排除init的原方案与新候选诊断：

| 指标 | 原方案 | 新候选 |
| --- | ---: | ---: |
| 内核累计 | 166.861ms | 137.530ms |
| 内核调用数 | 22175 | 21050 |
| GPU活动并集 | 177.009ms | 147.679ms |
| 首末活动跨度 | 233.781ms | 186.165ms |
| 时间线覆盖率（不是SM利用率） | 75.72% | 79.33% |
| 主要Half拷贝内核 | 12.653ms / 375次 | 0.418ms / 150次 |
| 主要解码器concat内核 | 7.555ms / 100次 | 0.035ms / 25次 |
| 新融合attention内核 | 无 | 1.703ms / 75次 |

内核累计缩短 **17.58%**，是减少中间读写的直接证据，不当作端到端收益。两次profile输出均独立评分并通过官方校验。详细原始kernel表见[原方案profile](../20261025-182239-bottleneck-profile-control/nsys-summary.json)与[新候选profile](../20261025-182026-bottleneck-final/nsys-summary.json)。剩余主要开销有FP16转换10.53ms、特征pack8.89ms和FP32逐元素add/mul，以及CPU供给空档；未采集新硬件计数器，不能宣称带宽或算力饱和。约105ms退出区间此前已测，本轮未证明其根因或完全消除。

## 检查、失败和风险

- 初始数值与环形缓冲针对性检查38 passed；共享value替代检查3 passed；最终全套 **83 passed, 1 skipped**（可选TensorRT引擎缺失）。覆盖普通/非连续value、网格边界/越界、CUDA Graph重放更新、depth1/2/3、同步/异步、输入槽回收/批量格式化、11张合成图含尾批与复用。
- 12次完整验证运行均处理1030张并含6张尾批；58份真实参考输出含正式、交错和profile逐次校验与评分。新数值路径不是逐项bitwise保证，以数值容差测试及真实精度为准；最终AP50存在小幅波动，隐藏集尚未验证。
- full-tests.log、correctness.log、cache-correctness.log在output/父实验目录，SHA256见索引。Python编译、shell语法、git diff --check通过。
- 首次final驱动漏加仓库根sys.path，在启动GPU前失败，实验20261025-182005-bottleneck-final标abandoned，原注册和错误日志保留；修复后换新ID运行，未覆盖或篡改旧结果。
- cudaMallocAsync失败已完整记录；cached及所有无明确收益的独立方案保留开关与证据，未覆盖已验证候选。默认原入口仍可复现旧三项组合。

## 候选状态与复现

本轮比较组推荐候选：combined-c1及新wrapper；历史最短有效完整三轮日志302.713346ms保留，不能把不同日期结果直接续排。保守640完整解码高精度候选仍为20261022-official-fast-opencv-score005，validation AP50=0.9167。最近Accepted沿用既有本机/用户记录，本次未在线更新或重传；官方隐藏集最优未知。

新候选：`PYTHON_BIN=/home/ubuntu/.cache/supership-venv/bin/python OUTPUT_FILE='output/new-unique-run/reference.json' bash benchmark_bottleneck.sh`。原对照：清除EARLY_INPUT_RECYCLE、BULK_RESULTS、DEFORM_ATTN_IMPL等外部覆盖后使用benchmark_optimized.sh；精确可执行的全部环境与命令以子实验config.json/commands.json为准，COMMON_COMMANDS.md提供自动时间戳目录示例。

独立方案：`tools/reference/run_bottleneck_experiments.py`；交错确认：`confirm_bottleneck_candidate.py --control <原配置> --candidate <候选配置>`；最终完整入口/验证/profile：`finalize_bottleneck_candidate.py --config <候选配置>`。这些驱动自动先创建唯一ID、登记与提交配置，再测量；输出目录必须新建，不复用旧产物。竞赛提交独立于这些脚本，本轮未执行。

Git成果在exp/bottleneck-opt-20261025提交推送。main的外部合并冲突未处理；主台账只合并本次状态摘要，因已有冲突暂留本地，完整证据在本独立分支可复现。

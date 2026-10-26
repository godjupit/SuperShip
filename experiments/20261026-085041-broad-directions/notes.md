# 四个性能瓶颈方向的独立对照

实验 `20261026-085041-broad-directions`；负责人Codex/root；分支 `exp/broad-directions-20261026`；状态 **completed**，2026-10-26 09:03CST。GPU0 RTX4090独占08:50–09:01，已核实空闲并释放。

本轮先核实main `6ff8eebbe1844d400514bfc0c4a24b1fd1497419` 的推理实现仍与已验证最快thread100-light相同，再从main建立隔离实验。按用户要求覆盖CPU供给、退出、GPU算子，以及额外的输出落盘方向。**四项均未得到稳定端到端收益，不晋级main。** 保留全部代码、失败与原始结果；最近Accepted258.409792ms和保守路径不变，无竞赛上传。

## 初筛与复测

| 方向 | 实验内容 | 三轮中位数ms | 结论 |
| --- | --- | ---: | --- |
| 基线开头 | 当前最快thread100-light |251.709695|末尾对照260.910024ms，存在时间漂移|
| CPU | 一次整文件读取后用同一OpenCV库imdecode |258.700938|8对257.600508→260.544697ms，慢1.1429%，3/8胜，p=0.640625；不采用|
| GPU | 所有输入已经FP16/channels-last时用原生cat，否则原Tritonpack |255.685603|8对257.714756→256.471031ms，名义快0.4826%，4/8胜，p=0.6875；不确认收益|
| 退出 | READY前为自身私有匿名/heap完整2MiB区间MADV_HUGEPAGE，并在init等12秒 |269.883890|申请成功但实际覆盖几乎不增；不采用|
| 输出 | fsync替换为fdatasync，保持flush、必要元数据/数据落盘、关闭和完整退出 |260.065426|无初筛收益，不采用|

全部逐轮时间、8对顺序和异常轮次见[results.md](results.md)及各JSON。配对使用完整worker单轮，AB/BA交替；精确双侧符号翻转检验基于每对时间差。GPU第6对基线295.831ms保留，是观察到的波动，不能挑除后宣称提速。CPU和GPU的名义百分比只比较各自同期配对控制；顺序初筛不可当作收益。

## 各方向证据

**CPU供给**：边界IO探针中read系统调用14559→404，减少97.2%，逻辑读取58,390,962→57,571,762bytes（stdio读取块边界不同），物理read_bytes始终0。CPU用户+系统时间1749.090→1729.010ms，只减少约1.15%。所以减少系统调用未解决主要解码工作，线程与临时内存开销可能抵消节省；本轮没有直接证明后一个归因。两者使用同一OpenCV/JPEG解码和同一resize/RGB路径，55份结果均字节一致。

**退出**：本机Linux5.15，本地头文件只有MADV_HUGEPAGE，未尝试不支持的MADV_COLLAPSE。只向本进程的rw-p匿名区域及heap内部完整2MiB区间申请，不更改系统THP策略/扫描频率，不访问评测输入。约1.49GB申请均返回成功，但三轮等待12秒后AnonHugePages增加0/4/4MiB；IO探针另增加4MiB。实际覆盖增幅不足，12秒初始化等待没有换来可确认的退出收益，独立探针退出51.786ms，仍接近历史50–56ms。建议不保留该额外初始化等待。原有glibc THP设置继续保持。没有重跑已否定的malloc_trim/empty_cache/deviceReset等方案。

**GPU算子**：合成测试从模型的合成初始化提取13组真实feature规格（每批14次cat），只使用随机张量，完全不接触评测图像。每组分别捕获8次调用的CUDA Graph，32次replay并做5轮交替事件计时。按调用次数加权，原Tritonpack约0.399525ms/批，条件原生cat约0.405650ms/批，微测也未改善。大尺寸第一层cat79.99→90.16us，若干小层改善被抵消。此加权微测不能直接与E2E或Nsightkernel总时间相加；使用随机数据、CUDA Graph池和缓存条件不同，不代表真实模型完整时间。所有微测、图重放和混合dtype/layout输出精确一致。

**落盘**：fdatasync仍在计时区间内完成，文件关闭和进程正常结束同样计入，未省略同步或另起脱离的后台任务。完整三轮264.462374/259.108275/260.065426ms，没有优于同组开头控制的证据。该变体不用于替换默认fsync。

## 边界诊断的限制

每个变体另做1次独立IO/退出探针，详情保存在screen.json的boundaries字段。基线该次核心260.373ms显著慢于历史典型208–212ms，完整318.306ms；原因未确定且结果保留，因此不能直接把该轮与CPU219.803ms或GPU204.755ms相减宣称40–55ms优化。退出/输出探针总时间分别270.621/287.568ms，同样只作诊断，不作为性能成绩。多次诊断不是同一时间线，CPU服务、GPU活动和其他线程开销可能重叠。

## 正确性、来源与可复现性

- 18次正式三轮输出+5次独立诊断+32次配对输出，**共55份**，每份200张/6102检测，官方格式检查/评分均通过，reference AP50全部0.7809；实际reference基线0.7935，98%门槛0.77763，比值0.984121、绝对裕量0.00327。validation AP50=null，hidden AP50=null，官方隐藏集最优未知；未测更大数据，也未对隐藏精度作推断。
- 55份输出全部SHA256 `4185ed612afb8234afae8e31eb43bafd0b68ef32c124d0d510d2da745f29100c`，与父版本相同。基线及四个独立方向只变化记录的单一配置项，完整其余参数见每个command.json/env_overrides和screen/confirmation文件。
- 54项相关唯一检查通过：像素、RGB、奇数JPEG、损坏图像、混合dtype/layout、随机输入图重放、异步/输入槽复用/尾批/空输入、线程JSON，以及私有匿名区域选择。其中初测2项奇数PNG测试假设有误，原基线在reduction2/4时因floor/ceil尺寸差拒绝该输入；改成两条读取路径都必须同样拒绝后7项受影响CPU检查通过。初测52pass/2fail和原测试源码保留在output，推理行为未因测试修正改变。
- 当前硬件/依赖沿用上一轮：RTX4090、EPYC7402/10核、driver550.142、PyTorch2.6.0+cu124/cuDNN90100、OpenCV4.11、Triton3.2。输入是热缓存，非冷盘。heap变体RSS约1.59GiB且等待前后增幅很小；本轮未重测32GB硬上限，未扩张模型或精度。
- 官方timer/scorer/validator/权重/全部200图像哈希与父manifest一致；所有原始文件SHA256和源码校验和在checksums.json。无未提交推理补丁。Python编译、gitdiff检查通过。

实际初筛和CPU配对源码完整SHA `09f147dfd507b7101556fabd0033072f617035b4`，GPU配对及微测源码 `2cb44378d1b3451be003b65badcaa5de3eb64fcc`；两提交之间只有脚本/记录变化，推理文件相同。旧main本地已有AGENTS修改未混入本轮提交。

原始日志、预测、探针和初始失败测试源码只在本机 `/tmp/SuperShip-broad-directions-20261026/output/20261026-085041-broad-directions/`，main/output下同ID链接到这里。Git保存必要脚本、配置覆盖、摘要、哈希和图。外部机器需要与manifest匹配的公开数据、权重、环境以及重新运行；本机路径不是完整可移植产物。

在隔离worktree提供data/SuperShip和weights/baseline.pth后复现：初筛/CPU配对检出09f147dfd507b7101556fabd0033072f617035b4（该提交尚无结果JSON），运行以下前两条；GPU配对/微测检出2cb44378d1b3451be003b65badcaa5de3eb64fcc（尚无对应GPU结果JSON），运行后两条。驱动拒绝已有结果/目录，保留历史，不在包含结果的最新提交上覆盖运行。需按机器调整run.py中的Python路径；完整preset从父thread100-light JSON读取，删除本机Triton缓存路径，glibc THP在解释器启动前设置。

```bash
/home/ubuntu/.cache/supership-venv/bin/python experiments/20261026-085041-broad-directions/run.py
/home/ubuntu/.cache/supership-venv/bin/python experiments/20261026-085041-broad-directions/run.py --confirm cpu --pairs 8
/home/ubuntu/.cache/supership-venv/bin/python experiments/20261026-085041-broad-directions/run.py --confirm gpu --pairs 8
GLIBC_TUNABLES=glibc.malloc.hugetlb=1 /home/ubuntu/.cache/supership-venv/bin/python experiments/20261026-085041-broad-directions/micro_pack.py
```

下一步应优先考虑能减少实际JPEG解码/resize服务量的单一新假设；本轮说明减少read调用、申请更多大页、条件原生cat和替换同步API都不能直接解决当前主要端到端瓶颈。

Main仅归档本轮记录；未证实有益的实现、测试与驱动保留在 `exp/broad-directions-20261026`（归档提交5339524）。按上文具体源码SHA复现，main继续使用原最快实现。

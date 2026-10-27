# 优化版本索引

## 20261027-114732-node-g0005

- Owner Codex/root；main source `7c8a161e3989b5ab341069fa7d3734975ad2145d`；status completed；用户要求切到五小时作业1351172，g0005/RTX4090/8核，分配结束15:57:33CST；11:47–11:48运行前GPU无计算进程，显存1MiB/利用率0。
- 与g0067全本地运行对照：精确thread100-light JSON、固定8核、200张参考集三轮、输入/预测/完整日志均位于节点/tmp NVMe，结束后同步结果到 `output/20261027-114732-node-g0005/`。不增加CPU，不改实现，不进行竞赛提交。旧节点分配保留，不终止用户交互shell。
- 命令：`srun --jobid=1351172 --overlap --ntasks=1 --cpus-per-task=8 --chdir=/data/run01/sczf193/SuperShip-main bash output/20261027-114732-node-g0005/run.sh`；完整执行脚本保存在上述本机输出目录，部署副本 `/tmp/supership-20261027-114732-node-g0005/` 留在g0005。环境为EPYC7502、Python3.11.11、torch2.5.1+cu124、OpenCV4.11.0，准确驱动/CPU/配置与数据权重校验和见environment.log；只有台账/运行说明未提交改动，无运行源码改动。
- 全三轮 `0.305249523 / 0.299772560 / 0.313619927` 秒，中位 **0.305249523**；每轮完整200张、6102检测、官方格式检查及评分通过，reference AP50均0.7809。输出SHA256与历史及g0067均为 `4185ed612afb8234afae8e31eb43bafd0b68ef32c124d0d510d2da745f29100c`；validation/hidden未测。新节点本轮比g0067的0.261382914秒稍慢，属于节点环境对照，不据三轮筛查宣称稳定差异或调整main候选。后续按用户要求使用五小时g0005分配，GPU任务已完成，分配保留。

## 20261027-114037-storage-diagnosis

- Owner Codex/root；main `7c8a161e3989b5ab341069fa7d3734975ad2145d`；status completed；GPU g0067/RTX4090，分配1351209，11:40–11:47CST，启动前GPU空闲。仅运行诊断，不改实现、不晋级候选、不竞赛提交；本会话工作已结束，用户分配保留。
- 核对最近thread100-light JSON与默认配置，排除环境覆盖；单一主要假设：共享JuiceFS输入/输出造成约1.6秒延迟，比较完全相同配置下共享存储三轮和本地NVMe输入/输出三轮，另立存储比较组，分别评分。节点为EPYC7502、分配8核；完整数据准备作为显式部署步骤，worker仍须READY后访问输入。原始结果 `output/20261027-114037-storage-diagnosis/`，本地数据与结果保留于该节点唯一/tmp目录，不缓存评测答案。
- 11:43追加诊断登记：用户明确CPU固定8核，禁止增加分配。保持默认配置分别做共享/本地一次独立插桩诊断，将核心处理与退出区间分开（插桩结果不作正式性能比较）；确认剩余差距来源。随后本地盘 workers8/6各完整三轮仅检查固定8核下线程竞争，保留默认10线程对照；未确认收益前不改默认配置。
- 11:46追加单一存储假设：上面的本地输入/输出对照仍将worker stderr日志写到共享盘，完成阶段的stderr flush包含在官方计时内。新增最近默认10线程配置、本地输入/输出/日志完整三轮，结束后再拷回共享目录；不屏蔽日志、不改计时器、不省略fsync，保持固定8核。
- 已完成：默认10线程、共享输入/预测/日志三轮 `0.591817180 / 0.460150161 / 0.955263980` 秒，中位0.591817180；本地输入/预测、共享日志三轮 `0.355758293 / 0.485003780 / 0.459530471` 秒，中位0.459530471；**本地输入/预测/完整日志**三轮 `0.260419176 / 0.282751773 / 0.261382914` 秒，中位 **0.261382914**，与历史约0.258秒接近。全部固定8核，不是增加CPU的收益；最近JSON所有参数不变。顺序筛查未做配对显著性检验，不宣称存储收益的精确因果百分比。
- 仅插桩诊断（非正式对比）：共享核心0.345783秒/端到端0.928055秒；本地核心0.196726秒/端到端0.418281秒，两个日志仍在共享盘，剩余区间含末尾stderr刷新和进程退出，不能全归因内核退出。最终全本地日志实验支持共享日志刷新是关键额外开销；首次1.612565秒还有共享存储冷热/波动，未逐项量化。
- 固定8核线程筛查：workers8三轮0.430404523 / 0.371507274 / 0.422572330，中位0.422572330；workers6三轮0.365634567 / 0.550403962 / 0.352342635，中位0.365634567（均本地输入/预测、共享日志）。波动较大，不更改默认10线程配置，不据此推荐新的最快参数。
- 全部15个正式筛查worker完整处理200张/每轮6102检测，逐轮reference AP50均0.7809；预测SHA256均 `4185ed612afb8234afae8e31eb43bafd0b68ef32c124d0d510d2da745f29100c`，与历史最佳输出一致；validation/hidden未测。完整命令脚本、环境、逐轮日志、评分、预测与校验和保留在本机上述output目录；节点/tmp副本保留，不代表跨机可获得。可复现的全本地命令已写入 docs/commands.md；未修改模型/worker/评分器或默认配置。

## 20261027-113500-runtime-reference

- Owner Codex /root；branch main；source `a39ea8e81f1ad0bcd75072f1101bc5ca1fc1e603`；status completed；2026-10-27 11:35–11:39 CST；GPU 分配 `1351209`，节点 g0067，RTX4090。启动前调度状态 RUNNING，GPU 显存占用0、利用率0，无其他计算进程；结束后GPU显存占用0，无本会话任务残留，保留用户的现有调度分配。
- 用户授权运行项目；复用现有有效分配，不在登录节点执行计算。不修改推理实现，使用 configs/fastest.env 默认参数；参考集完整三轮和逐轮评分，独立目录 `output/20261027-113500-runtime-reference/`。新环境比较组，仅验证运行，不直接与历史速度排名，无竞赛提交。
- 环境：8个分配CPU，Python3.11.11、torch2.5.1+cu124、OpenCV4.11.0、驱动580.82.07；依赖和CPU资源与历史环境不同，存储冷热状态未控制，不跨组比较。未改运行源码；本次未提交改动仅为台账。所有配置来自 configs/fastest.env，无性能参数覆盖。
- 实际运行：`srun --jobid=1351209 --overlap --ntasks=1 --cpus-per-task=8 --chdir=/data/run01/sczf193/SuperShip-main bash -c 'export PYTHON_BIN=/data/run01/sczf193/supership-venv/bin/python TRITON_CACHE_DIR=/data/run01/sczf193/.triton/cache PYTHONUNBUFFERED=1 OUTPUT_DIR=output/20261027-113500-runtime-reference; source configs/fastest.env; bash tools/benchmark/evaluate.sh reference --runs 3'`。复现须替换有效作业ID和唯一输出目录，不复用本次输出路径。
- 三轮耗时 `2.870352228 / 1.612564610 / 1.488872158` 秒，中位 `1.612564610` 秒；每轮完整处理200张（batch8，无尾批），6102条检测，官方工具格式检查及逐轮评分成功。reference AP50三轮均0.7809，相对本地参考基线0.7929比值0.984866，98%门槛0.777042、裕量0.003858；仅为本地参考判据，validation/hidden未测。
- 三轮预测字节一致，SHA256 `4185ed612afb8234afae8e31eb43bafd0b68ef32c124d0d510d2da745f29100c`；原始计时日志SHA256 `603aa2d8ae52d93ea7b9620774ee059450d301cfc6f467ed9289cc19ae901e78`；元数据SHA256 `7372e6e602a0f11edf8714c731b63709ada4644eb5feadf76a074ff64554d443`，权重SHA256与下方审查记录一致。环境、全部计时/评分日志、预测及SHA256SUMS仅存本机上述output目录，未上传。候选推荐及Accepted不变，无竞赛提交。

## 20261027-095206-sync-review

- 负责人 Codex /root；分支 main；基于 `99732c143da6658efa4cc4760b68ce9a8c597e78`；审查与 Git 同步状态 completed；GPU 运行状态 blocked（当前为登录节点，无 GPU 分配，查询无空闲 GPU）。本次不是性能优化实验，无竞赛提交。
- 本地原先为无提交、无远程的 Git 目录；已接入 origin/main 历史，保留本地文件后比较。engine/、supership/、run.sh、configs/fastest.env 与云端一致；恢复缺失的 docs/ 和 configs/presets/，修复本地旧 README/台账及忽略规则与当前云端布局不一致的问题。被替换的本地文档保存在 `output/sync-review-20261027-095040/`，仅本机可用。
- 基线权重 SHA256 为 `42a04535d33de94acc58ae3c66a9a2d161e975ee17adae6cae533770d1929c3e`，与 RELEASE_INFO.json 一致。未跟踪的旧实验脚本 `tools/reference/run_further_experiments.py` 含失效路径、过时基线和旧成绩重传逻辑，不运行、不提交；其他已有未跟踪文件保留。
- 使用 `/data/run01/sczf193/supership-venv/bin/python` 尝试默认入口，报错 `Found no NVIDIA driver`；日志 `output/startup-review.log`。全量 pytest 未完成，用户明确节点限制后已终止本会话测试及其子进程，不能记作测试通过。今后包括 CPU 测试在内的任务只在调度分配的 GPU 计算节点执行，规则写入 AGENTS.md。
- reference/validation/hidden AP50 均未测，无新计时结果；最快候选、保守候选与最近 Accepted 不变。下一步：获得 GPU 调度分配后执行 `PYTHON_BIN=/data/run01/sczf193/supership-venv/bin/python bash run.sh --worker` 并通过官方 worker 协议提供输入；在该节点补跑 `python -m pytest -q`。

2026-10-26 按用户要求清理旧实验、结果、重复源码快照和无收益分支。以下仅保留选版依据与代码/参数定位；原始结果已删除，数值为历史记录摘要，本次未重新计时。

| 保留分支 | 依据 | 参数 |
| --- | --- | --- |
| main | 默认最快 thread100-light，完整三轮复测中位 261.305519ms | configs/fastest.env |
| exp/continued-sweep-20261026 | 参考集三轮 258.409792 / 256.334286 / 263.016448ms，中位 258.409792ms；8 对快 4.8507%，8/8 胜；reference AP50=0.7809 | configs/presets/thread100-light.json |
| exp/exit-rootcause-20261026 | THP 六对中位 356.261538→289.448907ms；独立三轮中位 285.962649ms；validation AP50=0.9058，32GiB 限制通过 | configs/presets/exit-thp544.json |
| exp/kernel-sweep-20261024 | 历史完整三轮中位 302.713346ms；内核融合十对快 6.70%；validation AP50=0.9058 | configs/presets/kernel544.json |
| exp/rtx4090-e2e | 保守 640 输入、完整 JPEG 解码；validation AP50=0.9167 | configs/presets/conservative640.json |

这些指标来自不同日期/协议比较组，不能据此跨组排名。本地最快候选为 thread100-light；保守候选为 640 完整解码。最近 Accepted：2026-10-26 08:23:38，0.258409792 秒，仅 timing parsed。thread100-light 的 validation 未测；所有 hidden AP50 未测，官方隐藏集最优未知。原始回执已清理，此处不构成新提交或新精度验证。

## 清理记录

- ID: 20261026-135116-repository-cleanup；负责人 Codex /root；状态 completed；未使用 GPU，未进行竞赛提交。
- 清理前 main: `fd7d8beae5486299195008bb9ac64cf7a03de51d`。
- 删除旧实验目录、结果/报告/patch、重复源码快照、无收益/诊断分支、闲置 worktree、重复数据下载包、缓存与旧课程笔记本。
- 保留运行源码、模型配置、精选运行参数、测试、公开数据、基线权重、本机凭证和必要文档。
- 未重写历史、未强制推送。普通 Git 提交保留恢复路径；历史文件仍可能占用 Git 对象空间。
- 保留分支的清理前源码 SHA 如下。较早版本的运行协议/依赖以对应源码为准。

- `main`: `fd7d8beae5486299195008bb9ac64cf7a03de51d`
- `exp/continued-sweep-20261026`: `1da325e5a7cf4fe3ff485855622dc22100fd848a`
- `exp/exit-rootcause-20261026`: `6a774ee970eef2fcb32c7a5f01086780700a1e7f`
- `exp/kernel-sweep-20261024`: `d0db0d31148319923efe9eb05fb2ad3f19afa4fd`
- `exp/rtx4090-e2e`: `1c73be3b749dad59a1ec9cc083b115d09cac5ff9`

- 清理检查：主线 126 passed / 44 skipped（可选 GPU/部署相关检查未执行）；shell 语法、参数 JSON 和入口文档链接通过。保留历史分支的 engine/supership/run.sh/模型配置/测试字节未变，已通过差异核对；未重新运行性能计时。

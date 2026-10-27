# 优化版本索引

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

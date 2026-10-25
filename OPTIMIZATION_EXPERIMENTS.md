# 优化日志

时间均为北京时间。完整过程与结果统一放在 **[experiments/](experiments/README.md)**；原分支继续保留自己的代码和记录。各轮原始时间和失败方案不在此重复展开。

| 时间 | 优化方案 | 结果与状态 |
| --- | --- | --- |
| 10-16 | 批量回传、锁页/异步传输、JSON批量写盘 | RTX3090验证集单次17.452→9.536秒，AP50=0.9170 |
| 10-16 | CUDA Graph、TensorRT、INT8、剪枝/蒸馏 | Graph单次9.384秒；低精度/无收益方案完整保留 |
| 10-22 | CUDA Graph组合 | RTX4090参考集三轮中位5.128→3.172秒，AP50=0.7935 |
| 10-22 | OpenCV半尺寸解码、FP16、流水线/后处理 | 历史参考集0.4766秒，validation AP50=0.9101 |
| 10-22 19:59 | 544输入、异步流水线 | 参考集0.3798秒，validation AP50=0.9054 |
| 10-23 23:07–23:57 | 99对Conv-BN融合并验证主线 | 10对中位快4.76%；主线复测0.3308秒，validation AP50=0.9057 |
| 10-24 00:04–00:29 | FP16权重、1×1转Linear、Triton特征拼接 | 历史完整三轮0.302713秒；10对快6.70%，validation AP50=0.9058 |
| 10-25 17:47–17:56 | 最快三项组合性能诊断 | 定位CPU供给、约105ms退出区间、cross-attention搬运 |
| 10-25 18:04–18:23 | 提前回收输入槽、批量结果、Triton注意力、单连接 | 10对371.4→329.0ms，快11.44%；新完整三轮316.5ms，validation AP50=0.9056；未覆盖历史约304ms |
| 10-25 | 目录归档、全分支汇集 | 已完成：9分支源码/129份原始记录集中归档，非性能实验 |
| 10-25 19:00 | Git收尾与官方规范同步 | 上游冲突已解决；批量回传兼容检查及93项测试通过；整理落到main |
| 10-26 00:06–00:26 | 定位退出时主机小页回收，启用透明大页 | 6对中位356.262→289.449ms，快18.75%；独立三轮285.963ms已Accepted；validation AP50=0.9058，32GiB硬限制通过、峰值RSS2.025GiB |
| 10-26 00:29–00:37 | 已接受THP版本的时间构成诊断 | 无插桩三轮中位293.056ms；核心约221–232ms、退出61–93ms；GPU活动147–153ms并有38–46ms空档；热缓存下CPU解码供给优先；[记录](experiments/20261026-002932-profile-thp/notes.md) |

以上GPU、数据划分和计时组不同，不能直接按一列排榜。RTX4090参考集不等于RTX3090或隐藏集成绩；所有hidden AP50均未测。

| 当前状态 | 定位 |
| --- | --- |
| 历史最短有效完整参考日志 | 20261024-001935-kernel-weights-linear-concat，0.302713346秒；[记录](experiments/20261024-001935-kernel-weights-linear-concat/notes.md) |
| 当前比较组推荐候选 | 20261026-000619-exit-rootcause：主机透明大页；6对交错356.262→289.449ms，5/6更快；独立完整三轮285.962649ms；[记录](experiments/20261026-000619-exit-rootcause/notes.md) |
| 保守高精度候选 | 640完整JPEG解码，validation AP50=0.9167；[记录](experiments/20261022-official-fast-opencv-score005/notes.md) |
| 最近Accepted信息 | 2026-10-26 00:24:37，账号ruc2602，SUPERSHIP 0.285962649秒；[脱敏回执](experiments/20261026-000619-exit-rootcause/submission-receipt.txt)；仅计时解析，hidden AP50未测 |
| 官方隐藏集最优 | 未知 |
| 任务状态 | 20261026-002932-profile-thp：completed；14份参考输出校验/评分通过，时间构成与热点证据已保存；GPU0于00:37释放；Accepted成绩保持285.962649ms |

**常用入口**：运行`bash run.sh --worker`；基准/评分脚本在[tools/benchmark/](tools/benchmark/)；开发环境在[tools/dev/](tools/dev/)；主目录源码保持main原版本，其他优化代码见[分支快照](experiments/branches/README.md)。

[完整结果表](experiments/results/README.md) · [全部历史报告](experiments/reports/) · [各分支台账与SHA](experiments/branches/README.md) · [数据/原始产物](experiments/data/README.md)


主线已合并官方42460fba规范/评分更新；历史指标按固定SHA保留。10-26退出实验另建当前协议比较组，已按本次授权提交新日志。

## 20261026-000619-exit-rootcause

- Owner: Codex /root; branch `exp/exit-rootcause-20261026`; status **completed**; updated 2026-10-26 00:26 CST.
- Base: main `90bcc6165f6d65b5f6a16bb1298af83465a54d04`; optimized runtime parent `9a195679dbea` (full SHA recorded in experiment). Current main official protocol/scorer retained; new comparison group, historical timings are context only.
- Scope: reproduce and trace the ~105ms exit interval, implement a measured fix without changing timing boundaries, validate reference/validation accuracy and >=3 full runs.
- GPU0 RTX4090 reserved 00:06–00:26 CST after idle checks; released after final tests/timing. Worktree `/tmp/SuperShip-exit-20261026`. Complete1030-image validation and 32GiB hard memory cap passed (peak worker RSS2.025GiB), 101 tests passed/1 optional skip. User authorized system submission; new intact three-round log accepted at00:24:37,0.285962649s. Hidden AP50 unmeasured; official hidden best unknown. Main receives launcher fix only; optimized runtime remains on experiment branch.

## 20261026-002932-profile-thp

- Owner Codex /root; branch `exp/profile-thp-20261026`; status **completed**; updated 2026-10-26 00:37 CST.
- Parent `exp/exit-rootcause-20261026` at `6a774ee` (full SHA in experiment); target is the accepted285.962649ms optimized runtime, not main's standard pipeline.
- GPU0 RTX4090 reserved00:29–00:37 after idle checks, released; worktree `/tmp/SuperShip-time-20261026`. Scope: three unchanged-protocol baseline runs, main-thread stage and boundary probes, inference-only Nsight kernel/transfer timeline, prioritized bottleneck analysis. No inference changes or new competition submission; preserve current Accepted log. Host32GB constraint retained.

诊断结论（20261026-002932-profile-thp）：主线程输入Future等待164–183ms与GPU执行重叠，不能作为纯GPU空闲；Nsight独立测得GPU空档38–46ms。三轮物理读取0bytes，核心约1.6 CPU秒/7.2核；主要方向是解码/预处理供给、退出尾延迟、GPU转换/特征pack。完整三轮参考AP50=0.7809/0.7812/0.7809；validation AP50沿用未改动父版本0.9058，本轮未重测；hidden未测。无推理改动、无新竞赛提交，候选与最近Accepted不变。

## 20261026-004444-supply-exit

- Owner Codex /root; branch `exp/supply-exit-20261026`; status **abandoned**; updated2026-10-26 01:10 CST; user requested another optimization direction. Parent accepted runtime/diagnostics `67f2d7f` (full SHA in experiment).
- GPU0 RTX4090 reserved from00:44 after idle check. Worktree `/tmp/SuperShip-supply-20261026`. Separate hypotheses: faster CPU JPEG decoder and supply scheduling; reduce unnecessary inference imports to lower host-memory exit cost. Register each variant before running, preserve failures and compare against unchanged accepted runtime.
- Required: exact public200 reference/1030 validation coverage, tail handling, >=3 independent complete timings and paired confirmation;32GB host cap; user authorization for Git push and competition submission persists. No altered timer/scorer or pre-READY evaluation access; only a faster validated complete log may replace currentAccepted285.962649ms.

CPU-supply route20261026-004444-supply-exit abandoned at user request. Ten-pair light10 result inconclusive (5/10wins, CI crosses0); resize trials unpromoted. Full records on exp/supply-exit-20261026; local raw artifacts preserved in main output/20261026-004444-supply-exit (dependency symlinks retained). Accepted285.962649ms unchanged. GPU0 handed over to new fusion experiment, no concurrent GPU work.

## 20261026-011014-fuse-affine

- Codex /root; branch `exp/fuse-affine-20261026`; status **running**; updated2026-10-26 01:10 CST. Parent accepted runtime/diagnostics67f2d7f (full SHA in notes).
- GPU0 RTX4090 reserved from01:10, verified idle. Worktree `/tmp/SuperShip-affine-20261026`. Hypothesis: fuse HGNetv2 ReLU+float32 learned affine without changing scalar dtype, image decode/resize, model structure or precision policy; disable FMA and verify against original arithmetic. Exact-output tests, reference/validation and full timing required before promotion;32GB cap retained.

## 20261026-013427-validation-sweep

- Owner Codex /root; branch `exp/validation-sweep-20261026`; status **running**; updated2026-10-26 01:34 CST. Parent `222dc7a6b2c7bdf799e207362d648ff242e23fd3`; isolated worktree `/tmp/SuperShip-val-sweep-20261026`.
- Latest user instruction: skip reference-set testing; optimize multiple directions and pursue scores. No reference jobs launched by this experiment pending clarification of submission-only timing. Full1030-image validation screens batch size, loader count and queue depth on the existing affine fusion candidates; one hypothesis per configuration, all outcomes retained. No timer/scorer changes or pre-READY data access.
- GPU0 RTX4090 reserved01:34 after process/idle checks; no previous experiment GPU processes remain. Parent fast-score-results.json and sanitized receipt confirm Accepted **0.280231356s** at2026-10-26 01:28:59 for half-output (log SHA256 `757f6037b42e223f850dffe227a906d812a9f48adcd164f39c1774596d5ddd7c`); main's older285.962649ms entry is stale. Acceptance is timing parsed only; hidden AP50=null. No old log resubmission.

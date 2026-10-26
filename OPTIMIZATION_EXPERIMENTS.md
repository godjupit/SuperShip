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

| 10-26 07:55–08:28 | 50方向筛选、输出重叠和精简推理导入 | Accepted265.317→258.410ms；8对中位276.220→262.821ms，快4.8507%，8/8胜；reference AP50=0.7809，82项检查通过；[记录](experiments/20261026-075543-continued-sweep/notes.md) |

以上GPU、数据划分和计时组不同，不能直接按一列排榜。RTX4090参考集不等于RTX3090或隐藏集成绩；所有hidden AP50均未测。

| 当前状态 | 定位 |
| --- | --- |
| 历史比较组最短有效参考日志 | 20261024-001935-kernel-weights-linear-concat，0.302713346秒；[记录](experiments/20261024-001935-kernel-weights-linear-concat/notes.md) |
| 本地最快候选 / 当前比较组推荐 | 20261026-075543-continued-sweep/thread100-light；完整三轮 **258.409792ms** 已Accepted，reference AP50=0.7809；8对中位快4.8507%；[记录](experiments/20261026-075543-continued-sweep/notes.md) |
| 保守高精度候选 | 640完整JPEG解码，validation AP50=0.9167；[记录](experiments/20261022-official-fast-opencv-score005/notes.md) |
| 最近Accepted信息 | 2026-10-26 08:23:38，ruc2602，**0.258409792秒**；[脱敏回执](experiments/20261026-075543-continued-sweep/submission-receipt.txt)；timing parsed only，hidden未测 |
| 官方隐藏集最优 | 未知 |
| 任务状态 | continued-sweep completed；旧会话已中断，output-overlap实现由本实验接管；GPU0已释放 |

**常用入口**：运行`bash run.sh --worker`；基准/评分脚本在[tools/benchmark/](tools/benchmark/)；开发环境在[tools/dev/](tools/dev/)；主目录源码将按用户要求同步最快已验证候选，其他优化代码见[分支快照](experiments/branches/README.md)。

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

2026-10-26 01:38 clarification for20261026-013427-validation-sweep: user means skip larger validation, run200-image reference and score. Stop all larger-set runs (already completed). Now screen three registered complete3-round logs for half-w10, half-w10-b16, half-w10-depth5; submit only valid improvements overAccepted280.231356ms. GPU0 remains reserved; official timer and scorer unchanged.


Completion 2026-10-26 01:40 CST —20261026-013427-validation-sweep: **completed**, GPU0 released. User clarified200-image reference allowed, larger validation skipped thereafter. Three candidate logs /9reference outputs passed. half-w10 median275.737156ms (268.183722/275.737156/304.649908), half-w10-b16 median276.850853ms, half-w10-depth5 median291.720128ms. Only half-w10 uploaded;Accepted2026-10-26 01:39:08,275.737156ms, timing parsed only. Reference AP50>=0.7809; prior validation0.9055–0.9056 for half-w10, hidden=null. Slight score improvement1.60% vs prior280.231356ms overlaps observed variance. [Results](experiments/20261026-013427-validation-sweep/notes.md); source/commands/hashes preserved; no timer/model source changes.


## 20261026-014213-configwide

- Codex /root; branch `exp/configwide-20261026`; status **running**; updated2026-10-26 01:42 CST. Parent `509fe983b6864cbcbda1b8f52641c942dd11328a`; worktree `/tmp/SuperShip-configwide-20261026`. GPU0 RTX4090 reserved from01:42 after idle checks.
- User explicitly requests sustained optimization until quota ends.200-image reference-only search; no larger validation.17 individually registered config hypotheses (batch6/10/12/24/32, workers9/11, depth2/4, decoder2, encoder layout, native cat, exact affine, fixed cuDNN, arena2, score0.075, control). Complete3-round logs/output checks before immediate upload of strict improvements overAccepted275.737156ms. All outcomes retained; hidden=null.


## 20261026-014417-fusedio

- Codex /root; branch `exp/fusedio-20261026`; status **running** (CPU work only); updated2026-10-26 01:44 CST. Parent `509fe983b6864cbcbda1b8f52641c942dd11328a`; worktree `/tmp/SuperShip-fusedio-20261026`. GPU remains reserved exclusively for configwide; new kernels tested only after handover.
- Registered: fuse uint8 normalization, fuse detection output geometry/gather, segmented feature packing, kernel block tuning, light inference imports, query-count/output-count screening. Opt-in individual gates and full200-image three-round checks, no large validation; only faster valid logs uploaded.

2026-10-26 01:50 CST GPU handover: configwide17-case suite complete,51worker outputs,2reference precision-failed configurations (decoder2,score0.075) not uploaded; latestAccepted266.237340ms (cudnn-fixed), timing-only. GPU0 verified idle and reserved now for fusedio tests/screens. All16 fusedio configs inherit new CUDNN_BENCHMARK=0 parent from configwide/cudnn-fixed; baseline floor refreshed266.237340ms. No larger validation jobs.

20261026-014213-configwide **completed** at01:50 CST;17configs/51rounds; latestAccepted266.237340ms,cudnn-fixed,01:49:15; decoder2/threshold0.075 failed referenceAP, no upload. GPU handed to fusedio. Full evidence experiments/20261026-014213-configwide/notes.md.


## 20261026-015358-output-overlap

- Codex /root; branch `exp/output-overlap-20261026`; status **running** (CPU implementation only); updated2026-10-26 01:54 CST. Parent `0cd93cb12821da085172ca470c0e71e836de7016`; worktree `/tmp/SuperShip-output-20261026`. GPU remains exclusively with fusedio until explicit handover.
- Register threaded per-batch JSON formatting/serialization, byte-identical output order/rounding, prestarted thread and joined tasks, full final fsync/exit included. Synthetic correctness then complete200-image3-round accuracy/timing; no large validation.


## 20261026-075543-continued-sweep

- Owner Codex current /root continuation; branch `exp/continued-sweep-20261026`; status **completed**; updated 2026-10-26 08:28 CST. Parent `0cd93cb12821da085172ca470c0e71e836de7016`; isolated worktree `/tmp/SuperShip-continued-20261026`.
- Fresh process audit found no benchmark/worker/scoring processes and idle GPU0; fusedio last raw result at01:55 (6 hours old). Reserve GPU0 from07:58 for this continuation; output-overlap has CPU-only reservation and must wait for handover. Other worktree modifications left untouched.
- New hypotheses: pinned reusable image-size transfers, CUDA event reuse, batch7/9/14 tails, smaller/larger model geometry under reference accuracy gate, intermediate query counts, top-k output sizing, GLIBC mmap/arena and torch/OMP thread settings. Each variant registered in plan.json before running, unchanged official timer/scorer, all200 inputs afterREADY, complete3-round timing, no larger validation. Current floor266.237340ms; only fresh passing improvements eligible for competition upload.


2026-10-26 08:00 CST continuation resource conflict: another independent live Codex session resumed fusedio at07:56 and has a model-deploy benchmark active at08:00. Continued-sweep scheduler PID236262 STOPPED; its current batch14 worker terminated, no other session processes touched. Every screen from07:58 through08:00 must be treated as potentially contended/INVALID for formal comparison. No upload from continued-sweep. Defer GPU to existing fusedio/output-overlap owner; continuation does CPU implementation only until explicit shared-ledger handover. Latest externally verified Accepted is fusedio/top100265.316869ms at07:56:54, not266.237340.

Correction08:01: batch14 had already finished naturally before termination attempt (no process killed). Scheduler then terminated without starting another case. First7 cases/21rounds retained but all timing-invalid; correctness outputs valid. GPU fully released by continued-sweep.


2026-10-26 08:04 CST user explicitly instructed terminating the other Codex. Current thread01a1757c-3ea5-7373-b308-bb76e262b969 maps to PID233847 (started07:53:55); old fusedio/output owner thread01a1741f-0cb0-7d61-85cb-7f09cd3c060a maps to PID168376 (started01:32:32). SIGTERM sent only to168376. No benchmark/worker/Nsight children active at audit; historical sources/results/worktrees retained. Continuation resumes exclusive GPU0 after verifying termination and idle.

GPU0 handover2026-10-26 08:04 CST: fusedio48complete worker outputs plus boundary3/Nsight1 diagnostics finished, currentAccepted265.316869ms. Output-overlap now owns GPU exclusively for new BGR checks and10three-round reference screens. No concurrent GPU jobs and no large validation.

2026-10-26 08:06 CST GPU0 exclusively reclaimed by continued-sweep after user-directed termination of PID168376 and zero remaining worker/benchmark/Nsight processes. Combined72correctness checks passed (ring/tails/different dimensions, exact fusedIO/BGR/serialization).42registered variants ready for fresh3-round reference timings; all earlier21contended rounds excluded. Other parent worktrees preserved.

20261026-014417-fusedio **completed**08:04 CST:17cases/48complete worker outputs,1deployment failure retained/fixed; query150/100 failed AP. top100 **Accepted265.316869ms** at07:56:54 after network-timeout retry. Full profiling shows core208–212ms,exit58–64ms,GPUactivity128.181ms,74ms gaps; CPU supply priority. GPU handed to output-overlap. See experiments/20261026-014417-fusedio/notes.md.

2026-10-26 08:08:23 CST remote lifecycle verified **turn_aborted** for old thread01a1741f. Killing its CLI alone had not canceled daemon work: orphan output-overlap dispatcher243695 was terminated with its process group, then old remote turn was attached and interrupted via Esc. Its attach client exited. No model/scoring/Nsight processes remain; no shared daemon killed. All continued-sweep pre08:08:23 timings invalid, including second attempted control/top100/quarter. Existing official265.316869ms preserved. Fresh full42-case suite now starts from sourceffd89b6, no further production edits until completion.

2026-10-26 08:12 CST continued-sweep new full3-round threaded-top100 log **Accepted262.472328ms**, referenceAP50=0.7809 each, vs prior265.316869ms improvement1.0721%. Sourceffd89b6257539c46ee6c16ee3af3a54ad185457d; logSHA2563e42427a94d2b1829d9e8e1aef75fc27d0dc2b01755a9c0ec1bbfe99a2a499ee. Raw/receipt in /tmp/SuperShip-continued-20261026/output/20261026-075543-continued-sweep/20261026-081102-threaded-top100. timing parsed only; validation/hidden not measured. GPU remains exclusively reserved for remaining42-case suite and later paired confirmation.

2026-10-26 08:22 CST initial42-case screen completed:126complete reference worker runs;40variants passed all3AP gates, quarter/eighth rejected. End-control272.778741ms vs beginning290.072519ms shows temporal drift; require alternating confirmation. LatestAccepted threaded-balanced261.576759ms (log562640f9ac4d579a706468888c48319023241dc462877aa5ce0d34f5aca3872a); no hidden/large-validation claim. Proceed8previously registered combinations, production code remains exactlyffd89b6; then8pairs vs original accepted top100 baseline.

Correction08:22: final42-case result includes later Accepted threaded-pinned **260.302942ms**, superseding261.576759ms. LogSHA256=a618c4f17424e42358e84261ca0915accc8d6893225c106f0720be7993cd59ac; source=ffd89b6257539c46ee6c16ee3af3a54ad185457d; all3AP50=[0.7809, 0.7809, 0.7809]. Shared latest score must use this entry.

2026-10-26 08:25 CST 50-config screening complete:150complete workers;48passing variants,2precision failures. Best Accepted thread100-light258.409792ms,3rounds258.409792/256.334286/263.016448ms,AP50=0.7809all,logSHA2561d43c5c5c18874e823a2533f6702e48dbf5c98c274570b8d16d83f9b07ce65b1; sourcecda34913ed3cec8de577d151ee3a16984f46a5ed. Register8alternating pairs top100 vs thread100-light, AB/BA by pair, all rounds scored; no diagnostic one-round logs uploaded. Production source remains frozen, no GPU overlap.


Completion2026-10-26 08:28 CST —20261026-075543-continued-sweep **completed**.50registered configurations/150complete3-round reference workers;48passed,quarter/eighth decode failed precision and not uploaded. Sourcecda34913ed3cec8de577d151ee3a16984f46a5ed; selected thread100-light (top100+ordered threaded JSON+inference imports). LatestAccepted258.409792ms at08:23:38,all3referenceAP50=0.7809; validation/hidden=null.8alternating pairs276.219970→262.821248ms,4.8507% faster,8/8wins,p=0.0078125;all16outputsbyte-identical.82tests passed,assets/tool/source hashes checked. Old competing daemon turn actually interrupted08:08:23;10earlier contended cases retained timing-invalid; no history/worktree deleted. GPU0 released08:27. Complete results/reproduction: experiments/20261026-075543-continued-sweep/notes.md. No further GPU work pending.


## 20261026-083341-profile-thread100

- Owner Codex /root; branch `exp/profile-thread100-20261026`; status **completed**; updated 2026-10-26 08:37 CST. Parent latest candidate `1da325e5a7cf4fe3ff485855622dc22100fd848a`, production source `cda34913ed3cec8de577d151ee3a16984f46a5ed`; isolated worktree `/tmp/SuperShip-profile-thread100-20261026`.
- GPU0 RTX4090 reserved from08:34 after idle/process audit. Scope: latest thread100-light public200 reference baseline (3 full official-protocol runs), separate boundary/CPU-service/IO probes and Nsight timeline (2 runs). No inference changes, larger validation or competition submission. Record complete commands, exact source/config/assets and all outcomes; inherited Accepted258.409792ms stays unchanged.

Completion2026-10-26 08:37 CST —20261026-083341-profile-thread100 **completed**. Latest thread100-light official three rounds259.257667/251.140982/266.716015ms, median259.257667ms; all14formal/diagnostic outputs byte-identical, referenceAP50=0.7809. Normal core208–212ms,exit50–56ms; Nsight GPUactivity~128ms,64.5–83.5ms gaps, CPU8.4–8.7cores/10,physical read0bytes. CPUJPEG supply first,exit second,feature pack/small kernels third. One boundary core267ms outlier retained, cause unresolved. Validation/hidden=null, no model changes or competition upload; candidates/Accepted258.409792ms unchanged. GPU0 released08:35. [Full report](experiments/20261026-083341-profile-thread100/notes.md).


## 20261026-083914-main-fastest

- Owner Codex/root; branchmain; status **completed**; updated2026-10-26 08:40CST. Promote verified thread100-light source1da325e5a7cf4fe3ff485855622dc22100fd848a and its exact preset to defaultmain launcher before further optimization, per user instruction. Keep all historical versions and standard path. GPU0RTX4090 reserved08:40; no other GPU processes. Required preprocessing/ring/tail/import/launcher checks and three official full reference runs; no larger validation or competition upload.

Completion2026-10-26 08:41CST —20261026-083914-main-fastest completed: main default now selectedthread100-light implementation+portableconfigs/fastest.env; full three runs298.380190/261.305519/257.285773ms,median261.305519ms,allAP50=0.7809and byte-identical.96relevant checks passed (94existing+2new launcher cases). User workflow rule committed: sync verified fastest to main before each isolated optimization; preserve history and conservative path. No competition upload,Accepted258.409792ms unchanged. [Record](experiments/20261026-083914-main-fastest/notes.md).

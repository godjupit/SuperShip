# Accepted THP candidate: timing breakdown

ID 20261026-002932-profile-thp; Codex /root; completed. Parent 6a774ee970eef2fcb32c7a5f01086780700a1e7f, experiment20261026-000619-exit-rootcause. Target runtime is the accepted285.962649ms optimized candidate. New diagnostic files only, no production/model/timer changes.

GPU0 RTX4090 reserved from2026-10-26 00:29 CST after idle check. Same public200 reference images and weights as parent; checksums in parent data-checksums.json. Full model config in config.json; THP selected BEFORE child interpreter creation. Public input only accessed after READY in all workers. Formal baseline three rounds is separate from diagnostic line tracing/Nsight. No new competition submission: currentAccepted remains intact. Previous complete1030-image validation and32GiB hard-limit test apply to unchanged runtime; hidden AP50=null.

## What was measured

Runtime/model files and run.sh are byte-identical to parent6a774ee (and accepted runtime dff7a19). The official timer, scorer and validator hashes match the parent's manifests. Full parent source SHA is in initial notes above; exact execution commits and environment overrides are in every output case/command.json. Baseline/first probes executed1f8feb3; IO probes86b503b (full SHAs in runs.json and io-runs.json). No uncommitted inference patches. Same RTX4090, EPYC7402, CPU affinity0–9, PyTorch2.6.0+cu124/cuDNN90100, OpenCV4.11, Triton3.2, Nsight2024.2.3.38. Config requests THP before interpreter startup.

**Uninstrumented official three-round baseline:305.913433 /286.513029 /293.056173ms, median293.056173ms**, reference AP50=0.7809/0.7812/0.7809. This is a reproducibility check, not a new speedup or replacement submission. All14 reference outputs (baseline3, boundary3, line3, Nsight2, IO3) passed official validation and scoring:200 images each, reference AP50 range0.7809–0.7816. Original reference baseline0.7935 gives98% gate0.77763, margin>=0.00327. Validation AP50=0.9058 is **inherited from the unchanged parent's full1030-image run**, not measured again here; hidden AP50=null. Parent also passed32GiB hard cap, peak worker RSS2.025GiB. Diagnostic traces are not performance scores.

## 1. Additive full-process boundary view

These rows are actual measurements from the same run, not sums of independent medians:

| Round | Runtime.run ms | Exit tail ms | Diagnostic dump ms | Request/protocol misc ms | Full timer ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 |221.807443|72.964649|0.240869|0.211220|295.224181|
| 2 |231.625685|92.914912|0.315699|0.203560|325.059856|
| 3 |224.974340|64.000606|0.204200|0.203219|289.382365|

In the median-total boundary round1, Runtime.run is75.13% and the exit tail24.72%. Runtime.run includes input, transfers, graph replay, output waits, formatting, serialization and fsync. Initialization, weight loading and synthetic warmup remain outside official timing. The trace-free IO probe confirms stable core220.715–223.546ms but exit61.430/93.206/64.814ms: its slow round314.448ms comes primarily from the93.206ms tail. THP improved exit, but did not establish a fixed60–65ms tail; the earlier narrow range must not be treated as a guarantee.

## 2. Main-thread exclusive line view

Each row shows all three runs in order. These line intervals are exclusive on the main thread; child calls are included in their calling line. The GPU and background loaders run concurrently with these intervals.

| Stage | Three rounds ms |
| --- | --- |
| Waiting for image Future.result |176.328 /164.191 /183.182|
| Waiting for output GPU events incl final batch |17.689 /13.060 /13.264|
| Scheduling input jobs |5.335 /6.928 /5.782|
| Transfer submission on host |6.720 /7.336 /6.323|
| Graph replay submission on host |3.266 /3.953 /3.472|
| Snapshot collection |2.398 /2.188 /2.584|
| Bulk result formatting |8.827 /8.871 /8.866|
| JSON serialization |2.553 /2.563 /2.554|
| Write/flush |0.415 /0.291 /0.399|
| fsync |5.979 /7.068 /6.064|

Remaining time is metadata, stream/event bookkeeping, thread join and trace/context overhead. Full traced runtimes239.953/229.379/243.225ms; diagnostics dumping costs another7.260/8.408/8.897ms before exit and must not be mistaken for production runtime. The first analysis guard rejected a1.044ms difference between run scope and traced frame; explicit residual accounting fixed it. Frame intervals telescope exactly; outside-frame context/probe overhead0.762–1.044ms is preserved as its own category. **Do not read164–183ms Future wait as GPU idle or add it to GPU compute time.**

## 3. Decode/preprocess service and storage evidence

All200 load tasks span201.625–214.332ms of wall time. Loader-thread service summed across8 concurrent workers is1565.832–1676.416ms; sums overlap and are not additive wall time.

| Operation | Sum across200 calls, three rounds ms | Median per image ms |
| --- | --- | --- |
| cv2.imread: file access + reduced JPEG decode |1371.006 /1298.699 /1386.716|6.154 /5.909 /6.236|
| Resize |242.707 /226.533 /246.702|0.991 /0.989 /0.998|
| BGR→RGB |22.981 /22.530 /23.968|0.098 /0.092 /0.094|

imread accounts for~83% of loader service; some images reach20.5–20.7ms and can delay an ordered batch. These durations include scheduling/preemption. Three separate IO probe runs read58,390,963 logical bytes each, physical read_bytes=0 and major_faults=0; the measured input is warm-cache. Combined user+system CPU time1591.427/1599.998/1626.867ms over222.634/220.715/223.546ms core wall time gives7.15/7.25/7.28 average CPU cores. Current input limitation is decoding/preprocessing supply under this workload, not physical disk bandwidth. This does not predict a cold filesystem or4300 hidden images. OpenCV already uses libjpeg-turbo3.0.3-70 and AVX2/AVX512 dispatch; merely suggesting installing libjpeg-turbo would repeat an existing capability.

## 4. Independent GPU timeline view

| Nsight run | Kernel sum ms | GPU activity union ms | First-to-last GPU span ms | No-GPU-activity gaps ms | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 |137.520|147.442|185.398|37.956|79.53%|
| 2 |142.803|153.079|198.755|45.676|77.02%|

Union includes kernels and transfers; coverage is **timeline coverage, not SM utilization**. CPU preprocessing, graph compute and copy engines overlap. Do not add these durations to the main-thread table. Each run has25 graph launches,21050 kernels (842 per batch),14248–14746 kernels<5us. CUDA Graph removes host launch repetition but does not fuse those kernels.

H2D=9.696/10.041ms for177,563,200bytes; D2H=0.0878/0.0892ms for1,440,000bytes (read exact second-round values in summary.json if rounded differently). Transfers are not the dominant current bottleneck, especially D2H. Top exact kernel families (first run): FP16 conversion10.527ms/2450calls; one CUTLASS GEMM family9.154ms; Triton feature pack8.895ms/350calls; FP32 add8.884ms/1525calls; FP32 mul8.266ms/975calls; FP32 NHWC maxpool4.790ms/25calls. **The already-fused deformable attention is only1.703ms/75calls**, so it is no longer the first GPU target. Kernels are named families, not disjoint model-module timing. No hardware bandwidth/SM counters were collected, so no claim of bandwidth or compute saturation.

## Bottleneck priorities

1. **CPU image supply**: reduce decode/preprocess cost and batch head-of-line waiting; measure decoder service and thread/batch scheduling first. Existing GPU activity gaps38–46ms are a visible opportunity, not a guaranteed equal end-to-end gain. Avoid blindly increasing threads or caching evaluation-derived inputs before READY.
2. **Remaining exit cost and variance**: typical61–73ms, observed93ms; already22–29% of fast full runs and explains a slow IO probe despite stable core work. Any follow-up should inspect THP coverage and residual host-page/driver teardown per run; cudaDeviceReset and empty-cache approaches were already rejected in parent. Do not propose them again as untested fixes.
3. **GPU dtype/layout/elementwise traffic**: conversion + feature pack + FP32 add/mul are measurable families; investigate eliminating promotion/casts or fusing adjacent operations. Candidate code locations include engine/backbone/hgnetv2.py LearnableAffineBlock (float32 scale/bias) and engine/misc/feature_pack_triton.py. This is a hypothesis about attribution, not proof all casts originate there. Earlier affine-half experiments already exist and need same-group comparison, not an assumed win. Fused attention1.7ms is lower priority.
4. **Serial output tail**: bulk formatting~8.9ms, serialization~2.6ms, fsync6–7ms. Optimizing JSON alone has a small ceiling; fsync must remain in the counted protocol. Keep completeness/finite checks and full process-group termination.

No inference changes were made or promoted. Current recommended and conservative candidates, Accepted0.285962649s and unknown official hidden best remain unchanged. No diagnostic log was submitted to the competition system.

## Reproduction, artifacts and checks

In a fresh worktree at this diagnostic branch with matching public assets and dependencies:

```bash
/home/ubuntu/.cache/supership-venv/bin/python -u experiments/20261026-002932-profile-thp/run.py
/home/ubuntu/.cache/supership-venv/bin/python -u experiments/20261026-002932-profile-thp/run_io.py
/home/ubuntu/.cache/supership-venv/bin/python experiments/20261026-002932-profile-thp/analyze.py
```

Drivers reject existing case/output directories; choose a fresh worktree/output location rather than overwriting historical results. Commands, effective overrides and source commits are in each case/command.json; source/assets/raw artifact hashes in checksums.json. Raw predictions, full Nsight traces/SQLite and logs are **local only** at `/home/ubuntu/SuperShip-main 2/output/20261026-002932-profile-thp/` and original `/tmp/SuperShip-time-20261026/output/20261026-002932-profile-thp/`; not in Git. Off-machine reproduction needs public data, weights and rerunning. Diagnostic source/summary and compact chart are tracked. Matplotlib was absent from the model environment, so plotting dependencies were isolated under/tmp/supership-profile-plot-deps; this does not alter inference dependencies.

Checks: all14 scored outputs200 images each; line-interval conservation and nonnegative residuals; source diff against parent confirms engine/supership/run.sh unchanged; official tool/data/weight/reference-image checksums match parent; Python compilation and git diff --check. No additional model tests needed because production code is unchanged. GPU0 released at2026-10-26 00:37 CST after verifying idle. Parent32GiB memory result still applies to the inference runtime; profiler/tool overhead was not used to claim a new memory benchmark.

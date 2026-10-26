# Fused input, feature and detection-output experiments

ID20261026-014417-fusedio; Codex /root; running (CPU implementation only). Parent509fe983b6864cbcbda1b8f52641c942dd11328a; parents20261026-013427-validation-sweep and GPU hotspot diagnostic20261026-002932-profile-thp. Isolated branch exp/fusedio-20261026, /tmp/SuperShip-fusedio-20261026. No GPU tasks until configwide experiment releases GPU.

Registered independent hypotheses: fused uint8→normalized channels-last FP16 input, exact float32 multiply then half-store; fused top-k detection gather/box-conversion/scaling/output packing; segment-oriented feature packing and block-size tuning; affine block tuning; reduced inference-only registration imports; query proposal count and output top-k screening after strict checkpoint load. All opt-in; model weights strictly loaded; no changes to official timer/scorer/validator, no preREADY evaluation access, all images/outputs/exit included. Synthetic exact-output/CUDA Graph replay checks before three-round200-image reference screening and AP gate0.77763. No large validation jobs, validation/hidden results for changed models=null. Timing-only accepted scores do not establish hidden accuracy. All failed trials retained, no score regression uploads.

Registered14 initial kernel/model hypotheses in plan.json. half-w10 is control. fused-io combines normalize and postprocess parents; pack-segment1024 combines segmented mapping and block1024. Light imports reuses only optional registration changes from f92e90b supply branch (no decode/resize code). Validation/hidden null for this experiment; no claim of bitwise equivalence for query/top-k reduction. Full exact tests and existing synthetic tail/ring tests will execute after GPU handover.

Register GPU resize512 hypothesis parent f92e90b supply experiment (original variant had validation0.9001 but not fused affine): upload at512 then bilinear/round/normalize to544 in counted graph, preserving full input access afterREADY. This changes preprocessing rounding, so fresh reference AP required; no inherited validation claim for combination. When decoded source already matches upload dimensions, skip identity resize (same pixels). Also register model-deploy1 (existing checkpoint deployment conversion), all else unchanged. No fused normalization+resize combination allowed yet.

2026-10-26 01:50 CST GPU handover: configwide17-case suite complete,51worker outputs,2reference precision-failed configurations (decoder2,score0.075) not uploaded; latestAccepted266.237340ms (cudnn-fixed), timing-only. GPU0 verified idle and reserved now for fusedio tests/screens. All16 fusedio configs inherit new CUDNN_BENCHMARK=0 parent from configwide/cudnn-fixed; baseline floor refreshed266.237340ms. No larger validation jobs.

Initial targeted test run50passed/1failed: all fused IO/segmented pack exact arithmetic, changed-input graph replay, affine and synthetic async-tail tests passed. Light-import scope test exposed two missed existing parent changes (lazy TensorBoard import and optional profiler import); copied those exact opt-in changes, preserving default training registrations. No invalid timing generated, tests-initial.log retained. Rerun only affected import/launcher checks after fix.

Affected checks after import fix10passed. Ready for16variants/48official200-image runs with updated floor266.237340ms; GPU0 remains exclusive. Kernel/ring numerical checks50passed before import fix (kernel source unchanged). No extra large-data validation.

At0155 top100 completed259.766766/265.316869/275.865837ms, AP50=0.7809 each. Initial official upload timed out90s; driver stopped before last3variants, no receipt claimed. Resumed with GPU idle at2026-10-26 07:56 CST; same intact log/hash rechecked, bounded retry **Accepted265.316869ms at07:56:54**. No slower log submitted during unknown interval. Failed request metadata retained. Upload wrapper now owns/kills its process group on30s timeout and conservatively protects the attempted faster score, so an unknown acceptance cannot be overwritten by a slower candidate. Continue only unrun fused-io,gpu-resize512,model-deploy configurations, no rerun of first13cases.

Remaining resumed screens: fused-io313.094453ms and gpu-resize512296.951878ms/AP50=0.7823 failed to beat protected265.316869ms. model-deploy failed beforeREADY because deploy() creates fresh modules in training mode and subsequent strict Conv-BN fusion rejects them. Fix by reapplying model.eval() immediately after deployment; original failed log retained. Register one new model-deploy retry, then transfer GPU to output-overlap; no hidden/validation claims. Current host load/clock noted because resumed timings span a later wall-clock interval.

At08:01 all16initial hypotheses plus deployed retry completed; latestAccepted265.316869ms. User authorizes broad performance diagnostics. Register current top1003-round boundary/IO probe and one inference-only Nsight trace to decide next direction. Diagnostic timings not uploaded;200inputs/normal exits preserved. CPU/GPU/loader intervals overlap; do not sum them. GPU0 remains exclusive, output-overlap screens wait.

## Completed2026-10-26 08:04 CST

17cases:16complete3-round logs(48worker outputs),1initial deployment failure beforeREADY retained; reduced query150/100 failed referenceAP. New top100 median265.316869ms was accepted after bounded retry. No full validation or hidden tests; validation/hidden=null for all new paths. Source/parameters/commands/individual scores in results.json, receipt and all hashes retained. GPU0 handed to output-overlap08:04.

| Variant | 3 rounds ms | Median ms | Reference AP50 | Outcome |
|---|---|---:|---|---|
|control|264.635/269.878/270.233|269.878|0.7809,0.7809,0.7809|completed|
|normalize|272.409/272.701/285.032|272.701|0.7809,0.7809,0.7809|completed|
|postprocess|271.664/274.082/276.054|274.082|0.7809,0.7809,0.7809|completed|
|pack-segment|273.349/272.527/271.021|272.527|0.7809,0.7809,0.7809|completed|
|pack-block1024|276.257/278.839/278.240|278.240|0.7809,0.7809,0.7809|completed|
|pack-segment1024|272.105/283.467/267.872|272.105|0.7809,0.7809,0.7809|completed|
|affine-block1024|284.970/269.960/272.469|272.469|0.7809,0.7809,0.7809|completed|
|light-imports|268.686/292.004/278.971|278.971|0.7809,0.7809,0.7809|completed|
|queries200|268.273/272.378/269.422|269.422|0.7813,0.7813,0.7813|completed|
|queries150|269.357/297.165/258.735|269.357|0.7747,0.7747,0.7747|precision_failed|
|queries100|262.867/272.790/258.347|262.867|0.7717,0.7717,0.7717|precision_failed|
|top200|275.772/273.944/268.107|273.944|0.7809,0.7809,0.7809|completed|
|top100|259.767/265.317/275.866|265.317|0.7809,0.7809,0.7809|completed|
|fused-io|304.255/327.658/313.094|313.094|0.7809,0.7809,0.7809|completed|
|gpu-resize512|296.952/312.482/269.989|296.952|0.7823,0.7823,0.7823|completed|
|model-deploy|not timed|—|—|runtime failed|
|model-deploy|288.822/310.753/340.878|310.753|0.782,0.782,0.782|completed|

Full current-top100 process probes: core207.578/211.727/208.194ms; exit63.648/57.574/57.586ms; totals271.808/269.910/266.406ms. CPU1748–1777ms across~210ms core (~8.4cores), physical reads0 each. Nsight kernel118.518ms/18900calls; activity128.181ms over201.923ms span leaves73.742ms idle intervals,63.48% timeline coverage (not SM utilization). Top pack7.893ms; H2D9.467ms, D2H0.048ms. Input supply is still the first target; blindly adding GPU fusions cannot reclaim all existing CPU gaps. Profiling outputs all passed AP50=0.7809; diagnostic logs never uploaded. This supports moving CPU color conversion and output formatting off the critical path.

Checks:50targeted numerical/ring tests passed and light-import scope failure fixed with10affected checks passing; full case output checks and source compile/diff checks passed. Original failed tests/upload timeout/deployment failure all retained. No official timer/scorer modifications. Source variants executed0cd93cb12821da085172ca470c0e71e836de7016,41e109174383aa894e2d81c25831d853b4fbe4e3,ea7ab0c and4438b94 (full SHAs per result). Main stores reports only; optimized runtime lives on exp/fusedio-20261026. Raw artifacts local-only output/20261026-014417-fusedio; main output link preserves access.

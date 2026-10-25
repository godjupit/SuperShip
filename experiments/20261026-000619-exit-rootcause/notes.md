# Exit latency investigation

ID 20261026-000619-exit-rootcause; owner Codex /root; completed; GPU0 RTX4090 reserved at 2026-10-26 00:06 CST.

Base main 90bcc6165f6d65b5f6a16bb1298af83465a54d04 plus optimized runtime imported verbatim from 9a195679dbea2d02ff93815c8bacaf82a954646e (import commit ab4f167). Parent experiments 20261025-174717-profile-current and 20261025-180401-bottleneck-sweep. Current main timer, scorer, submission validator and competition document retained: NEW comparison group. Only exit strategy will differ within this group. No hidden evaluation. The user subsequently authorized competition submission; receipt recorded below.

Config in config.json. Public data symlink to original checkout; outputs under output/20261026-000619-exit-rootcause/. Native cache allocator; all evaluation data access after READY; complete output fsync and process-group termination included.

## Root-cause evidence and rejected hypotheses

- `trace-baseline`: strace exit_group at 1792944471.314102, last thread exited at 1792944471.413601 (99.499ms); leader exit at .413653. Confirms time is inside OS exit, not Python cleanup or timer polling. Tracing affects runtime; diagnostic scores are not promotion results.
- `sample-baseline`: /proc stack sampled NVIDIA nv_free_system_pages and set_pages_array_wb during the tail, but this alone did NOT establish the dominant component.
- `kernel-pairs-v2`: paired entry/return kprobes scoped to this worker's threads: exit_mmap=77.373ms, unmap_vmas=75.993ms, free_pgtables=0.829ms. Largest unmap_single_vma was the normal process heap, 22.540ms; another anonymous 225MB mapping took12.245ms. Individual unmap ranges matched ready.smaps. Approximately1.3GB resident anonymous host memory, all 4KiB pages (AnonHugePages=0). Thus host anonymous memory teardown is the dominant measured component; NVIDIA file/driver cleanup remains in the residual tail.
- `kernel-pairs-thp`: with glibc.malloc.hugetlb=1: exit_mmap=60.517ms, unmap_vmas=57.071ms. These tracing runs are diagnostic, not formal timing; do not subtract instrumentation from the timer.
- THP diagnostic three rounds: full 304.402 / 291.378 / 284.392ms; tail from pre-exit marker to parent wait 64.502 / 63.511 / 59.559ms. GLIBC_TUNABLES selected before Python starts; no machine sysfs settings changed and no reserved HugeTLB pool needed. Example READY snapshot1,062,912KiB AnonHugePages, RSS2,055,856KiB versus baseline RSS1,843,608KiB. Memory overhead is a tradeoff, especially on smaller-memory machines.
- `trimmed`: empty_cache before READY did not change reserved GPU memory (616,562,688 bytes), no useful tail reduction. `host-register`: switching pinned allocator did not help. `reset`: explicit cudaDeviceReset itself cost84.204–105.021ms and full median434.566ms, rejected. `readonly`: discarding clean file-backed read-only initialization pages gave no clear benefit, not shipped. `heap-trim`: malloc_trim released only about3MiB, no meaningful improvement. `thp-threshold`: adding fixed128KiB mmap threshold slowed the inference core to~263ms and full median327.436ms, rejected; keep THP alone.
- `kernel-baseline` abandoned before READY: function_graph is unavailable in per-instance tracers on this kernel; stopped only our own waiting diagnostic worker. `kernel-pairs` failed before READY because pathlib open('a') supplied O_CREAT to tracefs; fixed by opening the existing control file via os.open. Both failed logs retained, no timing score assigned. Temporary tracing instances/probes are scoped to this worker and removed after collection.

## Implementation

`run.sh` requests glibc transparent huge pages before exec on Linux by default. `HOST_THP=0` disables this request; explicit caller glibc.malloc.hugetlb settings take precedence, unrelated GLIBC_TUNABLES preserved. No cleanup is moved after counted termination; no worker persists, all output fsync and full process-group exit remain timed. Unsupported glibc/kernel configurations may see no benefit. Runtime/model/precision untouched by the fix; optimized runtime imports are only the experiment's baseline.

Allocator semantics: [GNU C Library manual](https://www.gnu.org/s/libc/manual/html_node/Memory-Allocation-Tunables.html), glibc.malloc.hugetlb=1 requests MADV_HUGEPAGE. Kernel/proc observations above, not the manual, establish this machine's actual bottleneck.

Checks so far:60 passed (worker launcher, preprocessing, async ring/tail, scoring and official benchmark). Official timer/scorer/validator are unchanged. Formal six AB/BA pairs plus complete1030-image validation for both configurations are recorded by confirm.py; no diagnostic worker or tracer in these formal runs.

## Formal comparison, accuracy and promotion

Official current-protocol full runs, source `65c42ad` (full SHA in paired6/results.json), same RTX4090, inputs and configuration; only HOST_THP0/1 changes. No tracer or boundary probe in the scored runs. AB/BA order alternates:

| Pair | Order | Control ms | THP ms | Control reference AP50 | THP reference AP50 |
| --- | --- | ---: | ---: | ---: | ---: |
| 1 | AB | 355.091292 | 339.884475 | 0.7809 | 0.7807 |
| 2 | BA | 357.431784 | 287.439702 | 0.7812 | 0.7812 |
| 3 | AB | 324.594184 | 291.106935 | 0.7809 | 0.7812 |
| 4 | BA | 365.611060 | 286.968734 | 0.7811 | 0.7812 |
| 5 | AB | 364.723148 | 287.790878 | 0.7812 | 0.7809 |
| 6 | BA | 325.873058 | 327.692089 | 0.7810 | 0.7816 |

Control median **356.261538ms**, THP median **289.4489065ms**, reduction **18.7538%**; candidate wins **5/6** pairs. Pair6 regressed1.819031ms, retained. The full improvement includes runtime differences as well as exit; do not attribute the entire66.8ms delta to exit or treat diagnostic stage timings as additive.

Complete1030-image validation (tail6) control **1.122407962s / AP50=0.9056**, THP **1.036243602s / AP50=0.9058**. Single validation timings are not a formal three-round speed claim. Minor accuracy fluctuations reflect the existing mixed-precision/cuDNN path; allocator change does not intentionally change numerics. Formal reference AP50 range control0.7809–0.7812, THP0.7807–0.7816. Conservative reference gate uses historical original baseline0.7935, 98% threshold0.77763, worst0.7807 gives retention98.3869%, margin0.00307; validation historical original baseline0.9170, threshold0.89866, candidate0.9058 gives98.7786%, margin0.00714. Actual same-group optimized control0.9056 is also retained above98%. Hidden AP50=null.

Fresh independent three-round submission, source `dff7a19` (full SHA in final-three/command.json): **284.952062 / 294.860144 / 285.962649ms**, median **285.962649ms**, AP50 **0.7812 / 0.7816 / 0.7809**. Log is intact stdout+stderr from one unchanged official timer invocation; no concatenation, selection of individual rounds, or changes after generation. Score commands, prediction hashes, source, full config and original log SHA recorded. This current-protocol group is distinct from historical302.713ms logs; no cross-date speedup claimed.

## 32GB host memory constraint

Both control and candidate completed all1030 validation images inside transient systemd cgroups with **memory.max=34359738368bytes (32GiB), memory.swap.max=0**. Timer, initialization, model loading, warmup, worker descendants and scoring were inside the limit. Both memory.events max/oom/oom_kill=0. GNU time peak worker RSS: control **1,909,236KiB (1.821GiB)**, THP **2,123,076KiB (2.025GiB)**, +**208.8MiB**. This is below either32GB decimal or32GiB. Cgroup charge peaks sampled every10ms: control1,468,452,864bytes, THP1,689,538,560bytes; sampled values are NOT exact peak RSS, and shared file-cache accounting differs. GNU time supplies peak worker RSS; successful execution under the hard cap proves the bound for these runs. Hidden4300 images were not available/tested.

Initial memory32-candidate run completed inference/scoring but its telemetry failed because Linux5.15 lacks memory.peak; raw outputs retained. A new unique candidate-v2 run used sampled memory.current plus GNU time, succeeded. No global memory or THP configuration changed; transient services collected automatically.

## Checks and system submission

**101 passed,1 skipped** with `python -m pytest -q tests` (optional TensorRT engine missing); launcher tests cover both pipelines, opt-out, unrelated tunables and caller overrides. Initial bare pytest traversed archived branch snapshots, producing47 collection/import-name collisions; retained in full-tests.log, corrected by explicitly targeting project tests. Shell syntax, Python compilation and git diff --check also pass. No scorer/timer/validator modifications.

User explicitly requested system submission in this session. Account **ruc2602**, task **SUPERSHIP**. Local official submit.sh matched freshly downloaded official script SHA256 **b6dc5a8cf976fab3e9e0cc9c290521e63ab353fcc263612875e4dc56b9419cdd**. Log SHA256 **39b6f8d6c7ee31d09d0423e724cfd4a27c76a508cf1ebde31169a17bc7ea1800** checked immediately before both requests. Dry validation succeeded at2026-10-26 00:24:31 CST; **Submission Accepted** at **00:24:37 CST**, performance **0.285962649s**, **timing parsed only**. Sanitized receipt in submission-receipt.txt; no credential contents saved in Git. No old log was resubmitted. Official hidden-set best remains unknown.

## Reproduction and artifacts

For the complete optimized candidate, use branch `exp/exit-rootcause-20261026` at source `dff7a19` or the final documentation descendant. Prepare public data/weights matching data-checksums.json; Python dependencies in environment.json. In a fresh worktree with no prior final-three outputs:

```bash
/home/ubuntu/.cache/supership-venv/bin/python experiments/20261026-000619-exit-rootcause/finalize.py
```

For AB/BA comparison use `confirm.py new-unique-name --pairs 6 --validation`. For the common launcher fix alone, main receives run.sh and its launcher tests; optimized model/kernel changes remain on the isolated experiment branch. Main's default standard pipeline is unchanged. `HOST_THP=0 bash run.sh --worker` opts out. Explicit GLIBC_TUNABLES glibc.malloc.hugetlb takes precedence. No guarantee of benefit on other libc/kernel/GPU combinations.

Raw artifacts retained primarily at `/home/ubuntu/SuperShip-main 2/output/20261026-000619-exit-rootcause/`, also original worktree output; only this machine, not Git. artifacts-sha256.json indexes all raw logs, predictions and traces; off-machine reproduction needs public assets and rerunning. Worktree/branch history preserved.

Final handoff: GPU0 released at2026-10-26 00:26 CST after idle verification. Main launcher checks8 passed; experiment project suite101 passed/1 skipped. Root checkout user-owned `.qoder/` left untouched and untracked. Git commits/pushes recorded in the task response; experiment history is on exp/exit-rootcause-20261026.

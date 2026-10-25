# Exit latency investigation

ID 20261026-000619-exit-rootcause; owner Codex /root; running; GPU0 RTX4090 reserved at 2026-10-26 00:06 CST.

Base main 90bcc6165f6d65b5f6a16bb1298af83465a54d04 plus optimized runtime imported verbatim from 9a195679dbea2d02ff93815c8bacaf82a954646e (import commit ab4f167). Parent experiments 20261025-174717-profile-current and 20261025-180401-bottleneck-sweep. Current main timer, scorer, submission validator and competition document retained: NEW comparison group. Only exit strategy will differ within this group. No hidden test or competition submission.

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

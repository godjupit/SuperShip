# Continued independent optimization screen


## 20261026-075543-continued-sweep

- Owner Codex current /root continuation; branch `exp/continued-sweep-20261026`; status **running**; updated 2026-10-26 07:58 CST. Parent `0cd93cb12821da085172ca470c0e71e836de7016`; isolated worktree `/tmp/SuperShip-continued-20261026`.
- Fresh process audit found no benchmark/worker/scoring processes and idle GPU0; fusedio last raw result at01:55 (6 hours old). Reserve GPU0 from07:58 for this continuation; output-overlap has CPU-only reservation and must wait for handover. Other worktree modifications left untouched.
- New hypotheses: pinned reusable image-size transfers, CUDA event reuse, batch7/9/14 tails, smaller/larger model geometry under reference accuracy gate, intermediate query counts, top-k output sizing, GLIBC mmap/arena and torch/OMP thread settings. Each variant registered in plan.json before running, unchanged official timer/scorer, all200 inputs afterREADY, complete3-round timing, no larger validation. Current floor266.237340ms; only fresh passing improvements eligible for competition upload.

Validation AP50=null; hidden AP50=null for all new variants. All data/weights local only, source and tool hashes recorded before execution. Source parent reference AP50 baseline0.7935, gate0.77763. No confidence in small speed changes without paired follow-up.

Registered25 variants before execution; plan.json and variants/ contain all overrides. Input512 rejected historically, so no repeated512 model trial. gpu-resize512 keeps544 model geometry and changes resampling. Query and top-k changes require new AP gates. CPU-only modifications and all configurations committed before any timing.


2026-10-26 08:00 CST continuation resource conflict: another independent live Codex session resumed fusedio at07:56 and has a model-deploy benchmark active at08:00. Continued-sweep scheduler PID236262 STOPPED; its current batch14 worker terminated, no other session processes touched. Every screen from07:58 through08:00 must be treated as potentially contended/INVALID for formal comparison. No upload from continued-sweep. Defer GPU to existing fusedio/output-overlap owner; continuation does CPU implementation only until explicit shared-ledger handover. Latest externally verified Accepted is fusedio/top100265.316869ms at07:56:54, not266.237340.

Correction08:01: batch14 had already finished naturally before termination attempt (no process killed). Scheduler then terminated without starting another case. First7 cases/21rounds retained but all timing-invalid; correctness outputs valid. GPU fully released by continued-sweep.

Stage2 registered before execution08:03: file-size scheduling small/large/balanced (all stat/access afterREADY, complete image coverage and deterministic ordering); quarter/eighth JPEG decode with original-coordinate dimension checks (new precision, cannot inherit validation); top100 combinations of independent pinned/event/scheduling parents. Apply model.eval() after deploy, matching the fix discovered by the other fusedio owner. No GPU tests during existing owner reservation.

# Completed:50-direction continuation

Experiment `20261026-075543-continued-sweep`; Codex thread01a1757c-3ea5-7373-b308-bb76e262b969; branch `exp/continued-sweep-20261026`; status **completed**, updated2026-10-26 08:28 CST. GPU0 RTX4090 released08:27 after idle verification. Worktree `/tmp/SuperShip-continued-20261026`.

Best complete three-round log **258.409792ms Accepted2026-10-26 08:23:38**, timing parsed only. Variant `thread100-light`: parent top100 + ordered threaded JSON + inference-only imports; batch8,544input,10loaders,depth3,FP16/CUDA Graph,full3decoderlayers,halfJPEGdecode,score0.05,CUDNN_BENCHMARK=0 and all earlier parent fusion/THP flags. Full effective config: `variants/thread100-light.json`. Source **cda34913ed3cec8de577d151ee3a16984f46a5ed**; production bytes equal frozen screening sourceffd89b6257539c46ee6c16ee3af3a54ad185457d. Asset/tool/source hashes accompany this record.

Three rounds258.409792 /256.334286 /263.016448ms; median258.409792ms. Prior Accepted265.316869ms→258.409792ms is a2.6033% score-log improvement. Reference AP50=0.7809 each; actual reference baseline0.7935,ratio0.9841210, gate0.77763,absolute margin0.00327. **Validation AP50=null; hidden AP50=null** for this new package. No large validation job was run. Preserve earlier640/fullJPEG conservative path(validation0.9167); hidden best remains unknown.

50configurations/150complete reference outputs:48passed all3AP gates; JPEGquarter0.7346 and eighth0.4649 failed, never uploaded. All original times, including regressions, in [results.md](results.md) and [results.json](results.json). Initial10contended configurations/30runs retained as timing-invalid and excluded from promotion. The other daemon turn was explicitly interrupted at08:08:23 on user instruction; no other session history, worktree or results deleted. Old output-overlap implementation parents b6474af/58a08bb are preserved and incorporated here.

Independent8alternating pairs: original top100 baseline median276.219969ms vs new package262.821248ms;4.8507% reduction;8/8wins, p=0.0078125. All16result files byte-identical(SHA2564185ed612afb8234afae8e31eb43bafd0b68ef32c124d0d510d2da745f29100c). These one-run diagnostics were not uploaded or concatenated; protected Accepted258.409792ms remains unchanged. Starting/ending control medians290.072519/272.778741ms show why the sequential grid alone is not a causal proof.

Checks:72tests for numeric exactness, graph replay, mixed image dimensions, async/ring/tails, JPEG reductions, order coverage and threaded serialization;10inference-import/launcher tests; **82passed**. Official timer/scorer and all200reference images/metadata/annotations/weights verified against initial manifest; Python compilation and git diff checks passed. No fresh32GiB hard-cap measurement; no material model-size expansion in this package.

Raw complete logs, predictions, commands, metric files and receipts are **local only** at `/tmp/SuperShip-continued-20261026/output/20261026-075543-continued-sweep/`, linked from main's `output/20261026-075543-continued-sweep/`. Best log `20261026-082325-thread100-light/supership.out`, SHA2561d43c5c5c18874e823a2533f6702e48dbf5c98c274570b8d16d83f9b07ce65b1. Every raw-file checksum retained; Git carries compact records/configs, not predictions or engines. Off-machine reproduction needs public reference assets and baseline weights matching manifest.json, matching software versions and GPU; local paths alone are not portable artifacts.

Reproduce by checking out sourcecda34913ed3cec8de577d151ee3a16984f46a5ed into an isolated worktree, supplying assets at `data/SuperShip` and `weights/baseline.pth`, then running from that worktree (adjust PYTHON_BIN/TRITON_CACHE_DIR in the explicit config on another host):

```bash
/home/ubuntu/.cache/supership-venv/bin/python experiments/20261026-075543-continued-sweep/run_case.py thread100-light --runs 3 --combined-log --split reference --name NEW_UNIQUE_CASE
```

This does not submit; only screen.py --submit invokes authorized formal uploads. Recreate paired confirmation with `paired.py top100 thread100-light --pairs 8`. Keep the faster complete log and conservative path; no remaining GPU experiment is running. Future work: profile the confirmed package and test broader data only if authorized; do not infer hidden precision from public200.

---

The chronological registration and resource-conflict history below is retained unchanged.

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


2026-10-26 08:04 CST user explicitly instructed terminating the other Codex. Current thread01a1757c-3ea5-7373-b308-bb76e262b969 maps to PID233847 (started07:53:55); old fusedio/output owner thread01a1741f-0cb0-7d61-85cb-7f09cd3c060a maps to PID168376 (started01:32:32). SIGTERM sent only to168376. No benchmark/worker/Nsight children active at audit; historical sources/results/worktrees retained. Continuation resumes exclusive GPU0 after verifying termination and idle.

08:05 takeover: incorporate ordered threaded serialization from parent b6474af and correctness tests7b7ecf6 (other session stopped by explicit user instruction). Six independent/combination variants registered, parents listed by overrides. Full39-case plan now committed before exclusive retiming. No source mutation during suite. Reuse all old artifacts, never overwrite.

Final stage before exclusive screen: integrate GPU BGR normalization parent58a08bb with three registered variants; total42variants. Existing earlier output-overlap handover text predates explicit user termination; this continuation now owns GPU0, other stopped worktrees remain untouched.

2026-10-26 08:06 CST GPU0 exclusively reclaimed by continued-sweep after user-directed termination of PID168376 and zero remaining worker/benchmark/Nsight processes. Combined72correctness checks passed (ring/tails/different dimensions, exact fusedIO/BGR/serialization).42registered variants ready for fresh3-round reference timings; all earlier21contended rounds excluded. Other parent worktrees preserved.

2026-10-26 08:08:23 CST remote lifecycle verified **turn_aborted** for old thread01a1741f. Killing its CLI alone had not canceled daemon work: orphan output-overlap dispatcher243695 was terminated with its process group, then old remote turn was attached and interrupted via Esc. Its attach client exited. No model/scoring/Nsight processes remain; no shared daemon killed. All continued-sweep pre08:08:23 timings invalid, including second attempted control/top100/quarter. Existing official265.316869ms preserved. Fresh full42-case suite now starts from sourceffd89b6, no further production edits until completion.

2026-10-26 08:12 CST continued-sweep new full3-round threaded-top100 log **Accepted262.472328ms**, referenceAP50=0.7809 each, vs prior265.316869ms improvement1.0721%. Sourceffd89b6257539c46ee6c16ee3af3a54ad185457d; logSHA2563e42427a94d2b1829d9e8e1aef75fc27d0dc2b01755a9c0ec1bbfe99a2a499ee. Raw/receipt in /tmp/SuperShip-continued-20261026/output/20261026-075543-continued-sweep/20261026-081102-threaded-top100. timing parsed only; validation/hidden not measured. GPU remains exclusively reserved for remaining42-case suite and later paired confirmation.

08:19 stage3 register8additional combinations (total50) before execution: threaded-top100 parent plus workers8/9,depth4,light imports,GPU resize512,fusedIO,arena1/2. Parents explicitly threaded-top100 and corresponding prior independent trial. These cover remaining output-overlap queue hypotheses; plan/config changes do not modify the still-running42-case production sourceffd89b6. Commit configurations after initial42finish, before running these8. Then8alternating pairs for the selected best candidate; all pairs retained, no one-run uploads.

2026-10-26 08:22 CST initial42-case screen completed:126complete reference worker runs;40variants passed all3AP gates, quarter/eighth rejected. End-control272.778741ms vs beginning290.072519ms shows temporal drift; require alternating confirmation. LatestAccepted threaded-balanced261.576759ms (log562640f9ac4d579a706468888c48319023241dc462877aa5ce0d34f5aca3872a); no hidden/large-validation claim. Proceed8previously registered combinations, production code remains exactlyffd89b6; then8pairs vs original accepted top100 baseline.

Correction08:22: final42-case result includes later Accepted threaded-pinned **260.302942ms**, superseding261.576759ms. LogSHA256=a618c4f17424e42358e84261ca0915accc8d6893225c106f0720be7993cd59ac; source=ffd89b6257539c46ee6c16ee3af3a54ad185457d; all3AP50=[0.7809, 0.7809, 0.7809]. Shared latest score must use this entry.

2026-10-26 08:25 CST 50-config screening complete:150complete workers;48passing variants,2precision failures. Best Accepted thread100-light258.409792ms,3rounds258.409792/256.334286/263.016448ms,AP50=0.7809all,logSHA2561d43c5c5c18874e823a2533f6702e48dbf5c98c274570b8d16d83f9b07ce65b1; sourcecda34913ed3cec8de577d151ee3a16984f46a5ed. Register8alternating pairs top100 vs thread100-light, AB/BA by pair, all rounds scored; no diagnostic one-round logs uploaded. Production source remains frozen, no GPU overlap.

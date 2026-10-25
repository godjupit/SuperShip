# Broad reference-only configuration search

ID20261026-014213-configwide; owner Codex /root; running. Parent509fe983b6864cbcbda1b8f52641c942dd11328a, parent experiment20261026-013427-validation-sweep. GPU0 RTX4090 reserved2026-10-26 01:42 CST after idle/process checks. Isolated branch exp/configwide-20261026, worktree /tmp/SuperShip-configwide-20261026.

User authorizes sustained optimization,200-image testing and immediate improved submissions; no1030-image validation jobs. Initial Accepted275.737156ms. Each registered variant changes one parameter from half-w10 (batch8,workers10,depth3). plan.json and variant configs enumerate17 hypotheses spanning batch sizing/tails, CPU workers, ring depth, decoder depth, encoder layout, native feature packing on now-half activations, exact affine output, cuDNN search and host arena count, result threshold. All3 independent complete official worker rounds, all200 inputs afterREADY, process-group exit and fsync retained, each output scored. Any precision failure or runtime failure recorded and not submitted. Gate reference0.98*0.7935=0.77763; validation for new variants=null; hidden=null. Scorer/timer unchanged. Known rejected input512 and cudaMallocAsync not repeated.

This is a broad screen, not a paired proof for each marginal score gain. Current best only replaced by strictly faster passing complete3-round logs; no stitched rounds or old-log resubmission. Local raw artifacts output/20261026-014213-configwide; source SHA/commands/configs in every case command.json and metrics.json. Parent manifests preserve data/weights/tool hashes, refreshed before finalization.

## Completed2026-10-26 01:50 CST

17cases/51complete200-image worker rounds; no runtime failures.15configurations passed all3AP gates, decoder2(AP50~0.7710) and score0.075(AP50<=0.7775) failed and were not uploaded. Both retained. Control independent median271.317521ms was accepted, then cudnn-fixed median266.237340ms accepted at01:49:15. All sources and commands in results.json; source0c3ed80 recorded in each case. No large validation; hidden=null.

| Variant | 3 rounds ms | Median ms | Reference AP50 | Uploaded |
|---|---|---:|---|---|
|control|266.770/271.318/288.122|271.318|0.7809,0.7815,0.7809|True|
|batch6|291.005/295.248/290.110|291.005|0.782,0.7809,0.7809|False|
|batch10|272.994/264.258/271.938|271.938|0.7815,0.7813,0.7813|False|
|batch12|278.051/290.917/265.456|278.051|0.7807,0.7813,0.7808|False|
|batch24|306.644/300.189/309.850|306.644|0.7813,0.7813,0.7813|False|
|batch32|338.869/332.449/330.652|332.449|0.7813,0.7816,0.7816|False|
|workers9|276.148/352.001/275.962|276.148|0.7813,0.7809,0.7809|False|
|workers11|305.274/313.839/295.981|305.274|0.7815,0.7809,0.7814|False|
|depth2|313.934/296.887/308.292|308.292|0.7809,0.7809,0.7809|False|
|depth4|274.676/284.615/268.153|274.676|0.7809,0.7814,0.7815|False|
|decoder2|268.615/274.345/273.854|273.854|0.771,0.771,0.7711|False|
|encoder-layout|272.683/260.844/289.477|272.683|0.7811,0.7815,0.7808|False|
|native-cat|274.519/262.119/333.230|274.519|0.7813,0.7813,0.7808|False|
|affine-exact|277.252/325.588/323.878|323.878|0.7812,0.7811,0.7812|False|
|cudnn-fixed|298.391/264.835/266.237|266.237|0.7809,0.7809,0.7809|True|
|arena2|270.634/266.908/264.293|266.908|0.7814,0.7815,0.781|False|
|score075|266.171/265.192/270.752|266.171|0.7775,0.7769,0.7774|False|

New accepted score improvement3.4445% vs previous275.737156ms; repeated-control improvement and broad timing overlap mean this is not a paired causal proof for cuDNN. Selected config batch8,w10,depth3,full3-layer decoder,threshold0.05,half-output affine,CUDNN_BENCHMARK=0. Preserve high-precision parent and all historical logs. GPU0 released to fusedio experiment01:50; no overlap. Python compilation/diff checks passed; official timer/scorer unchanged. Raw artifacts local-only output/20261026-014213-configwide; main output symlink preserves discovery. Reproduce using run_case.py cudnn-fixed --split reference --runs 3 --combined-log --name UNIQUE in this branch.

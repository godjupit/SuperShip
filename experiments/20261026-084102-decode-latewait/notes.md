# Defer input-slot wait until decoded pixels are ready

ID20261026-084102-decode-latewait; ownerCodex/root; statuscompleted; parent4db824339e9009ec6b66a16d16c775bbfd75f9b4 (newly verified/promotedfastestmain), no prior config sweep duplication. GPU0RTX4090 reserved08:41 after idle/main handover. Single registered hypothesisDECODE_BEFORE_COPY_WAIT=1: CPUdecode/resize ahead of reusable pinned-buffer fence; no destination modification before event completes. Preserve exact image/output values, dimensions, full worker protocol. Variantsbaseline0/candidate1,3complete public200 reference runs each,8alternating one-run pairs for confirmation if screen succeeds. Independent formal runs retained; paired diagnostics never uploaded. Validation/hidden=null.

## Results — no promotion

Actual experiment source `d3d301a` (fullSHAinresults.json), no uncommitted runtime patch. Exact defaults are inheritedmainconfigs/fastest.env; onlyDECODE_BEFORE_COPY_WAIT differs. Runtime/score commands and all overrides stored inrun.py/eachcommand.json/results.json.

| Variant | Three complete roundsms | Medianms | ReferenceAP50 |
| --- | --- | ---: | --- |
| baselineflag0 |260.364199 /308.026727 /261.682067|261.682067|0.7809all|
| latewaitflag1 |260.199672 /261.792209 /262.471628|261.792209|0.7809all|

Three-round candidate median is0.042%slower. Eight independent alternatingAB/BA pairs: baseline median264.734377ms, candidate261.493858ms (nominal1.2241%lower), but only5/8wins; exact two-sided sign-flip test on paired differencesp=0.796875. These paired observations do not establish reliable benefit. All times including baseline308ms and candidatepair4 283.836ms retained. See paired.json for every pair. Do not promote or modify fastestmain preset.

All22predictions byte-identical to parent,200images/6102detections each,referenceAP50=0.7809; actual baseline0.7935 gives98%gate0.77763,ratio0.984121andmargin0.00327. Validation/hidden=null, no larger validation or competition submission; Accepted258.409792ms unchanged.35tests passed: fence waits after decode, destination untouched until synchronize, RGB/odd dimensions exact, ringreuse+tails+empty inputs+threaded output withflag0/1. Officialtimer/scorer/data/weights verified against parentmanifest, all artifacts hashed, Python compilation/gitdiff checks pass. No32GBhard-cap test repeated; no model/precision/persistent memory expansion. Main stays on fastestthread100-light; experiment code preserved here for reproducibility.

GPU0RTX4090 exclusive08:41–08:44CST, verifiedidle/released after final pair. Same EPYC7402/10CPUcores,torch2.6.0+cu124/cuDNN90100/OpenCV4.11/Triton3.2 as preceding main promotion/profile. Raw outputs/logs/commands localonly in `/tmp/SuperShip-decode-latewait-20261026/output/20261026-084102-decode-latewait/`, also linked under mainoutput. Off-machine reproduction requires matching public assets and dependencies, not merely this local path.

Reproduce at this experimentbranch in a fresh worktree, provide data/SuperShip and weights/baseline.pth, then `/home/ubuntu/.cache/supership-venv/bin/python experiments/20261026-084102-decode-latewait/run.py`. Outputdirectoriesmustbenew; adjust interpreterpath inrun.py on anothermachine. Allcomplete3-round logs and allpairoutputs scored independently; no uploads.

Next candidate direction: decoded-image service cost or algorithmic layout work with a new single registered hypothesis; moving only the copy fence proved insufficient.

Main archive stores records only; experimentalrun.py and changedruntime/tests remain on `exp/decode-latewait-20261026` atf4788e9. Reproduction requires that branch rather than main.

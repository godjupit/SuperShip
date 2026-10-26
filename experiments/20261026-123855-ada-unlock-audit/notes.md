# RTX4090 Ada unlock preparation and stock baseline

Experiment `20261026-123855-ada-unlock-audit`; owner Codex/root; branch `exp/ada-unlock-20261026`; status **completed (preparation/audit)**; updated2026-10-26 12:44CST. Upstream source `d28c485418c3d9d034cd4bac19200bc33dd3453b`, cloned at `/home/ubuntu/gpu-unlock-ada-reviewed`. SuperShip full source SHA, exact binary/source/firmware pins and runtime environment are in [manifest.json](manifest.json) and [summary.json](summary.json). Parent audit20261026-122450-gpu-unlock-audit examined Ampere-only upstream; this fork supplies the distinct AD102 payload, not just a changed PCI whitelist. Main already contains verified thread100-light; no runtime/config changes made.

## Evidence

- Source `kernel/gpu_unlock/main.c` admits RTX4090 device2684; upstream read-only `python3 tools/print_boot_option.py` correctly prints `gpu_unlock.targets=0000:29:00.0` for this host.
- Built `gpu_unlock.ko` against installed Linux5.15.0-128-generic headers, moduleversion1.1.1; CONFIG_CRYPTO_LIB_SHA256=y. BTF skipped because vmlinux absent, module build succeeds. DKMS command is not currently installed. EFI variables unavailable; bootloader/recovery path has not been validated. Driver stays550.142; no driver upgrade performed.
- Read-only RM getter on driver550.142 succeeds: fmla32=1, imla2=1, imla4=1; other fields0. Getter defines0=full,1=half. [Sanitized values](sm-rates.json). This observes current rate settings, not proof of successful unlock or its application benefit.
- `make test`:30tests,9skips,no failure. `make assets CACHE=build/audit-20261026-123855/cache` downloads326MiB of pinned NVIDIA610.43.03 source/package, verifiesSHA256 and locally generates GA102+AD102 firmware. Nothing installed. `make test-full CACHE=build/audit-20261026-123855/cache`:33tests,3optional PyCryptodome decoder skips,no failure; real-asset GA102 and AD102 mocked transactions pass. Tests still model firmware/hardware; no live transaction occurred.
- Native `mma_bench.cu` sm89 build fails underCUDA11.8 because PTX assembler lacks e4m3 FP8 instruction support; complete [failure log](mma-build.log) retained. Fallback uses unchanged upstream `tensor_modes_issue.cu`/driver runner (FP16/TF32/unsignedINT4), successfully compiledsm89 withCUDA11.8. BinarySHA256b1274a5aa7a8469bf100b71a49bccb8372457913b692d094ce3692f8f92070a8.

GPU0 idle/process check passed; exclusive stock-only GPU work12:40–12:43CST, released after last baseline, no clocks/power/driver changes. CUDA instruction probe20000iterations,3reps,450W,exactUUID/cubin checks. Every mode checks270336cells,0mismatches:

| Mode | Three rates | Unit | Median |
| --- | --- | --- | --- |
| FP16/FP32 |151.304633 /151.325820 /151.322239|TFLOPS|151.322239|
| TF32/FP32 |76.634467 /81.057838 /81.060274|TFLOPS|81.057838|
| unsignedINT4/INT32 |1288.771793 /1288.709426 /1288.771793|TOPS|1288.771793|

[Stock probe](stock-probe.json); instruction rates are not GEMM or application throughput.

## Full worker stock control

First three inference rounds354.375896/290.314976/312.176118ms overlap CPU firmware generation; retained in stock-full.log/summary.json as preliminary and **timing-invalid for formal comparison**. After all builds/tests finish, repeat clean three full worker rounds: **265.256365 /251.750705 /257.130582ms**, median **257.130582ms**. All outputs process200images/6102detections, have SHA2564185ed612afb8234afae8e31eb43bafd0b68ef32c124d0d510d2da745f29100c, byte-equal previous selected candidate. Fresh scoring AP50=0.7809each vs referencebaseline0.7935,ratio0.9841210,gate0.77763,margin0.00327. ValidationAP50=null,hiddenAP50=null. Batch8 exactly divides200:25batches,no partial tail exercised here; unchanged production tailhandling inherited. No new correctness tests needed for unchanged inference code.

READY/input/output/process-exit protocol unchanged; no evaluation access before READY by worker. Host52GiB total, no fresh32GiB hardcap run. All200input hashes, weights, metadata, annotations, timer/scorer/launcher/preset hashes in [assets-sha256.json](assets-sha256.json). No baseline CPU/GPU background jobs identified during clean run. This is the same current implementation; a new stock measurement does not establish any optimization gain and is not uploaded.

Reproduce baseline from SuperShip root with matching data/weights and recorded configs/fastest.env:

```bash
PYTHON_BIN=/home/ubuntu/.cache/supership-venv/bin/python /home/ubuntu/.cache/supership-venv/bin/python supership/benchmark_submission.py --image-dir data/SuperShip/reference/images --meta-file data/SuperShip/reference/reference_images_meta.json --output-file output/NEW_UNIQUE_CASE/stock-clean.json --runs 3 --init-timeout 300 --run-timeout 3600 -- env PYTHON_BIN=/home/ubuntu/.cache/supership-venv/bin/python TRITON_CACHE_DIR=/home/ubuntu/.triton/cache bash run.sh --worker
```

Score each .runN.json with the unchanged `supership/score_submission.py --gt data/SuperShip/reference/annotations/instances_reference.json --submission PATH`. Raw predictions and score logs local only at `/home/ubuntu/SuperShip-main 2/output/20261026-123855-ada-unlock-audit/`; upstream cache/binaries/rawUUID evidence local only in `/home/ubuntu/gpu-unlock-ada-reviewed/build/audit-20261026-123855/`. Git carries compact logs/checksums, no firmware or credentials. Off-host reproduction requires public data, weights and matching system; binaries/firmware can be rebuilt from pinned source/inputs.

## Remaining transition

No module loaded/installed, no boot/initramfs change, driver unload/reset, poweroff or reboot. Actual unlock and after measurements remain **unperformed**. Upstream QUICKSTART.md step4 calls for full poweroff/fresh card state; already-driver-bound manual loading cannot unlock it. An actual test needs owner authorization and a way to restore power/recover the remote machine, then review exact bootloader entries, install/build dependencies and module+firmware into an early initramfs with exacttarget0000:29:00.0, preserve stockboot entry, coldstart, verify card-specific completion/selector/postFLR logs and healthy550.142driver. A compatible build alone does not prove firmware handoff with this older driver. Retest identical cubin and fullworker>=3rounds plus freshprecision; retain all regressions and verify kernel/driver/450W identical.

No speedup claimed, no candidate promotion, no competition upload; fastest implementation/currentAccepted258.409792ms unchanged; hiddenbestunknown. GPU released. Prepared evidence is concrete; cold-boot test awaits explicit owner scheduling rather than silently shutting down an active remote host.

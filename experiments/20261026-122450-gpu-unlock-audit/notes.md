# gpu-unlock applicability audit

Experiment `20261026-122450-gpu-unlock-audit`; owner Codex /root; branch `exp/gpu-unlock-20261026`; status **completed**; updated2026-10-26 12:26CST. Parent main `dbaca8889e89e1782fa10eef1e1d554c3b35505f`; registration commit and exact source/log checksums in [manifest.json](manifest.json). No inference implementation or configuration changes. Main already contains the verified thread100-light candidate; prior no-benefit experiments do not supersede it.

## Findings

Cloned https://github.com/Zagitta/gpu-unlock to `/home/ubuntu/gpu-unlock-reviewed`, pinned upstream `af28cbbfd3d922a659227ecfb7369adfd924cf03`. This is an early-boot Linux kernel module that changes Ampere speed selectors before the NVIDIA driver binds, followed by function-level reset; it is not a PyTorch/Triton kernel optimization. Source `kernel/gpu_unlock/main.c:22–36` supports GA102/GA103/GA104/GA106 PCI IDs. The RTX3090 device2204 is included; this host's sole RTX4090 device2684 is absent. The read-only [probe](probe.py) reads the actual upstream whitelist and enumerates NVIDIA PCI devices in sysfs; [result](applicability.json): **zero applicable devices**. NVIDIA audio function22ba is also excluded. The display function is already bound to nvidia. `main.c:68` refuses boot unlock on a bound card. Loading it into the current runtime cannot enable the requested optimization.

Upstream README reports RTX3090 BF16 dense GEMM gains of25–67% across user reports. These are upstream reports, not local measurements, and not evidence for this RT-DETR FP16 end-to-end workload. Our hypothesis is relevant to the competition's3090, but requires an actual supported3090 host and driver-before-bind boot setup; changing application code alone cannot reproduce it. Competition documentation requires a3090 but does not establish permission to modify the official host's boot/driver environment.

## Checks and limits

`make test` passed **5 unittest tests**, including six C component executables compiled using mocked kernel/PCI shims, packaging layout in temporary DESTDIR, and pinned payload checksum checks. Full generated-firmware hardware simulation was not enabled: firmware assets are absent. These tests establish upstream host checks only; no hardware unlock or measured speed gain is claimed. Full test output is [upstream-tests.txt](upstream-tests.txt). Local raw copy: `output/20261026-122450-gpu-unlock-audit/upstream-tests.log`.

No module installed/loaded, boot options changed, driver unbound, GPU reset or reboot. GPU0 remained idle/unreserved. No evaluation inputs, weights or data accessed, so dataset/weight hashes are not applicable. Reference AP50=null, validation AP50=null, hidden AP50=null; before/after times=null. No full inference timing was run because no supported GPU or unlock treatment exists here; running three unchanged4090 rounds would not measure this hypothesis. Current main/fastest candidate and Accepted258.409792ms remain unchanged; hidden best unknown. No competition submission.

## Reproduce and handoff

```bash
git clone https://github.com/Zagitta/gpu-unlock /PATH/gpu-unlock
git -C /PATH/gpu-unlock checkout af28cbbfd3d922a659227ecfb7369adfd924cf03
python3 experiments/20261026-122450-gpu-unlock-audit/probe.py /PATH/gpu-unlock
make -C /PATH/gpu-unlock test
```

Network workaround on this host: default Git proxy127.0.0.1:17897 refused connections and direct Git stalled; clone/push succeeded with per-command `git -c http.proxy=http://127.0.0.1:7897 ...`. No global config changed. Initial stalled clone at `/home/ubuntu/gpu-unlock` was interrupted (only this task's processes); successful complete clone is the reviewed path above. An initial log redirection failed before tests ran because the output directory did not exist; after creating the intended directory the test command passed.

Next meaningful test requires a supported RTX3090 machine: collect >=3 complete before rounds under the same protocol, apply the host-level module, verify boot logs, then >=3 complete after rounds, validate coverage/tails and fresh reference/validation AP50, retain every result and alternate/recheck if margins overlap. Do not extrapolate GEMM speedups to end-to-end inference or insert this into run.sh. No main promotion is justified by this audit.

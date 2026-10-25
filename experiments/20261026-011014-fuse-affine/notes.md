# GPU activation/affine fusion

ID 20261026-011014-fuse-affine; Codex /root; running; GPU0 RTX4090 reserved2026-10-26 01:10 CST. Parent 67f2d7f0eef9bdd13810146c6c8ae8d4e687694b, accepted runtime dff7a19. User explicitly requested a different optimization; no CPU-supply/import/resize changes from the abandoned branch are included.

Hypothesis: replace separate ReLU + float32 learned scalar multiply + add with one Triton kernel, preserving output float32 and scalar dtypes; disable multiply-add fusion to match original separate arithmetic. All trained weights remain strictly loaded before patching, image decoder/resize and full3-layer model unchanged. Same official timer/scorer/data as parent. Exact tensor tests, CUDA Graph replay, all input/tail checks and reference+validation gates before timing promotion.32GB host memory constraint retained; currentAccepted285.962649ms preserved until a faster independently validated new3-round log. Hidden AP50=null.

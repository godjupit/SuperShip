# Further optimization: decoder1-score004

Source: `585d759e3e2563733ef6dc18d2ff638333ee41be`, dirty=True (saved source.patch when dirty).

Full effective parameters: config.json. Full command, runtime/precision results, dataset metadata and weight SHA256, and raw artifacts: metrics.json.

Measured on one RTX 4090 with the unchanged official timer and validator pinned in the repository. No test images or metadata are accessed before READY.

Status: success. Validation AP50 and hidden AP50 are unmeasured unless explicitly populated.

Validation: full 1,030 public images; AP50=0.8926, same-split baseline=0.9170, 98% threshold=0.89866, pass=False. Logs and predictions in /home/ubuntu/SuperShip-optimize/output/submissions/20261022-195339-further-decoder1-score004/validation. No validation timing is submitted.

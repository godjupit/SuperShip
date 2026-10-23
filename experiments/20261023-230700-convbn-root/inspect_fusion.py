"""Audit actual checkpoint fusion coverage and synthetic FP32/FP16 errors."""

import copy
import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", required=True, help="New JSON path; existing files are preserved")
args = parser.parse_args()
output = Path(args.output).resolve()
if output.exists():
    raise FileExistsError(output)
output.parent.mkdir(parents=True, exist_ok=True)
config = json.loads(Path(__file__).with_name("config.json").read_text())
os.environ.update(config)
os.environ["FUSE_CONV_BN"] = "0"

import torch
from supership.fast_worker import Runtime
from supership.conv_bn_fusion import fuse_model_conv_bn
from supership.generate_submission import model_forward

runtime = Runtime()
before = [name for name, m in runtime.model.named_modules() if isinstance(m, torch.nn.BatchNorm2d)]
fused_model = copy.deepcopy(runtime.model)
names = fuse_model_conv_bn(fused_model)
after = [name for name, m in fused_model.named_modules() if isinstance(m, torch.nn.BatchNorm2d)]
report = dict(fused_count=len(names), fused_names=names, bn_before=before, bn_after=after,
              errors={}, feature_errors={}, input="seed42 synthetic normal tensor (2,3,544,544); no dataset access")
# Verify the folding in FP32 without TF32 rounding. End-to-end FP16 accuracy is
# checked separately on real images; top-k query ordering is not continuous.
torch.backends.cudnn.allow_tf32 = False
torch.backends.cuda.matmul.allow_tf32 = False
report["synthetic_tf32"] = False
torch.manual_seed(42)
inputs = torch.randn(2, 3, 544, 544, device="cuda").to(memory_format=torch.channels_last)
with torch.inference_mode():
    for precision in ["fp32", "fp16"]:
        expected = model_forward(runtime.model, inputs, precision)
        actual = model_forward(fused_model, inputs, precision)
        report["errors"][precision] = {}
        for key in ["pred_boxes", "pred_logits"]:
            assert torch.isfinite(actual[key]).all()
            difference = (expected[key] - actual[key]).abs()
            report["errors"][precision][key] = dict(max_absolute=difference.max().item(),
                                                     mean_absolute=difference.mean().item())
        if precision == "fp32":
            expected_features = runtime.model.encoder(runtime.model.backbone(inputs))
            actual_features = fused_model.encoder(fused_model.backbone(inputs))
            for index, (expected_feature, actual_feature) in enumerate(zip(expected_features, actual_features)):
                delta = (actual_feature - expected_feature).abs()
                report["feature_errors"][str(index)] = dict(max_absolute=delta.max().item(),
                                                           mean_absolute=delta.mean().item())
                torch.testing.assert_close(actual_feature, expected_feature, rtol=1e-3, atol=1e-3)
assert len(names) == len(before) and not after
with output.open("x") as stream:
    stream.write(json.dumps(report, indent=2) + "\n")
print(json.dumps({key: value for key, value in report.items() if key not in ("fused_names", "bn_before")}), flush=True)

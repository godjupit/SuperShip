"""Profile the current eager PyTorch model with real images and module scopes.

GPU percentages use exclusive operator device time, avoiding nested double counting.
This is a model-forward diagnostic, not an end-to-end benchmark or accuracy test.
"""

import argparse
import csv
import hashlib
import json
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import torch
from PIL import Image
from torchvision.transforms import functional as F

from supership.generate_submission import build_runtime, model_forward


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def add_scopes(model):
    handles, scopes = [], []

    def before(label):
        def hook(module, inputs):
            scope = torch.profiler.record_function(label)
            scope.__enter__()
            scopes.append(scope)
        return hook

    def after(module, inputs, output):
        scopes.pop().__exit__(None, None, None)

    for name, module in model.named_modules():
        if name in {"backbone", "encoder", "decoder"} or name.endswith(("self_attn", "cross_attn")):
            handles.append(module.register_forward_pre_hook(before("module::" + name)))
            handles.append(module.register_forward_hook(after, always_call=True))
    return handles


def analyze(prof, steps):
    # Only CPU launch events: CUDA kernel events represent the same work again.
    operators, groups = {}, {}
    for event in prof.events():
        if event.device_type != torch.autograd.DeviceType.CPU:
            continue
        us = event.self_device_time_total
        if us <= 0:
            continue
        operators[event.name] = operators.get(event.name, 0.) + us
        parent, group = event, "other"
        while parent is not None:
            if parent.name.startswith("module::"):
                group = parent.name.removeprefix("module::")
                break
            parent = parent.cpu_parent
        groups[group] = groups.get(group, 0.) + us
    total = sum(operators.values())
    if total <= 0:
        raise RuntimeError("No attributed GPU time captured; inspect CUPTI/profiler availability")

    def rows(values):
        return [{"name": name, "gpu_ms_per_batch": us / steps / 1000,
                 "gpu_percent": 100 * us / total}
                for name, us in sorted(values.items(), key=lambda item: item[1], reverse=True)]

    attention = sum(us for name, us in groups.items() if name.endswith("self_attn"))
    cross = sum(us for name, us in groups.items() if name.endswith("cross_attn"))
    return {"gpu_kernel_ms_per_batch": total / steps / 1000,
            "self_attention_percent": 100 * attention / total,
            "cross_attention_percent": 100 * cross / total,
            "operators": rows(operators), "exclusive_modules": rows(groups)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/dfine/dfine_hgnetv2_s_supership.yml")
    parser.add_argument("--weights", default="weights/baseline.pth")
    parser.add_argument("--image-dir", default="data/SuperShip/val/images")
    parser.add_argument("--annotations", default="data/SuperShip/val/annotations/instances_val.json")
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--precision", choices=["fp32", "fp16"], default="fp32")
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--batches", type=int, default=5)
    parser.add_argument("--warmup", type=int, default=5)
    parser.add_argument("--timing-steps", type=int, default=20)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    if min(args.batch_size, args.batches, args.timing_steps, args.repeats) < 1 or args.warmup < 0:
        parser.error("counts must be positive; warmup must be nonnegative")
    if not args.device.startswith("cuda") or not torch.cuda.is_available():
        parser.error("this experiment requires CUDA")
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=False)
    torch.cuda.set_device(args.device)
    torch.manual_seed(42)
    torch.set_num_threads(4)
    _, model, _ = build_runtime(args.config, args.weights, args.device)
    images = json.loads(Path(args.annotations).read_text())["images"]
    needed = args.batch_size * args.batches
    if len(images) < needed:
        raise ValueError("not enough images for complete batches")
    # Spread deterministic samples over the split rather than repeating one image.
    selected = [images[i * len(images) // needed] for i in range(needed)]
    tensors = []
    for item in selected:
        with Image.open(Path(args.image_dir) / item["file_name"]) as image:
            tensors.append(F.pil_to_tensor(F.resize(image.convert("RGB"), [640, 640])).float() / 255.)
    batches = [torch.stack(tensors[i:i + args.batch_size]).to(args.device)
               for i in range(0, len(tensors), args.batch_size)]
    write_json(output / "parameters.json", vars(args) | {
        "backend": "torch_eager", "deploy_conversion": False,
        "sample_files": [item["file_name"] for item in selected],
        "annotations_sha256": hashlib.sha256(Path(args.annotations).read_bytes()).hexdigest(),
        "weights_sha256": hashlib.sha256(Path(args.weights).read_bytes()).hexdigest(),
        "scope": "forward only, images already resident on GPU",
        "seed": 42, "cpu_threads": 4, "torch": torch.__version__,
        "cuda": torch.version.cuda, "gpu": torch.cuda.get_device_name(args.device),
        "cudnn_benchmark": torch.backends.cudnn.benchmark,
        "matmul_allow_tf32": torch.backends.cuda.matmul.allow_tf32,
        "cudnn_allow_tf32": torch.backends.cudnn.allow_tf32,
    })
    timings, reports = [], []
    with torch.inference_mode():
        for index in range(args.warmup):
            model_forward(model, batches[index % len(batches)], args.precision)
        torch.cuda.synchronize()
        # No hooks and no profiler during baseline timing; events span queued forwards.
        for repeat in range(args.repeats):
            start, end = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
            start.record()
            for index in range(args.timing_steps):
                model_forward(model, batches[index % len(batches)], args.precision)
            end.record()
            end.synchronize()
            timings.append(start.elapsed_time(end) / args.timing_steps)
        handles = add_scopes(model)
        try:
            for repeat in range(args.repeats):
                with torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU,
                                                       torch.profiler.ProfilerActivity.CUDA]) as prof:
                    for samples in batches:
                        with torch.profiler.record_function("model_forward"):
                            model_forward(model, samples, args.precision)
                        prof.step()
                    torch.cuda.synchronize()
                reports.append(analyze(prof, len(batches)))
                if repeat == 0:
                    prof.export_chrome_trace(str(output / "trace.json"))
                    (output / "operator_table.txt").write_text(
                        prof.key_averages().table(sort_by="self_cuda_time_total", row_limit=40))
                print(f"Profile {repeat + 1}: self-attention={reports[-1]['self_attention_percent']:.2f}%", flush=True)
        finally:
            for handle in handles:
                handle.remove()
    result = {"unprofiled_forward_ms_per_batch_runs": timings,
              "unprofiled_forward_ms_per_batch_median": statistics.median(timings),
              "self_attention_percent_runs": [r["self_attention_percent"] for r in reports],
              "cross_attention_percent_runs": [r["cross_attention_percent"] for r in reports],
              "profile_runs": reports,
              "note": "profile percentages use summed exclusive GPU kernel time, not wall time; no AP50 or end-to-end measurement"}
    write_json(output / "profile.json", result)
    for key in ["operators", "exclusive_modules"]:
        names = set(row["name"] for report in reports for row in report[key])
        averaged = []
        for name in names:
            ms = sum(next((row["gpu_ms_per_batch"] for row in r[key] if row["name"] == name), 0.) for r in reports) / len(reports)
            averaged.append({"name": name, "gpu_ms_per_batch": ms})
        total = sum(row["gpu_ms_per_batch"] for row in averaged)
        averaged.sort(key=lambda row: row["gpu_ms_per_batch"], reverse=True)
        for row in averaged:
            row["gpu_percent"] = row["gpu_ms_per_batch"] / total * 100
        write_json(output / f"{key}.json", averaged)
        with (output / f"{key}.csv").open("w") as handle:
            writer = csv.DictWriter(handle, fieldnames=["name", "gpu_ms_per_batch", "gpu_percent"])
            writer.writeheader()
            writer.writerows(averaged)
    print(json.dumps({k: v for k, v in result.items() if k != "profile_runs"}, indent=2))


if __name__ == "__main__":
    main()

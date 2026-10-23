"""Reproduce an isolated baseline/fused reference or full validation run."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--output", required=True)
    parser.add_argument("--fuse", choices=["0", "1"], required=True)
    parser.add_argument("--split", choices=["reference", "val"], default="reference")
    parser.add_argument("--runs", type=int, default=3)
    args = parser.parse_args()
    config = json.loads(Path(__file__).with_name("config.json").read_text())
    config["FUSE_CONV_BN"] = args.fuse
    root, output = Path(args.root).resolve(), Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    python = config["PYTHON_BIN"]
    env = {**os.environ, **config}
    env.pop("FAST_PROFILE", None)
    split = args.split
    metadata = ("data/SuperShip/reference/reference_images_meta.json" if split == "reference"
                else "data/SuperShip/val/annotations/instances_val.json")
    gt = ("data/SuperShip/reference/annotations/instances_reference.json" if split == "reference"
          else metadata)
    command = [python, "supership/benchmark_submission.py", "--image-dir",
               f"data/SuperShip/{split}/images", "--meta-file", metadata,
               "--output-file", str(output / "predictions.json"), "--runs", str(args.runs),
               "--", "bash", "run.sh", "--worker"]
    source = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    (output / "command.json").write_text(json.dumps(dict(command=command, cwd=str(root),
        config=config, source_commit=source), indent=2) + "\n")
    with (output / "benchmark.log").open("w") as log:
        subprocess.run(command, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
    lines = (output / "benchmark.log").read_text().splitlines()
    metrics = next(json.loads(line) for line in reversed(lines) if line.startswith('{"runs_seconds"'))
    metrics.update(split=split, fuse=args.fuse, source_commit=source, config=config,
                   reference_ap50_per_run=[], prediction_sha256=[], hidden_ap50=None)
    for index in range(1, args.runs + 1):
        prediction = output / (f"predictions.run{index}.json" if args.runs > 1 else "predictions.json")
        score_log = output / f"score{index}.log"
        with score_log.open("w") as log:
            subprocess.run([python, "supership/score_submission.py", "--gt", gt,
                            "--submission", str(prediction)], cwd=root, env=env,
                           stdout=log, stderr=subprocess.STDOUT, check=True)
        score = float(re.search(r"AP@0\.50\s+([0-9.]+)", score_log.read_text()).group(1))
        metrics["reference_ap50_per_run"].append(score)
        metrics["prediction_sha256"].append(hashlib.sha256(prediction.read_bytes()).hexdigest())
    if split == "val":
        metrics["validation_ap50_per_run"] = metrics.pop("reference_ap50_per_run")
    (output / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    print(json.dumps(dict(output=str(output), **metrics)), flush=True)


if __name__ == "__main__":
    main()

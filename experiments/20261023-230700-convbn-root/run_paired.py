"""Run ten paired independent workers, alternating AB/BA order."""

import argparse
import json
from pathlib import Path
import statistics
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--baseline-root", required=True)
    parser.add_argument("--repetitions", type=int, default=10)
    args = parser.parse_args()
    if args.repetitions < 1:
        parser.error("repetitions must be positive")
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    runner = Path(__file__).with_name("run.py")
    root = runner.resolve().parents[2]
    pairs = []
    for index in range(1, args.repetitions + 1):
        pair = dict(index=index, order=["baseline", "fused"] if index % 2 else ["fused", "baseline"])
        for kind in pair["order"]:
            destination = output / f"pair{index:02d}-{kind}"
            command = [sys.executable, str(runner), "--output", str(destination), "--fuse",
                       "1" if kind == "fused" else "0", "--runs", "1"]
            if kind == "baseline":
                command += ["--root", args.baseline_root]
            log = output / f"pair{index:02d}-{kind}.log"
            with log.open("x") as stream:
                subprocess.run(command, cwd=root, stdout=stream, stderr=subprocess.STDOUT, check=True)
            pair[kind] = json.loads((destination / "metrics.json").read_text())
        before, after = [pair[kind]["runs_seconds"][0] for kind in ["baseline", "fused"]]
        pair["reduction_seconds"] = before - after
        pair["reduction_percent"] = (1 - after / before) * 100
        pairs.append(pair)
        (output / "pairs.json").write_text(json.dumps(pairs, indent=2) + "\n")
        print(f"Pair {index}/{args.repetitions}: baseline={before:.9f}s fused={after:.9f}s "
              f"reduction={pair['reduction_percent']:.2f}% order={pair['order']}", flush=True)
    summary = dict(pairs=pairs)
    for kind in ["baseline", "fused"]:
        times = [pair[kind]["runs_seconds"][0] for pair in pairs]
        summary[kind] = dict(runs_seconds=times, median_seconds=statistics.median(times),
                             mean_seconds=statistics.mean(times), min_seconds=min(times),
                             max_seconds=max(times), stdev_seconds=statistics.stdev(times) if len(times) > 1 else 0,
                             ap50=[pair[kind]["reference_ap50_per_run"][0] for pair in pairs])
    summary["median_reduction_percent"] = (
        1 - summary["fused"]["median_seconds"] / summary["baseline"]["median_seconds"]) * 100
    summary["paired_median_reduction_seconds"] = statistics.median(p["reduction_seconds"] for p in pairs)
    summary["fused_faster_pairs"] = sum(p["reduction_seconds"] > 0 for p in pairs)
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "pairs"}), flush=True)


if __name__ == "__main__":
    main()

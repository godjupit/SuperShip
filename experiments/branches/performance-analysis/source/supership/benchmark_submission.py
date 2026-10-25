"""Measure end-to-end inference after an untimed initialization stage."""

import argparse
import json
import math
import os
import selectors
import statistics
import subprocess
import sys
import threading
import time
from pathlib import Path


READY_MARKER = "THU_RS_READY"


def parse_args():
    parser = argparse.ArgumentParser(
        usage=(
            "%(prog)s --image-dir DIR --meta-file FILE --output-file FILE "
            "[options] -- COMMAND [ARG ...]"
        )
    )
    parser.add_argument("--image-dir", required=True)
    parser.add_argument("--meta-file", required=True)
    parser.add_argument("--output-file", required=True)
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--init-timeout", type=float, default=300.0)
    parser.add_argument("--run-timeout", type=float, default=3600.0)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.command and args.command[0] == "--":
        args.command = args.command[1:]
    if not args.command:
        parser.error("a worker command is required after --")
    if args.runs < 1:
        parser.error("--runs must be at least 1")
    return args


def wait_for_ready(process, timeout):
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ)
    deadline = time.monotonic() + timeout

    try:
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(f"init did not finish within {timeout:.1f} seconds")
            events = selector.select(remaining)
            if not events:
                continue
            line = process.stdout.readline()
            if line == "":
                code = process.poll()
                raise RuntimeError(f"worker exited before READY (exit code {code})")
            if line.strip() == READY_MARKER:
                return
    finally:
        selector.close()


def validate_output(path):
    with open(path, "r", encoding="utf-8") as submission_file:
        submission = json.load(submission_file)
    if not isinstance(submission, list):
        raise ValueError("submission must be a JSON array")

    required = {"image_id", "category_id", "bbox", "score"}
    for index, detection in enumerate(submission):
        if not isinstance(detection, dict) or not required.issubset(detection):
            raise ValueError(f"detection {index} has missing or invalid fields")
        if detection["category_id"] not in (0, 1, 2):
            raise ValueError(f"detection {index} has an invalid category_id")
        bbox = detection["bbox"]
        if not isinstance(bbox, list) or len(bbox) != 4:
            raise ValueError(f"detection {index} has an invalid bbox")
        values = [*bbox, detection["score"]]
        if not all(
            isinstance(value, (int, float)) and math.isfinite(value)
            for value in values
        ):
            raise ValueError(f"detection {index} contains a non-finite number")
        if bbox[2] <= 0 or bbox[3] <= 0:
            raise ValueError(f"detection {index} has a non-positive bbox")
        if not 0 <= detection["score"] <= 1:
            raise ValueError(f"detection {index} has an invalid score")
    return len(submission)


def output_path_for_run(base_path, run_index, runs):
    if runs == 1:
        return base_path
    path = Path(base_path)
    return str(path.with_name(f"{path.stem}.run{run_index + 1}{path.suffix}"))


def terminate(process):
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def drain_stdout(stream):
    for _line in stream:
        pass


def run_once(args, run_index):
    output_file = output_path_for_run(args.output_file, run_index, args.runs)
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.unlink(missing_ok=True)

    process = subprocess.Popen(
        args.command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=None,
        text=True,
        bufsize=1,
    )

    try:
        wait_for_ready(process, args.init_timeout)
        threading.Thread(
            target=drain_stdout, args=(process.stdout,), daemon=True
        ).start()
        request = json.dumps(
            {
                "image_dir": os.path.abspath(args.image_dir),
                "meta_file": os.path.abspath(args.meta_file),
                "output_file": os.path.abspath(output_file),
            },
            separators=(",", ":"),
        )

        start_ns = time.monotonic_ns()
        process.stdin.write(request + "\n")
        process.stdin.flush()
        process.stdin.close()
        try:
            return_code = process.wait(timeout=args.run_timeout)
        except subprocess.TimeoutExpired as error:
            raise TimeoutError(
                f"inference exceeded {args.run_timeout:.1f} seconds"
            ) from error
        elapsed_seconds = (time.monotonic_ns() - start_ns) / 1_000_000_000

        if return_code != 0:
            raise RuntimeError(f"worker failed with exit code {return_code}")
        detection_count = validate_output(output_file)
        return elapsed_seconds, output_file, detection_count
    finally:
        terminate(process)


def main():
    args = parse_args()
    durations = []
    for run_index in range(args.runs):
        elapsed, output_file, detection_count = run_once(args, run_index)
        durations.append(elapsed)
        print(
            f"run {run_index + 1}/{args.runs}: {elapsed:.6f} s, "
            f"{detection_count} detections, {output_file}",
            flush=True,
        )

    report = {
        "runs_seconds": durations,
        "median_seconds": statistics.median(durations),
    }
    print(json.dumps(report, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"benchmark failed: {error}", file=sys.stderr)
        raise SystemExit(1)

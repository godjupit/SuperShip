"""Opt-in pipeline diagnosis; CUDA events preserve asynchronous execution."""

from collections import defaultdict
from contextlib import contextmanager
import json
from pathlib import Path
import threading
import time

import torch


class PipelineProfile:
    def __init__(self, output):
        self.output = output
        self.cpu = defaultdict(float)
        self.calls = defaultdict(int)
        self.events = []
        self.lock = threading.Lock()
        self.started = time.perf_counter()

    def add(self, name, seconds):
        with self.lock:
            self.cpu[name] += seconds
            self.calls[name] += 1

    @contextmanager
    def host(self, name):
        started = time.perf_counter()
        try:
            yield
        finally:
            self.add(name, time.perf_counter() - started)

    def begin_gpu(self, name, stream=None):
        start = torch.cuda.Event(enable_timing=True)
        end = torch.cuda.Event(enable_timing=True)
        start.record(stream)
        self.events.append((name, start, end))
        return end

    def finish(self, images, detections):
        # Called after the worker's existing final device synchronization/fsync.
        elapsed = time.perf_counter() - self.started
        gpu = defaultdict(float)
        gpu_calls = defaultdict(int)
        for name, start, end in self.events:
            gpu[name] += start.elapsed_time(end) / 1000
            gpu_calls[name] += 1
        report = dict(
            wall_seconds=elapsed, images=images, detections=detections,
            cpu_seconds=dict(self.cpu), cpu_calls=dict(self.calls),
            gpu_seconds=dict(gpu), gpu_calls=dict(gpu_calls),
            method='perf_counter host regions and CUDA events, no added per-batch synchronization',
            caveats='Thread CPU regions are summed wall times, overlap each other and GPU; do not add CPU and GPU columns. Graph covers preprocessing, model and GPU postprocessing. Excludes init, report writing and process exit. Instrumentation adds overhead.',
        )
        Path(self.output).write_text(json.dumps(report, indent=2) + '\n')

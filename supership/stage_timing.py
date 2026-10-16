"""Opt-in serialized pipeline diagnosis; synchronizations change overlap."""

import json
from pathlib import Path
import time

import torch


class StageTimer:
    def __init__(self, path, device):
        self.path = path
        self.device = device
        self.stages = {}
        if path:
            self.synchronize()
            self.start = self.previous = time.perf_counter()

    def synchronize(self):
        if str(self.device).startswith("cuda"):
            torch.cuda.synchronize(self.device)

    def mark(self, name):
        if not self.path:
            return
        self.synchronize()
        now = time.perf_counter()
        self.stages[name] = self.stages.get(name, 0.) + now - self.previous
        self.previous = now

    def finish(self, detections):
        if not self.path:
            return
        total = sum(self.stages.values())
        result = {
            "scope": "run_inference entry through output flush/fsync; excludes initialization, report writing, process exit and scoring",
            "method": "perf_counter with CUDA synchronization at each stage boundary; serialized diagnosis changes pipeline overlap; loader workers still prefetch concurrently",
            "total_seconds": total,
            "detections": detections,
            "stages": [{"name": name, "seconds": value, "percent": value / total * 100}
                       for name, value in self.stages.items()],
        }
        path = Path(self.path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")

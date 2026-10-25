"""Trace the fastest worker on real inputs, using the existing READY protocol.

This is a diagnostic worker. Its timings include profiler overhead and must not
be used as competition performance numbers. Set all normal runtime variables.
"""

from collections import defaultdict
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, os.getcwd())

import torch

from supership.fast_worker import Runtime
from supership.generate_submission import read_worker_request


def main():
    runtime = Runtime()
    print('THU_RS_READY', flush=True)
    request = read_worker_request()
    with torch.profiler.profile(activities=[
        torch.profiler.ProfilerActivity.CPU,
        torch.profiler.ProfilerActivity.CUDA,
    ]) as profiler:
        detections, images = runtime.run(request)
    base = Path(request['output_file'])
    profiler.export_chrome_trace(str(base) + '.trace.json')
    kernels = defaultdict(lambda: dict(calls=0, microseconds=0.0))
    for event in profiler.events():
        if event.device_type == torch.autograd.DeviceType.CUDA:
            row = kernels[event.name]
            row['calls'] += 1
            row['microseconds'] += event.device_time_total
    rows = [dict(name=name, **data) for name, data in kernels.items()]
    rows.sort(key=lambda row: row['microseconds'], reverse=True)
    Path(str(base) + '.kernels.json').write_text(json.dumps(dict(
        images=images, detections=detections, kernels=rows,
        caveat='Profiler overhead changes wall time. CUDA kernel sums are not end-to-end percentages.',
    ), indent=2) + '\n')
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0)


if __name__ == '__main__':
    main()

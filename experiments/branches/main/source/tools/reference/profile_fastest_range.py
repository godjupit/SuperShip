"""Profile real-input inference after synthetic initialization; diagnostic only."""

import argparse
import json
import os
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output exists; choose a unique experiment path")
    os.environ.update(json.loads(args.config.read_text()))
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    import torch
    from supership.fast_worker import Runtime

    runtime = Runtime()  # Only synthetic warmup and graph capture, outside range.
    torch.cuda.synchronize()
    request = dict(
        image_dir="data/SuperShip/reference/images",
        meta_file="data/SuperShip/reference/reference_images_meta.json",
        output_file=str(args.output),
    )
    torch.cuda.cudart().cudaProfilerStart()
    try:
        with torch.inference_mode():
            detections, images = runtime.run(request)
        torch.cuda.synchronize()
    finally:
        torch.cuda.cudart().cudaProfilerStop()
    print(json.dumps(dict(images=images, detections=detections,
                          scope="diagnostic inference range; initialization excluded")))


if __name__ == "__main__":
    main()

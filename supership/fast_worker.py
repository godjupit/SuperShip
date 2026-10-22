"""Bounded threaded image pipeline; all dataset access starts after READY."""

import concurrent.futures
import json
import os
from pathlib import Path
import sys
import threading

sys.path.insert(0, os.getcwd())

import numpy as np
import orjson
from PIL import Image
import torch

from supership.generate_submission import build_runtime, model_forward, read_worker_request


class Runtime:
    def __init__(self):
        self.batch = int(os.environ.get("BATCH_SIZE", "8"))
        self.workers = int(os.environ.get("NUM_WORKERS", "8"))
        self.prefetch = int(os.environ.get("PIPELINE_DEPTH", "3"))
        self.device = os.environ.get("DEVICE", "cuda:0")
        self.precision = os.environ.get("PRECISION", "fp32")
        self.backend = os.environ.get("BACKEND", "cuda_graph")
        self.threshold = float(os.environ.get("SCORE_THRESHOLD", "0"))
        self.decoder = os.environ.get("IMAGE_DECODER", "pil")
        self.reduction = int(os.environ.get("JPEG_REDUCTION", "1"))
        self.antialias = os.environ.get("RESIZE_ANTIALIAS", "1") == "1"
        self.vectorized = os.environ.get("VECTORIZED_RESULTS", "0") == "1"
        if min(self.batch, self.workers, self.prefetch) < 1:
            raise ValueError("batch, workers and pipeline depth must be positive")
        if self.precision not in ("fp32", "fp16") or self.backend not in ("torch", "cuda_graph"):
            raise ValueError("unsupported precision or backend")
        if not 0 <= self.threshold <= 1:
            raise ValueError("score threshold must be in [0, 1]")
        if self.decoder not in ("pil", "opencv", "cuda"):
            raise ValueError("unsupported image decoder")
        if self.reduction not in (1, 2) or (self.reduction != 1 and self.decoder != "opencv"):
            raise ValueError("JPEG_REDUCTION=2 is supported only by the OpenCV decoder")
        torch.set_num_threads(int(os.environ.get("TORCH_THREADS", "1")))
        if self.decoder == "opencv":
            import cv2
            cv2.setNumThreads(1)
        if self.decoder == "cuda":
            # Initialize nvJPEG using a synthetic JPEG, without opening any dataset.
            import io
            from torchvision.io import decode_jpeg
            from torchvision.transforms.v2.functional import resize
            buffer = io.BytesIO()
            Image.new("RGB", (64, 64), (127, 127, 127)).save(buffer, format="JPEG")
            encoded = torch.frombuffer(bytearray(buffer.getvalue()), dtype=torch.uint8)
            synthetic = decode_jpeg([encoded], mode="RGB", device=self.device)[0]
            resize(synthetic, [640, 640], antialias=self.antialias)
            torch.cuda.synchronize(self.device)
        _, self.model, self.post = build_runtime(
            os.environ.get("MODEL_CONFIG", "configs/dfine/dfine_hgnetv2_s_supership.yml"),
            os.environ.get("MODEL_WEIGHTS", "weights/baseline.pth"), self.device,
        )
        if os.environ.get("MODEL_DEPLOY", "0") == "1":
            self.model.deploy()
        if os.environ.get("CHANNELS_LAST", "1") == "1":
            self.model.to(memory_format=torch.channels_last)
        self.post.deploy()
        self.images = torch.zeros(self.batch, 640, 640, 3, dtype=torch.uint8, device=self.device)
        self.sizes = torch.ones(self.batch, 2, dtype=torch.float32, device=self.device)
        self.host = [torch.empty_like(self.images, device="cpu", pin_memory=True)
                     for _ in range(self.prefetch)]
        self.host_arrays = [x.numpy() for x in self.host]
        self.pool = concurrent.futures.ThreadPoolExecutor(max_workers=self.workers)
        # Start threads using synthetic work only, without accessing evaluation paths.
        barrier = threading.Barrier(self.workers)
        jobs = [self.pool.submit(barrier.wait) for _ in range(self.workers)]
        for job in jobs:
            job.result()
        with torch.inference_mode():
            stream = torch.cuda.Stream(device=self.device)
            stream.wait_stream(torch.cuda.current_stream(self.device))
            with torch.cuda.stream(stream):
                for _ in range(5):
                    self.forward()
            torch.cuda.current_stream(self.device).wait_stream(stream)
            torch.cuda.synchronize(self.device)
            self.graph = None
            if self.backend == "cuda_graph":
                self.graph = torch.cuda.CUDAGraph()
                with torch.cuda.graph(self.graph, stream=stream):
                    self.captured = self.forward()
                torch.cuda.synchronize(self.device)

    def forward(self):
        images = self.images.permute(0, 3, 1, 2).float().mul_(1 / 255)
        if os.environ.get("CHANNELS_LAST", "1") != "1":
            images = images.contiguous()
        outputs = model_forward(self.model, images, self.precision)
        labels, boxes, scores = self.post(outputs, self.sizes)
        return torch.cat((boxes, scores.unsqueeze(-1), labels.unsqueeze(-1)), dim=-1)

    def load_image(self, item, image_dir, destination):
        # image_dir and metadata are obtained only after READY.
        path = Path(image_dir) / item["file_name"]
        if self.decoder == "cuda":
            return torch.frombuffer(bytearray(path.read_bytes()), dtype=torch.uint8)
        if self.decoder == "opencv":
            import cv2
            flag = cv2.IMREAD_REDUCED_COLOR_2 if self.reduction == 2 else cv2.IMREAD_COLOR
            image = cv2.imread(str(path), flag)
            if image is None:
                raise ValueError(f"cannot decode image: {path}")
            h, w = image.shape[:2]
            resized = cv2.resize(image, (640, 640), interpolation=cv2.INTER_LINEAR)
            destination[:] = resized[:, :, ::-1]
        else:
            with Image.open(path) as image:
                image = image.convert("RGB")
                w, h = image.size
                destination[:] = np.asarray(image.resize((640, 640), Image.Resampling.BILINEAR))
        reduction = self.reduction if self.decoder == "opencv" else 1
        expected = tuple((item[key] + reduction - 1) // reduction for key in ("width", "height"))
        if (w, h) != expected:
            raise ValueError(f"metadata dimensions disagree with decoded image: {path}")
        return item["width"], item["height"]

    def run(self, request):
        metadata = json.loads(Path(request["meta_file"]).read_text())
        items = metadata["images"]
        ids = [item["id"] for item in items]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate image ids")
        jobs = {}
        count = (len(items) + self.batch - 1) // self.batch

        def schedule(index):
            slot = index % self.prefetch
            batch = items[index * self.batch:(index + 1) * self.batch]
            jobs[index] = [self.pool.submit(self.load_image, item, request["image_dir"],
                                           self.host_arrays[slot][row])
                           for row, item in enumerate(batch)]

        for index in range(min(self.prefetch, count)):
            schedule(index)
        results = []
        with torch.inference_mode():
            for index in range(count):
                slot = index % self.prefetch
                batch = items[index * self.batch:(index + 1) * self.batch]
                loaded = [job.result() for job in jobs.pop(index)]
                n = len(batch)
                if self.decoder == "cuda":
                    from torchvision.io import decode_jpeg
                    from torchvision.transforms.v2.functional import resize
                    decoded = decode_jpeg(loaded, mode="RGB", device=self.device)
                    sizes = []
                    groups = {}
                    for row, (item, image) in enumerate(zip(batch, decoded)):
                        h, w = image.shape[-2:]
                        if (w, h) != (item["width"], item["height"]):
                            raise ValueError("metadata dimensions disagree with decoded image")
                        sizes.append((w, h))
                        groups.setdefault((h, w), []).append(row)
                    for indices in groups.values():
                        images = torch.stack([decoded[row] for row in indices])
                        resized = resize(images, [640, 640], antialias=self.antialias)
                        for row, image in zip(indices, resized):
                            self.images[row].copy_(image.permute(1, 2, 0))
                    if n < self.batch:
                        self.images[n:].zero_()
                else:
                    sizes = loaded
                    if n < self.batch:
                        self.host[slot][n:].zero_()
                    self.images.copy_(self.host[slot], non_blocking=True)
                self.sizes[:n].copy_(torch.tensor(sizes, dtype=torch.float32), non_blocking=True)
                if n < self.batch:
                    self.sizes[n:].fill_(1)
                if self.graph is not None:
                    self.graph.replay()
                    output = self.captured[:n].cpu().numpy()
                else:
                    output = self.forward()[:n].cpu().numpy()
                if not np.isfinite(output).all():
                    raise ValueError("nonfinite detection")
                # D2H above also fences H2D: this slot can now be safely reused.
                if index + self.prefetch < count:
                    schedule(index + self.prefetch)
                for item, detections in zip(batch, output):
                    selected = detections[detections[:, 4] >= self.threshold].astype(np.float64)
                    if self.vectorized:
                        selected[:, 2:4] -= selected[:, :2]
                        boxes = np.round(selected[:, :4], 2)
                        scores = np.round(selected[:, 4], 5)
                        for box, score, label in zip(boxes.tolist(), scores.tolist(), selected[:, 5]):
                            if box[2] > 0 and box[3] > 0:
                                results.append(dict(image_id=int(item["id"]), category_id=int(label),
                                                    bbox=box, score=score))
                    else:
                        for x1, y1, x2, y2, score, label in selected.tolist():
                            w, h = round(x2 - x1, 2), round(y2 - y1, 2)
                            if w > 0 and h > 0:
                                results.append(dict(image_id=int(item["id"]), category_id=int(label),
                                                    bbox=[round(x1, 2), round(y1, 2), w, h],
                                                    score=round(score, 5)))
        self.pool.shutdown(wait=True)
        torch.cuda.synchronize(self.device)
        # Nonfinite model outputs were rejected before orjson serialization.
        payload = orjson.dumps(results)
        path = Path(request["output_file"])
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb") as f:
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())
        return len(results), len(items)


def main():
    runtime = Runtime()
    print("THU_RS_READY", flush=True)
    detections, images = runtime.run(read_worker_request())
    print(f"processed {images} images; wrote {detections} detections", file=sys.stderr, flush=True)
    # All threads joined, kernels synchronized, and output closed after fsync.
    # Avoid spending timed inference on Python/CUDA allocator destruction.
    sys.stdout.flush()
    sys.stderr.flush()
    if os.environ.get("FAST_EXIT", "1") == "1":
        os._exit(0)


if __name__ == "__main__":
    main()

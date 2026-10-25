"""Bounded threaded image pipeline; all dataset access starts after READY."""

import concurrent.futures
from collections import deque
import json
import os
from pathlib import Path
import sys
import threading
import time

sys.path.insert(0, os.getcwd())

import numpy as np
import orjson
from PIL import Image
import torch

from supership.generate_submission import build_runtime, model_forward, read_worker_request


class Runtime:
    def __init__(self):
        self.side = int(os.environ.get("INPUT_SIZE", "640"))
        self.batch = int(os.environ.get("BATCH_SIZE", "8"))
        self.workers = int(os.environ.get("NUM_WORKERS", "8"))
        self.prefetch = int(os.environ.get("PIPELINE_DEPTH", "3"))
        self.device = os.environ.get("DEVICE", "cuda:0")
        self.precision = os.environ.get("PRECISION", "fp32")
        self.backend = os.environ.get("BACKEND", "cuda_graph")
        self.threshold = float(os.environ.get("SCORE_THRESHOLD", "0"))
        self.decoder = os.environ.get("IMAGE_DECODER", "pil")
        self.reduction = int(os.environ.get("JPEG_REDUCTION", "1"))
        self.copy_mode = os.environ.get("OPENCV_COPY_MODE", "strided")
        self.async_output = os.environ.get("ASYNC_OUTPUT", "0") == "1"
        self.eval_layers = int(os.environ.get("DECODER_LAYERS", "0"))
        self.antialias = os.environ.get("RESIZE_ANTIALIAS", "1") == "1"
        self.vectorized = os.environ.get("VECTORIZED_RESULTS", "0") == "1"
        if self.side < 320 or self.side > 1280 or self.side % 32:
            raise ValueError("INPUT_SIZE must be a multiple of 32 between 320 and 1280")
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
        if self.copy_mode not in ("strided", "cvtcolor", "direct"):
            raise ValueError("unsupported OPENCV_COPY_MODE")
        if self.eval_layers not in (0, 1, 2, 3):
            raise ValueError("DECODER_LAYERS must be 0 (checkpoint default), 1, 2 or 3")
        torch.backends.cudnn.benchmark = os.environ.get("CUDNN_BENCHMARK", "0") == "1"
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
        if self.side != 640:
            # Load all trained weights strictly first, then regenerate only geometry.
            encoder, decoder = self.model.encoder, self.model.decoder
            encoder.eval_spatial_size = decoder.eval_spatial_size = (self.side, self.side)
            for index in encoder.use_encoder_idx:
                stride = encoder.feat_strides[index]
                position = encoder.build_2d_sincos_position_embedding(
                    self.side // stride, self.side // stride,
                    encoder.hidden_dim, encoder.pe_temperature, device=self.device)
                setattr(encoder, f"pos_embed{index}", position)
            decoder.anchors, decoder.valid_mask = decoder._generate_anchors(device=self.device)
        if self.eval_layers:
            # Keep trained head dimensions; change only the inference stopping layer.
            if self.eval_layers > self.model.decoder.num_layers:
                raise ValueError("DECODER_LAYERS exceeds the checkpoint architecture")
            self.model.decoder.eval_idx = self.eval_layers - 1
            self.model.decoder.decoder.eval_idx = self.eval_layers - 1
        if os.environ.get("MODEL_DEPLOY", "0") == "1":
            self.model.deploy()
        if os.environ.get("CHANNELS_LAST", "1") == "1":
            self.model.to(memory_format=torch.channels_last)
        self.post.deploy()
        self.images = torch.zeros(self.batch, self.side, self.side, 3, dtype=torch.uint8, device=self.device)
        self.sizes = torch.ones(self.batch, 2, dtype=torch.float32, device=self.device)
        self.host = [torch.empty_like(self.images, device="cpu", pin_memory=True)
                     for _ in range(self.prefetch)]
        self.host_arrays = [x.numpy() for x in self.host]
        self.output_stream = torch.cuda.Stream(device=self.device) if self.async_output else None
        self.host_outputs = None
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
            if self.async_output:
                example = self.captured if self.graph is not None else self.forward()
                self.host_outputs = [torch.empty_like(example, device="cpu", pin_memory=True)
                                     for _ in range(self.prefetch)]
                torch.cuda.synchronize(self.device)

    def forward(self):
        images = self.images.permute(0, 3, 1, 2).float().mul_(1 / 255)
        if os.environ.get("CHANNELS_LAST", "1") != "1":
            images = images.contiguous()
        outputs = model_forward(self.model, images, self.precision)
        labels, boxes, scores = self.post(outputs, self.sizes)
        return torch.cat((boxes, scores.unsqueeze(-1), labels.unsqueeze(-1)), dim=-1)

    def load_image(self, item, image_dir, destination):
        profile = getattr(self, "profile", None)
        if profile is None:
            return self._load_image(item, image_dir, destination)
        with profile.host("loader_thread_total"):
            return self._load_image(item, image_dir, destination)

    def _load_image(self, item, image_dir, destination):
        # image_dir and metadata are obtained only after READY.
        path = Path(image_dir) / item["file_name"]
        if self.decoder == "cuda":
            return torch.frombuffer(bytearray(path.read_bytes()), dtype=torch.uint8)
        if self.decoder == "opencv":
            import cv2
            flag = cv2.IMREAD_REDUCED_COLOR_2 if self.reduction == 2 else cv2.IMREAD_COLOR
            profile = getattr(self, "profile", None)
            stamp = time.perf_counter() if profile else 0
            image = cv2.imread(str(path), flag)
            if profile:
                profile.add("loader_imread_decode", time.perf_counter() - stamp)
                stamp = time.perf_counter()
            if image is None:
                raise ValueError(f"cannot decode image: {path}")
            h, w = image.shape[:2]
            copy_mode = getattr(self, "copy_mode", "strided")
            if copy_mode != "direct":
                resized = cv2.resize(image, (destination.shape[1], destination.shape[0]), interpolation=cv2.INTER_LINEAR)
            if copy_mode == "direct":
                # Reuse the pinned destination for both resize and channel swap.
                cv2.resize(image, (destination.shape[1], destination.shape[0]), dst=destination, interpolation=cv2.INTER_LINEAR)
                cv2.cvtColor(destination, cv2.COLOR_BGR2RGB, dst=destination)
            elif copy_mode == "cvtcolor":
                cv2.cvtColor(resized, cv2.COLOR_BGR2RGB, dst=destination)
            else:
                destination[:] = resized[:, :, ::-1]
            if profile:
                profile.add("loader_resize_rgb", time.perf_counter() - stamp)
        else:
            with Image.open(path) as image:
                image = image.convert("RGB")
                w, h = image.size
                destination[:] = np.asarray(image.resize((destination.shape[1], destination.shape[0]), Image.Resampling.BILINEAR))
        reduction = self.reduction if self.decoder == "opencv" else 1
        expected = tuple((item[key] + reduction - 1) // reduction for key in ("width", "height"))
        if (w, h) != expected:
            raise ValueError(f"metadata dimensions disagree with decoded image: {path}")
        return item["width"], item["height"]

    def run(self, request):
        profile = None
        if os.environ.get("FAST_PROFILE") == "1":
            from supership.pipeline_profile import PipelineProfile
            profile = PipelineProfile(request["output_file"] + ".profile.json")
        self.profile = profile
        stamp = time.perf_counter() if profile else 0
        metadata = json.loads(Path(request["meta_file"]).read_text())
        items = metadata["images"]
        ids = [item["id"] for item in items]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate image ids")
        if profile:
            profile.add("metadata", time.perf_counter() - stamp)
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
        pending = deque()

        def collect(batch, output):
            stamp = time.perf_counter() if profile else 0
            if not np.isfinite(output).all():
                raise ValueError("nonfinite detection")
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
            if profile:
                profile.add("cpu_collect", time.perf_counter() - stamp)
        with torch.inference_mode():
            for index in range(count):
                slot = index % self.prefetch
                batch = items[index * self.batch:(index + 1) * self.batch]
                stamp = time.perf_counter() if profile else 0
                loaded = [job.result() for job in jobs.pop(index)]
                if profile:
                    profile.add("loader_wait", time.perf_counter() - stamp)
                    transfer_end = profile.begin_gpu("h2d")
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
                        resized = resize(images, [self.side, self.side], antialias=self.antialias)
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
                if profile:
                    transfer_end.record()
                    graph_end = profile.begin_gpu("graph_preprocess_model_postprocess")
                if self.graph is not None:
                    self.graph.replay()
                    device_output = self.captured
                else:
                    device_output = self.forward()
                if profile:
                    graph_end.record()
                if self.async_output:
                    # Copy off the graph's static output before its next replay.
                    # The next batch can execute while Python formats older results.
                    current = torch.cuda.current_stream(self.device)
                    self.output_stream.wait_stream(current)
                    with torch.cuda.stream(self.output_stream):
                        if profile:
                            output_end = profile.begin_gpu("d2h", self.output_stream)
                        self.host_outputs[slot].copy_(device_output, non_blocking=True)
                        if profile:
                            output_end.record(self.output_stream)
                        ready = torch.cuda.Event()
                        ready.record(self.output_stream)
                    current.wait_event(ready)
                    pending.append((index, batch, ready))
                    if len(pending) >= min(2, self.prefetch):
                        previous, previous_batch, event = pending.popleft()
                        stamp = time.perf_counter() if profile else 0
                        event.synchronize()
                        if profile:
                            profile.add("output_wait", time.perf_counter() - stamp)
                        previous_slot = previous % self.prefetch
                        # This completion also fences the pinned input's H2D copy.
                        if previous + self.prefetch < count:
                            schedule(previous + self.prefetch)
                        collect(previous_batch, self.host_outputs[previous_slot][:len(previous_batch)].numpy())
                else:
                    output = device_output[:n].cpu().numpy()
                    if index + self.prefetch < count:
                        schedule(index + self.prefetch)
                    collect(batch, output)
            for previous, previous_batch, event in pending:
                stamp = time.perf_counter() if profile else 0
                event.synchronize()
                if profile:
                    profile.add("output_wait", time.perf_counter() - stamp)
                collect(previous_batch, self.host_outputs[previous % self.prefetch][:len(previous_batch)].numpy())
        stamp = time.perf_counter() if profile else 0
        self.pool.shutdown(wait=True)
        torch.cuda.synchronize(self.device)
        # Nonfinite model outputs were rejected before orjson serialization.
        if profile:
            profile.add("shutdown_sync", time.perf_counter() - stamp)
            stamp = time.perf_counter()
        payload = orjson.dumps(results)
        if profile:
            profile.add("serialize", time.perf_counter() - stamp)
            stamp = time.perf_counter()
        path = Path(request["output_file"])
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb") as f:
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())
        if profile:
            profile.add("write_fsync", time.perf_counter() - stamp)
            profile.finish(len(items), len(results))
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

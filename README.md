# SuperShip: GPU End-to-End Inference Optimization

This repository is the public code package for the SuperShip competition task. It contains the fixed RT-DETRv4 source, the official baseline inference weight, and the reference timing/scoring tools. The public dataset is distributed separately through Tsinghua Cloud.

The full competition rules are available in [COMPETITION.md](COMPETITION.md).

The upstream RT-DETRv4 source is pinned to commit:

```text
55fefaaed7efe2a5f72d0a18fd4e05965e35c292
```

See [UPSTREAM_README.md](UPSTREAM_README.md) for the original RT-DETRv4 documentation and [LICENSE](LICENSE) for the upstream license.
Machine-readable release metadata and checksums are stored in [RELEASE_INFO.json](RELEASE_INFO.json).

## Public Data

| Split | Images | Instances | Released content |
| --- | ---: | ---: | --- |
| Train | 2,405 | 11,904 | Images and COCO annotations |
| Validation | 1,030 | 4,576 | Images and COCO annotations |
| Public reference | 200 | 519 | Images, inference metadata, and COCO ground truth |

The public reference split is selected deterministically by sorting the private test-pool images by integer `image_id` and taking the first 200. After installing the data package, its manifest is available at `data/SuperShip/reference/split_manifest.json`.

The remaining 4,300 hidden-test images, metadata, and annotations are not included in this repository.

### Download and install

Download `SuperShip-public-data.tar.zst` from the [Tsinghua Cloud link](https://cloud.tsinghua.edu.cn/d/da024b91e33a46cb8200/). Its expected SHA-256 is:

```text
46e0b3a18ceaa0a95d8093aa7c4211c16dd69e4e27247a82146131e50e18f3fb
```

Install an archive already downloaded to the local machine:

```bash
bash download_data.sh /path/to/SuperShip-public-data.tar.zst
```

Alternatively, use a direct-download URL:

```bash
SUPERSHIP_DATA_URL='<THU_CLOUD_DIRECT_DOWNLOAD_URL>' bash download_data.sh
```

The script verifies the archive checksum, extracts it under `data/SuperShip/`, and runs the release integrity check. It requires `curl` for URL downloads and `zstd` for extraction.

## Categories

| ID | Name | Description |
| ---: | --- | --- |
| 0 | `aircraft_carrier` | Aircraft carrier |
| 1 | `warship` | Warship |
| 2 | `other_ship` | Other ship |

## Repository Layout

```text
SuperShip/
├── configs/                         # RT-DETRv4 and SuperShip configs
├── engine/                          # RT-DETRv4 source
├── tools/                           # Upstream RT-DETRv4 tools
├── data/SuperShip/                  # Created after cloud data installation
│   ├── train/
│   │   ├── images/
│   │   └── annotations/instances_train.json
│   ├── val/
│   │   ├── images/
│   │   └── annotations/instances_val.json
│   └── reference/
│       ├── images/
│       ├── annotations/instances_reference.json
│       ├── reference_images_meta.json
│       └── split_manifest.json
├── supership/                       # Inference, timing, scoring, validation
├── weights/baseline.pth            # Official compact inference checkpoint
├── run.sh                           # Competition worker entry point
├── benchmark_reference.sh          # End-to-end timing on public reference data
└── score_reference.sh              # AP evaluation on public reference data
```

## Environment

The official evaluation device is one NVIDIA GeForce RTX 3090. Python 3.11 is recommended.

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

Install a PyTorch build compatible with the CUDA driver on the target system if the generic requirement does not select the desired build.

## Baseline Inference

Run one-shot inference on the public reference split:

```bash
python3 supership/generate_submission.py \
  --config configs/dfine/dfine_hgnetv2_s_supership.yml \
  --weights weights/baseline.pth \
  --img-folder data/SuperShip/reference/images \
  --ann-file data/SuperShip/reference/reference_images_meta.json \
  --output output/reference_submission.json \
  --device cuda:0 \
  --batch-size 8
```

Score the result:

```bash
bash score_reference.sh output/reference_submission.json
```

The validation baseline reported by the organizer is `AP50 = 0.916`.

## End-to-End Timing

The competition protocol separates untimed initialization from timed inference:

1. The organizer starts `bash run.sh --worker` without exposing evaluation paths.
2. The worker loads the model, initializes CUDA, then prints `THU_RS_READY`.
3. The timer starts immediately before the organizer sends input/output paths over stdin.
4. Timing stops after all images are processed, the output is flushed with `fsync`, and the worker exits.

Run the same protocol locally on the 200-image public reference split:

```bash
bash benchmark_reference.sh
```

The default is three independent runs. Results are written to:

```text
output/reference_submission.run1.json
output/reference_submission.run2.json
output/reference_submission.run3.json
```

Score all generated runs:

```bash
bash score_reference.sh
```

Environment overrides are supported:

```bash
BATCH_SIZE=16 RUNS=3 DEVICE=cuda:0 bash benchmark_reference.sh
```

## Training

The released training and validation data use COCO Detection format. Train or fine-tune with:

```bash
python3 train.py \
  --config configs/dfine/dfine_hgnetv2_s_supership.yml \
  --tuning weights/baseline.pth \
  --device cuda:0
```

Use representative training samples for post-training quantization calibration. The validation split should remain reserved for model selection and accuracy evaluation.

## Accuracy Scoring

The scoring tool can evaluate any COCO result array against a released split:

```bash
python3 supership/score_submission.py \
  --gt data/SuperShip/val/annotations/instances_val.json \
  --submission output/val_submission.json
```

Official ranking is performed by the organizer on the unreleased 4,300-image hidden test set.

## RTX 4090 optimized pipeline

The optimized worker is opt-in and retains the official READY/timing protocol. Install the extra dependencies with `python -m pip install -r requirements-fast.txt`, then run `bash benchmark_optimized.sh`. The wrapper delegates timing and output validation to the unchanged official `benchmark_reference.sh`. Set `PYTHON_BIN` to your Python environment as usual.

The measured fastest configuration uses 8 image threads, bounded prefetch, reduced JPEG decoding, OpenCV resizing, FP16 CUDA Graph inference and postprocessing, vectorized result assembly, `orjson`, and score threshold 0.05. Every input image is decoded and inferred after READY. The output is flushed, fsynced, closed, and GPU work synchronized before process exit. Initialization uses synthetic images only.

For the higher accuracy alternative, use `JPEG_REDUCTION=1 bash benchmark_optimized.sh`. For the original inference route, continue using `bash benchmark_reference.sh` without `PIPELINE=fast`. Full measurements, accuracy checks and accepted submission receipts are linked in [OPTIMIZATION_RESULTS_20261022.md](OPTIMIZATION_RESULTS_20261022.md). Public validation cannot guarantee the organizer's hidden-set accuracy.

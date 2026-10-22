"""Check the data contract of the threaded preprocessing path."""

import numpy as np
from PIL import Image
import pytest
from torchvision.transforms import v2

from supership.fast_worker import Runtime


def make_image(tmp_path):
    pixels = np.arange(37 * 23 * 3, dtype=np.uint8).reshape(23, 37, 3)
    path = tmp_path / "sample.png"
    Image.fromarray(pixels).save(path)
    return path, {"id": 17, "file_name": path.name, "width": 37, "height": 23}


def test_pil_pipeline_preserves_official_resize(tmp_path):
    path, item = make_image(tmp_path)
    runtime = Runtime.__new__(Runtime)
    runtime.decoder = "pil"
    result = np.empty((640, 640, 3), dtype=np.uint8)
    assert runtime.load_image(item, tmp_path, result) == (37, 23)
    with Image.open(path) as image:
        expected = np.asarray(v2.Resize([640, 640])(image.convert("RGB")))
    np.testing.assert_array_equal(result, expected)


def test_image_dimensions_checked_against_metadata(tmp_path):
    _, item = make_image(tmp_path)
    item["width"] += 1
    runtime = Runtime.__new__(Runtime)
    runtime.decoder = "pil"
    with pytest.raises(ValueError, match="metadata dimensions"):
        runtime.load_image(item, tmp_path, np.empty((640, 640, 3), dtype=np.uint8))


def test_opencv_pipeline_keeps_rgb_order(tmp_path):
    import cv2

    path, item = make_image(tmp_path)
    runtime = Runtime.__new__(Runtime)
    runtime.decoder = "opencv"
    result = np.empty((640, 640, 3), dtype=np.uint8)
    runtime.load_image(item, tmp_path, result)
    with Image.open(path) as image:
        expected = cv2.resize(np.asarray(image), (640, 640), interpolation=cv2.INTER_LINEAR)
    np.testing.assert_array_equal(result, expected)

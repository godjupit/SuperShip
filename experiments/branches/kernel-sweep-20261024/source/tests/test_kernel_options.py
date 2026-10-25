"""Numerical and graph checks for opt-in inference kernel alternatives."""
import copy
import pytest
import torch
from torch import nn
from supership.kernel_optimizations import LinearPointwise, apply_kernel_options


def test_pointwise_linear_matches_convolution():
    torch.manual_seed(7)
    conv = nn.Conv2d(7, 11, 1).eval()
    inputs = torch.randn(2, 7, 9, 13).to(memory_format=torch.channels_last)
    torch.testing.assert_close(LinearPointwise(conv)(inputs), conv(inputs), rtol=1e-5, atol=1e-6)


def test_precision_options_leave_normalization_unchanged(monkeypatch):
    from engine.backbone.hgnetv2 import LearnableAffineBlock
    model = nn.Sequential(nn.Conv2d(3, 4, 1), LearnableAffineBlock(), nn.LayerNorm(4)).eval()
    reference = copy.deepcopy(model)
    monkeypatch.setenv("KERNEL_WEIGHT_HALF", "1")
    changes = apply_kernel_options(model, "fp16")
    assert changes == {"weight_half": 1}
    assert model[0].weight.dtype == torch.float16
    assert model[1].scale.dtype == model[2].weight.dtype == torch.float32
    torch.testing.assert_close(model[0].weight, reference[0].weight.half(), rtol=0, atol=0)
    with pytest.raises(ValueError, match="evaluation"):
        apply_kernel_options(model.train(), "fp16")


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA required")
@pytest.mark.parametrize("layout", ["nchw", "nhwc", "channel_slice", "spatial_slice"])
def test_feature_pack_matches_cast_and_supports_graph_reuse(layout, monkeypatch):
    from engine.misc.feature_ops import feature_cat
    monkeypatch.setenv("FEATURE_CAT", "triton_half")
    x = torch.randn(2, 14, 9, 11, device="cuda")
    if layout != "nchw":
        x = x.to(memory_format=torch.channels_last)
    if layout == "channel_slice":
        parts = [x[:, :3], x[:, 3:8].half(), x[:, 8:]]
    elif layout == "spatial_slice":
        parts = [x[:, :3, ::2, ::2], x[:, 3:, ::2, ::2].half()]
    else:
        parts = [x, x[:, :5].half()]
    with torch.inference_mode():
        expected = torch.cat(parts, 1).half()
        actual = feature_cat(parts)
        torch.testing.assert_close(actual, expected, rtol=0, atol=0)
        assert actual.is_contiguous(memory_format=torch.channels_last)
        stream = torch.cuda.Stream()
        stream.wait_stream(torch.cuda.current_stream())
        with torch.cuda.stream(stream):
            feature_cat(parts)
        torch.cuda.current_stream().wait_stream(stream)
        torch.cuda.synchronize()
        graph = torch.cuda.CUDAGraph()
        with torch.cuda.graph(graph, stream=stream):
            output = feature_cat(parts)
        for part in parts:
            part.add_(0.25)
        graph.replay()
        torch.cuda.synchronize()
        torch.testing.assert_close(output, torch.cat(parts, 1).half(), rtol=0, atol=0)

"""Check inference equivalence, padding and unsupported graph connections."""

import copy

import pytest
import torch
from torch import nn

from engine.backbone.common import FrozenBatchNorm2d
from engine.backbone.hgnetv2 import ConvBNAct
from engine.rtv4.hybrid_encoder import ConvNormLayer, ConvNormLayer_fuse
from supership.conv_bn_fusion import fuse_model_conv_bn


@pytest.mark.parametrize("kind", ["padded", "grouped", "encoder", "sequential", "frozen"])
def test_fusion_preserves_evaluation_output(kind):
    torch.manual_seed(42)
    if kind == "padded":
        module = ConvBNAct(4, 4, 3, padding="same", use_lab=True)
    elif kind == "grouped":
        module = ConvNormLayer_fuse(4, 4, 3, 1, g=4, bias=True, act="silu")
    elif kind == "encoder":
        module = ConvNormLayer(4, 6, 1, 1, act="relu")
    else:
        bn = FrozenBatchNorm2d(4) if kind == "frozen" else nn.BatchNorm2d(4, affine=False)
        module = nn.Sequential(nn.Conv2d(4, 4, 3, padding=1, bias=True), bn, nn.ReLU())
    module.eval()
    for bn in module.modules():
        if isinstance(bn, (nn.BatchNorm2d, FrozenBatchNorm2d)):
            bn.running_mean.copy_(torch.randn_like(bn.running_mean))
            bn.running_var.copy_(torch.rand_like(bn.running_var) + 0.2)
            if bn.weight is not None:
                bn.weight.data.uniform_(-1, 2)
                bn.bias.data.uniform_(-1, 1)
    original = copy.deepcopy(module)
    inputs = torch.randn(2, 4, 19, 23)
    names = fuse_model_conv_bn(module)
    assert len(names) == 1
    with torch.inference_mode():
        torch.testing.assert_close(module(inputs), original(inputs), rtol=2e-5, atol=2e-5)
    assert fuse_model_conv_bn(module) == []


def test_fusion_rejects_training_and_missing_statistics():
    model = nn.Sequential(nn.Conv2d(3, 3, 1), nn.BatchNorm2d(3))
    with pytest.raises(ValueError, match="evaluation"):
        fuse_model_conv_bn(model)
    model[1] = nn.BatchNorm2d(3, track_running_stats=False)
    model.eval()
    with pytest.raises(ValueError, match="running statistics"):
        fuse_model_conv_bn(model)


def test_module_registration_order_does_not_imply_a_forward_connection():
    class Branched(nn.Module):
        def __init__(self):
            super().__init__()
            self.conv = nn.Conv2d(3, 3, 1)
            self.bn = nn.BatchNorm2d(3)

        def forward(self, inputs):
            return self.conv(inputs) + self.bn(inputs)

    model = Branched().eval()
    assert fuse_model_conv_bn(model) == []

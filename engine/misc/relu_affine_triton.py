"""Inference-only ReLU + learned float32 scalar affine, with separate rounding."""
import torch
import triton
import triton.language as tl


@triton.jit
def _relu_affine(X, SCALE, BIAS, OUT, N: tl.constexpr, BLOCK: tl.constexpr):
    index=tl.program_id(0)*BLOCK+tl.arange(0,BLOCK)
    x=tl.load(X+index,index<N,other=0).to(tl.float32)
    scale=tl.load(SCALE).to(tl.float32)
    bias=tl.load(BIAS).to(tl.float32)
    positive=tl.maximum(x,0.,propagate_nan=tl.PropagateNan.ALL)
    scaled=positive*scale
    output=scaled+bias
    tl.store(OUT+index,output,index<N)


def relu_affine(x,scale,bias):
    if not x.is_cuda or x.dtype not in (torch.float16,torch.float32):
        raise ValueError('fused ReLU affine requires a CUDA float16/float32 input')
    if scale.dtype!=torch.float32 or bias.dtype!=torch.float32 or scale.numel()!=1 or bias.numel()!=1:
        raise ValueError('fused ReLU affine preserves float32 scalar parameters')
    if scale.device!=x.device or bias.device!=x.device:
        raise ValueError('input and scalars must use the same CUDA device')
    if not (x.is_contiguous() or (x.ndim==4 and x.is_contiguous(memory_format=torch.channels_last))):
        return torch.relu(x)*scale+bias
    output=torch.empty_like(x,dtype=torch.float32,memory_format=torch.preserve_format)
    n=x.numel()
    if n:
        _relu_affine[(triton.cdiv(n,512),)](x,scale,bias,output,n,512,enable_fp_fusion=False)
    return output


class FusedReLUAffine(torch.nn.Module):
    def __init__(self,original):
        super().__init__()
        self.scale=original.scale
        self.bias=original.bias

    def forward(self,x):
        if self.training or torch.is_grad_enabled():
            return torch.relu(x)*self.scale+self.bias
        return relu_affine(x,self.scale,self.bias)
